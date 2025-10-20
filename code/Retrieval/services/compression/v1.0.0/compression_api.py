#!/usr/bin/env python3
"""
Compression Service v2.0.0
LLM-powered contextual compression - extract only relevant sentences
https://compress.mindmate247.com/
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import asyncio
import requests
import re
import uvicorn
from typing import List, Dict

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
# Startup/Shutdown Events
# ============================================================================

async def wait_for_dependency(service_name: str, url: str, max_retries: int = 5) -> bool:
    """
    Wait for a dependency service to be healthy

    Args:
        service_name: Name of the service
        url: Health check URL
        max_retries: Maximum number of retries

    Returns:
        True if service is healthy, False otherwise
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {service_name} is healthy")
                return True
        except:
            pass

        wait_time = 2 ** attempt
        print(f"  ⏳ Waiting for {service_name}... (attempt {attempt + 1}/{max_retries}, retry in {wait_time}s)")
        asyncio.run(asyncio.sleep(wait_time))

    print(f"  ❌ ERROR: {service_name} not available at {url}")
    return False

@app.on_event("startup")
async def startup_event():
    """Print startup information and check dependencies"""
    print("\n" + "="*60)
    print(f"🚀 {SERVICE_NAME} v{API_VERSION}")
    print("="*60)
    print(f"Port: {DEFAULT_PORT}")
    print(f"LLM Gateway: {LLM_GATEWAY_URL}")
    print(f"Default Model: {DEFAULT_MODEL}")
    print(f"Max Chunks: {MAX_CHUNKS_PER_REQUEST}")
    print("="*60)

    # Check dependencies before starting
    print("\n🔍 Checking dependencies...")
    llm_gateway_url = LLM_GATEWAY_URL.replace("/v1/chat/completions", "/health")
    llm_ok = await asyncio.to_thread(wait_for_dependency, "LLM Gateway", llm_gateway_url)

    if not llm_ok:
        print("\n❌ STARTUP FAILED: Required dependencies not available")
        print("Please ensure the following services are running:")
        print(f"  - LLM Gateway Service (port 8065)")
        print("\nExiting...")
        import sys
        sys.exit(1)

    print("\n✅ All dependencies healthy - starting Compression Service")
    print("="*60 + "\n")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("\n👋 Compression Service stopped")

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
            "detail": f"Direct access forbidden. Use gateway: https://compress.mindmate247.com",
            "api_version": API_VERSION
        }
    )

# ============================================================================
# Compression Logic
# ============================================================================

