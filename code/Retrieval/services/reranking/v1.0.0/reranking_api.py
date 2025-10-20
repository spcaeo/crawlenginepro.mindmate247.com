#!/usr/bin/env python3
"""
Reranking Service v2.0.0
Rerank documents by relevance using BGE-Reranker-v2-M3
https://rerank.mindmate247.com/
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sentence_transformers import CrossEncoder
import time
import torch
import uvicorn
import httpx

# Import configurations and models
from config import *
from models import *

# ============================================================================
# Service Initialization
# ============================================================================

START_TIME = time.time()
TOTAL_REQUESTS = 0

app = FastAPI(
    title=f"{SERVICE_NAME} v{API_VERSION}",
    description=SERVICE_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Security Middleware
# ============================================================================

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Security check - only allow localhost and gateway access"""
    global TOTAL_REQUESTS
    TOTAL_REQUESTS += 1

    client_host = request.client.host

    # Allow localhost
    if client_host in ["127.0.0.1", "localhost", "::1"]:
        return await call_next(request)

    # Allow Docker/internal networks
    if client_host.startswith(("172.", "10.", "192.168.")):
        return await call_next(request)

    # Block external access
    return JSONResponse(
        status_code=403,
        content={
            "error": "Forbidden",
            "detail": f"Direct access forbidden. Use gateway: https://rerank.mindmate247.com",
            "api_version": API_VERSION
        }
    )

# ============================================================================
# Model Loading & Jina AI Setup
# ============================================================================

print("=" * 80)
print(f"{SERVICE_NAME} v{API_VERSION}")
print("=" * 80)
print(f"Reranker Backend: {RERANKER_BACKEND.upper()}")

model = None
http_client = None

if RERANKER_BACKEND == "jina":
    # Jina AI mode
    if not JINA_AI_KEY:
        print("❌ ERROR: JINA_AI_KEY not found in environment!")
        print("   Please set JINA_AI_KEY in .env file")
        exit(1)

    print(f"Jina AI Model: {JINA_MODEL}")
    print(f"API URL: {JINA_API_URL}")
    print(f"API Key: {JINA_AI_KEY[:20]}...")
    http_client = httpx.AsyncClient(timeout=30.0)
    print("✅ Jina AI reranker configured")
else:
    # BGE mode (default)
    print(f"Loading BGE model: {MODEL_NAME}")
    print(f"Device: {DEVICE}")
    print(f"Max length: {MAX_LENGTH}")
    model = CrossEncoder(MODEL_NAME, device=DEVICE, max_length=MAX_LENGTH)
    print(f"✅ BGE model loaded successfully on {DEVICE}")

print("=" * 80)

# ============================================================================
# Reranking Functions
# ============================================================================

async def rerank_with_jina(query: str, documents: list, top_n: int = None):
    """Rerank using Jina AI API"""
    payload = {
        "model": JINA_MODEL,
        "query": query,
        "documents": documents,
        "top_n": top_n or len(documents)
    }

    response = await http_client.post(
        JINA_API_URL,
        json=payload,
        headers={
            "Authorization": f"Bearer {JINA_AI_KEY}",
            "Content-Type": "application/json"
        }
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Jina AI API error: {response.text}"
        )

    return response.json()