def batch_compress_chunks(chunks: List[Chunk], question: str, model: str, max_tokens: int) -> List[Dict]:
    """
    Compress all chunks in a single LLM call for efficiency

    Args:
        chunks: List of chunks to compress
        question: User question to determine relevance
        model: Model to use (7B-fast, 72B, 480B)
        max_tokens: Maximum tokens for all compressed outputs

    Returns:
        List of dicts with compressed text and metrics
    """
    start_time = time.time()

    # Build batch prompt with all chunks
    chunk_texts = []
    for i, chunk in enumerate(chunks):
        chunk_id = chunk.id or chunk.chunk_id or f"chunk_{i}"
        chunk_texts.append(f"=== CHUNK {i+1} (ID: {chunk_id}) ===\n{chunk.text}\n")

    batch_prompt = f"""Extract and preserve relevant information from each chunk below that helps answer the question.
Return the compressed version of each chunk, keeping the "=== CHUNK [N] ===" markers.

Question: {question}

{chr(10).join(chunk_texts)}
Instructions:
- Extract sentences relevant to the question
- For factual/specification queries: Preserve ALL factual details, numbers, specs, features, and data points
- For comparison queries: Keep both technical details AND their intended use/benefits
- Include supporting context and descriptive details that explain WHY or HOW things work
- Preserve technical terms along with their purpose or function
- Keep lists, bullet points, and structured data intact
- If you see sections labeled "Technical Specifications", "Features", "Details", preserve them completely
- Keep exact wording from original text
- Maintain the "=== CHUNK [N] (ID: ...)" markers in your response
- If a chunk has no relevant content, write "No relevant content" for that chunk
- Aim for informative compression that preserves all key facts, not minimal extraction

Compressed Chunks:"""

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            # Map model names to use_case
            model_mapping = {
                "7B-fast": "fast",
                "72B": "balanced",
                "480B": "advanced"
            }
            use_case = model_mapping.get(model, "fast")

            # Call LLM Gateway
            headers = {
                "Content-Type": "application/json"
            }
            if LLM_GATEWAY_API_KEY:
                headers["Authorization"] = f"Bearer {LLM_GATEWAY_API_KEY}"

            response = requests.post(
                LLM_GATEWAY_URL,
                headers=headers,
                json={
                    "use_case": use_case,
                    "messages": [{"role": "user", "content": batch_prompt}],
                    "max_tokens": max_tokens,
                    "temperature": TEMPERATURE,
                    "top_p": TOP_P
                },
                timeout=COMPRESSION_TIMEOUT
            )

            if response.status_code == 200:
                result = response.json()
                compressed_batch = result['choices'][0]['message']['content'].strip()

                # Parse batched response back into individual chunks
                compressed_parts = compressed_batch.split("=== CHUNK")
                results = []

                for i, chunk in enumerate(chunks):
                    compressed_text = ""

                    # Try to find matching chunk in response
                    for part in compressed_parts:
                        if f"{i+1}" in part[:20]:  # Check if chunk number matches
                            # Extract text after the marker
                            lines = part.split("\n", 1)
                            if len(lines) > 1:
                                compressed_text = lines[1].strip()
                                # Remove any trailing chunk markers
                                if "=== CHUNK" in compressed_text:
                                    compressed_text = compressed_text.split("=== CHUNK")[0].strip()
                            break

                    # Fallback if parsing failed or no relevant content
                    if not compressed_text or len(compressed_text) < 20 or "no relevant content" in compressed_text.lower():
                        compressed_text = chunk.summary if chunk.summary else chunk.text[:500]

                    results.append({
                        "compressed_text": compressed_text,
                        "compression_time_ms": (time.time() - start_time) * 1000,
                        "original_length": len(chunk.text),
                        "compressed_length": len(compressed_text)
                    })

                return results
            else:
                last_error = f"LLM Gateway returned {response.status_code}: {response.text}"

        except requests.exceptions.Timeout:
            last_error = f"Request timeout after {COMPRESSION_TIMEOUT}s"
        except requests.exceptions.RequestException as e:
            last_error = f"Request failed: {str(e)}"
        except Exception as e:
            last_error = f"Compression error: {str(e)}"

        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY * (attempt + 1))

    # Fallback: use summaries or truncated text
    return [{
        "compressed_text": chunk.summary if chunk.summary else chunk.text[:500],
        "compression_time_ms": (time.time() - start_time) * 1000,
        "original_length": len(chunk.text),
        "compressed_length": len(chunk.summary if chunk.summary else chunk.text[:500]),
        "error": last_error
    } for chunk in chunks]

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    # Test LLM Gateway connection (STANDARDIZED: 2s timeout)
    llm_connected = False
    try:
        response = requests.get(
            LLM_GATEWAY_URL.replace("/v1/chat/completions", "/health"),
            timeout=2  # STANDARDIZED: 2s timeout
        )
        llm_connected = response.status_code == 200
    except:
        pass

    uptime = time.time() - START_TIME

    return HealthResponse(
        status="healthy" if llm_connected else "degraded",
        version=API_VERSION,
        service=SERVICE_NAME,
        llm_gateway_connected=llm_connected,
        uptime_seconds=uptime,
        total_requests=TOTAL_REQUESTS
    )

@app.get("/version", response_model=VersionResponse)
async def version_info():
    """Get version information"""
    return VersionResponse(
        version=API_VERSION,
        service=SERVICE_NAME,
        description=SERVICE_DESCRIPTION,
        default_model=DEFAULT_MODEL,
        max_chunks=MAX_CHUNKS_PER_REQUEST,
        max_tokens_per_chunk=MAX_TOKENS_PER_CHUNK,
        endpoints=[
            "/health",
            "/version",
            "/v2/compress",
            "/v1/compress"
        ]
    )