def rerank_with_bge(query: str, documents: list, top_n: int = None):
    """Rerank using BGE model"""
    pairs = [[query, doc] for doc in documents]
    scores = model.predict(pairs)

    results = [
        {"index": i, "document": doc, "relevance_score": float(score)}
        for i, (doc, score) in enumerate(zip(documents, scores))
    ]

    results.sort(key=lambda x: x["relevance_score"], reverse=True)

    if top_n:
        results = results[:top_n]

    return results

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with API connectivity test"""
    uptime = time.time() - START_TIME

    model_info = JINA_MODEL if RERANKER_BACKEND == "jina" else MODEL_NAME
    device_info = "jina-api" if RERANKER_BACKEND == "jina" else DEVICE

    # Test Jina API connectivity if using Jina backend (ADDED)
    api_connected = True  # Default for BGE mode
    if RERANKER_BACKEND == "jina":
        try:
            response = await http_client.get(
                "https://api.jina.ai/v1/embeddings",  # Jina health endpoint
                headers={"Authorization": f"Bearer {JINA_AI_KEY}"},
                timeout=2.0
            )
            api_connected = response.status_code in [200, 405]  # 405 = method not allowed (GET on POST endpoint)
        except Exception:
            api_connected = False

    status = "healthy" if api_connected else "degraded"

    return HealthResponse(
        status=status,
        version=API_VERSION,
        service=SERVICE_NAME,
        model=model_info,
        device=device_info,
        uptime_seconds=uptime,
        total_requests=TOTAL_REQUESTS,
        api_connected=api_connected
    )

@app.get("/version", response_model=VersionResponse)
async def version_info():
    """Get version information"""
    return VersionResponse(
        version=API_VERSION,
        service=SERVICE_NAME,
        description=SERVICE_DESCRIPTION,
        model=MODEL_NAME,
        max_documents=MAX_DOCUMENTS,
        max_length=MAX_LENGTH,
        endpoints=[
            "/health",
            "/version",
            "/v2/rerank",
            "/v1/rerank"
        ]
    )

@app.post("/v2/rerank", response_model=RerankResponse)
async def rerank_v2(request: RerankRequest):
    """Rerank documents by relevance (v2 endpoint)"""
    start_time = time.time()

    # Validate document count
    if len(request.documents) > MAX_DOCUMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Too many documents. Maximum is {MAX_DOCUMENTS}, got {len(request.documents)}"
        )

    # Create query-document pairs
    pairs = [[request.query, doc] for doc in request.documents]

    # Get relevance scores
    scores = model.predict(pairs)

    # Build results
    results = [
        RerankResult(
            index=i,
            relevance_score=float(score),
            document=doc
        )
        for i, (doc, score) in enumerate(zip(request.documents, scores))
    ]

    # Sort by relevance (highest first)
    results.sort(key=lambda x: x.relevance_score, reverse=True)

    # Apply top_n filter if specified
    returned_count = len(results)
    if request.top_n:
        results = results[:request.top_n]
        returned_count = len(results)

    processing_time = (time.time() - start_time) * 1000

    return RerankResponse(
        results=results,
        query=request.query,
        total_documents=len(request.documents),
        returned_count=returned_count,
        model=MODEL_NAME,
        processing_time_ms=round(processing_time, 2),
        api_version=API_VERSION
    )

@app.post("/v1/rerank", response_model=RerankChunksResponse)
async def rerank_chunks(request: RerankChunksRequest):
    """Rerank chunks with IDs (RAG pipeline compatibility)"""
    start_time = time.time()

    # Extract texts for reranking with metadata enrichment
    # Include ALL metadata fields (topics, keywords, questions, summary) to improve reranking relevance
    texts = []
    for chunk in request.chunks:
        text = chunk.text
        # Append all available metadata to help reranker understand full context
        if hasattr(chunk, 'topics') and chunk.topics:
            text += f"\n\nTopics: {chunk.topics}"
        if hasattr(chunk, 'keywords') and chunk.keywords:
            text += f"\nKeywords: {chunk.keywords}"
        if hasattr(chunk, 'questions') and chunk.questions:
            text += f"\nQuestions: {chunk.questions}"
        if hasattr(chunk, 'summary') and chunk.summary:
            text += f"\nSummary: {chunk.summary}"
        texts.append(text)

    if RERANKER_BACKEND == "jina":
        # Use Jina AI
        jina_response = await rerank_with_jina(request.query, texts, request.top_k)

        # Parse Jina response
        scored_chunks = []
        for result in jina_response.get("results", []):
            original_index = result.get("index")
            scored_chunks.append({
                "chunk": request.chunks[original_index],
                "score": result.get("relevance_score", 0.0)
            })
    else:
        # Use BGE model
        pairs = [[request.query, text] for text in texts]
        scores = model.predict(pairs)

        scored_chunks = [
            {
                "chunk": chunk,
                "score": float(score)
            }
            for chunk, score in zip(request.chunks, scores)
        ]

        # Sort by relevance (highest first)
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)

        # Take top_k
        scored_chunks = scored_chunks[:request.top_k]

    # Build response
    reranked = [
        RerankChunk(
            chunk_id=item["chunk"].chunk_id or item["chunk"].id or f"chunk_{i}",
            text=item["chunk"].text,
            relevance_score=item["score"],
            document_id=item["chunk"].document_id
        )
        for i, item in enumerate(scored_chunks)
    ]

    processing_time = (time.time() - start_time) * 1000

    return RerankChunksResponse(
        success=True,
        reranked_chunks=reranked,
        num_input_chunks=len(request.chunks),
        reranking_time_ms=round(processing_time, 2)
    )

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "reranking_api:app",
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        reload=False
    )