@app.post("/v2/compress", response_model=CompressionResponse)
async def compress_v2(request: CompressionRequest):
    """Compress chunks by extracting only relevant sentences (v2 endpoint)"""
    start_time = time.time()

    # Support both 'question' and 'query' fields
    question = request.question or request.query
    if not question:
        raise HTTPException(status_code=400, detail="Either 'question' or 'query' field is required")

    # Validate chunk count
    if len(request.chunks) > MAX_CHUNKS_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"Too many chunks. Maximum is {MAX_CHUNKS_PER_REQUEST}, got {len(request.chunks)}"
        )

    # SCORE-BASED FILTERING (NEW FEATURE)
    # Filter chunks by relevance score before LLM compression
    filtered_chunks = []
    skipped_chunks = []
    
    for chunk in request.chunks:
        if chunk.relevance_score is not None:
            if chunk.relevance_score >= request.score_threshold:
                filtered_chunks.append(chunk)
            else:
                skipped_chunks.append({"id": chunk.id or chunk.chunk_id or "unknown", "score": chunk.relevance_score})
        else:
            filtered_chunks.append(chunk)
    
    if skipped_chunks:
        print(f"  ⏭️  Filtered out {len(skipped_chunks)} chunks (score < {request.score_threshold})")
        for skip in skipped_chunks[:3]:
            print(f"     - {skip['id']}: score={skip['score']:.4f}")
    
    if not filtered_chunks:
        print(f"  ⚠️  Warning: All chunks filtered, using all chunks")
        filtered_chunks = request.chunks
    else:
        print(f"  ✅ Kept {len(filtered_chunks)}/{len(request.chunks)} chunks for compression")

    # Calculate total max tokens for batch
    max_tokens_total = request.max_tokens_per_chunk * len(request.chunks)

    # Batch compress all chunks
    compression_results = batch_compress_chunks(
        filtered_chunks,
        question,
        request.model,
        max_tokens=max_tokens_total
    )

    # Build response
    compressed_chunks = []
    total_input_tokens = 0
    total_output_tokens = 0

    for chunk, result in zip(filtered_chunks, compression_results):
        original_len = result.get("original_length", len(chunk.text))
        compressed_len = result.get("compressed_length", len(result["compressed_text"]))

        # Support both id and chunk_id fields
        chunk_identifier = chunk.id or chunk.chunk_id or "unknown"

        compressed_chunks.append(CompressedChunk(
            id=chunk_identifier,
            original_text=chunk.text,
            compressed_text=result["compressed_text"],
            original_length=original_len,
            compressed_length=compressed_len,
            compression_ratio=compressed_len / original_len if original_len > 0 else 1.0,
            compression_time_ms=result["compression_time_ms"]
        ))

        # Estimate tokens (rough: 1 token ≈ 4 characters)
        total_input_tokens += original_len // 4
        total_output_tokens += compressed_len // 4

    total_time = (time.time() - start_time) * 1000
    avg_ratio = sum(c.compression_ratio for c in compressed_chunks) / len(compressed_chunks) if compressed_chunks else 1.0

    return CompressionResponse(
        compressed_chunks=compressed_chunks,
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
        total_compression_time_ms=total_time,
        avg_compression_ratio=avg_ratio,
        model_used=request.model,
        api_version=API_VERSION
    )

@app.post("/v1/compress")
async def compress_v1(request: CompressionRequest):
    """Compress chunks (v1 endpoint for backward compatibility)"""
    # Call v2 endpoint
    response = await compress_v2(request)

    # Convert to v1 format (simpler structure)
    return {
        "compressed_chunks": [
            {
                "id": c.id,
                "original_text": c.original_text,
                "compressed_text": c.compressed_text,
                "original_length": c.original_length,
                "compressed_length": c.compressed_length,
                "compression_ratio": c.compression_ratio
            }
            for c in response.compressed_chunks
        ]
    }

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "compression_api:app",
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        reload=False
    )
