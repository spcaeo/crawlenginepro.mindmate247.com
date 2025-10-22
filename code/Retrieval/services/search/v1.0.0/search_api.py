#!/usr/bin/env python3
"""
Search Service v1.0.0
Dense vector search + metadata boosting (ALL 7 fields)
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
import time
from typing import List, Dict

import config
from models import (
    SearchRequest, SearchResponse, SearchResultItem,
    HealthResponse, VersionResponse, MetadataMatch
)
from metadata_boost import apply_metadata_boost

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title=config.SERVICE_NAME,
    version=config.API_VERSION,
    description=config.SERVICE_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service start time for uptime tracking
SERVICE_START_TIME = time.time()

# ============================================================================
# Security Middleware (localhost only)
# ============================================================================

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Security check - only allow localhost and internal network access"""
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
            "detail": "Direct access forbidden. Use gateway if available.",
            "api_version": config.API_VERSION
        }
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
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    print(f"  ✅ {service_name} is healthy")
                    return True
        except:
            pass

        wait_time = 2 ** attempt
        print(f"  ⏳ Waiting for {service_name}... (attempt {attempt + 1}/{max_retries}, retry in {wait_time}s)")
        await asyncio.sleep(wait_time)

    print(f"  ❌ ERROR: {service_name} not available at {url}")
    return False

@app.on_event("startup")
async def startup_event():
    """Print startup information and check dependencies"""
    print(f"\n{'='*60}")
    print(f"🚀 {config.SERVICE_NAME} v{config.API_VERSION}")
    print(f"{'='*60}")
    print(f"Port: {config.DEFAULT_PORT}")
    print(f"Embeddings: {config.EMBEDDINGS_URL}")
    print(f"Storage: {config.STORAGE_URL}")
    print(f"\nMetadata Boost Weights (ALL 7 FIELDS):")
    print(f"  Standard Fields:")
    print(f"    - keywords:  {config.BOOST_WEIGHTS['keywords']:.2f}")
    print(f"    - topics:    {config.BOOST_WEIGHTS['topics']:.2f}")
    print(f"    - questions: {config.BOOST_WEIGHTS['questions']:.2f}")
    print(f"    - summary:   {config.BOOST_WEIGHTS['summary']:.2f}")
    print(f"  Enhanced Fields:")
    print(f"    - semantic_keywords:     {config.BOOST_WEIGHTS['semantic_keywords']:.2f}")
    print(f"    - entity_relationships:  {config.BOOST_WEIGHTS['entity_relationships']:.2f}")
    print(f"    - attributes:            {config.BOOST_WEIGHTS['attributes']:.2f}")
    print(f"  Max Total Boost: {config.MAX_TOTAL_BOOST:.2f}")
    print(f"{'='*60}")

    # Check dependencies before starting
    print("\n🔍 Checking dependencies...")
    # Extract base URL (remove /v1/... paths)
    embeddings_health_url = config.EMBEDDINGS_URL.split("/v1")[0] + "/health"
    storage_health_url = config.STORAGE_URL.split("/v1")[0] + "/health"
    embeddings_ok = await wait_for_dependency("Embeddings Service", embeddings_health_url)
    storage_ok = await wait_for_dependency("Storage Service", storage_health_url)

    if not embeddings_ok or not storage_ok:
        print("\n❌ STARTUP FAILED: Required dependencies not available")
        print("Please ensure the following services are running:")
        if not embeddings_ok:
            print(f"  - Embeddings Service (port 8063)")
        if not storage_ok:
            print(f"  - Storage Service (port 8064)")
        print("\nExiting...")
        import sys
        sys.exit(1)

    print("\n✅ All dependencies healthy - starting Search Service")
    print(f"{'='*60}\n")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("\n👋 Search Service stopped")

# ============================================================================
# Helper Functions
# ============================================================================

async def check_service(url: str) -> bool:
    """Check if a service is reachable"""
    try:
        async with httpx.AsyncClient(timeout=2) as client:  # STANDARDIZED: 2s timeout
            response = await client.get(url)
            return response.status_code == 200
    except:
        return False

async def get_query_embedding(query: str) -> Dict:
    """
    Get embedding from Embeddings Service

    Args:
        query: Query text to embed

    Returns:
        {"dense_vector": [0.1, 0.2, ...]}
    """
    try:
        async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT) as client:
            response = await client.post(
                config.EMBEDDINGS_URL,
                json={"input": [query]}
            )
            response.raise_for_status()
            data = response.json()

            # Extract the first dense embedding (Embeddings v3.0.1 format)
            # Response format: {"data": [{"dense_embedding": [...]}]}
            embeddings_data = data.get("data", [])
            if not embeddings_data or not embeddings_data[0].get("dense_embedding"):
                raise ValueError("No embeddings returned from service")

            return {"dense_vector": embeddings_data[0]["dense_embedding"]}
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Embeddings service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get embedding: {str(e)}")

async def search_milvus(
    collection: str,
    query_vector: List[float],
    tenant_id: str = None,
    limit: int = 20,
    filter_expr: str = None
) -> List[Dict]:
    """
    Search Milvus Storage with dense vector

    Args:
        collection: Collection name
        query_vector: Dense query vector
        tenant_id: Optional tenant filter
        limit: Number of results
        filter_expr: Optional filter expression

    Returns:
        List of search results with metadata
    """
    payload = {
        "collection_name": collection,
        "query_dense": query_vector,
        "limit": limit,
        "tenant_id": tenant_id,
        "filter": filter_expr,
        "output_fields": [
            "id", "text", "document_id", "chunk_index",
            "keywords", "topics", "questions", "summary",
            "semantic_keywords", "entity_relationships", "attributes"  # NEW: +3 enhanced fields
        ],
        "search_mode": "dense"  # Dense only (no sparse)
    }

    try:
        async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{config.STORAGE_URL}/search",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                raise ValueError(f"Storage search failed: {data.get('error', 'Unknown error')}")

            return data.get("results", [])
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Storage service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search storage: {str(e)}")

# ============================================================================
# Health & Version Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    # Check dependent services (extract base URL before adding /health)
    embeddings_health_url = config.EMBEDDINGS_URL.split("/v1")[0] + "/health"
    storage_health_url = config.STORAGE_URL.split("/v1")[0] + "/health"
    embeddings_ok = await check_service(embeddings_health_url)
    storage_ok = await check_service(storage_health_url)

    return HealthResponse(
        status="healthy" if (embeddings_ok and storage_ok) else "degraded",
        version=config.API_VERSION,
        service=config.SERVICE_NAME,
        dependencies={
            "embeddings": embeddings_ok,
            "storage": storage_ok
        },
        uptime_seconds=time.time() - SERVICE_START_TIME
    )

@app.get("/version", response_model=VersionResponse)
async def get_version():
    """Get service version and available endpoints"""
    return VersionResponse(
        version=config.API_VERSION,
        service=config.SERVICE_NAME,
        description=config.SERVICE_DESCRIPTION,
        endpoints=[
            "/v1/search - Search with metadata boost",
            "/v1/search/vector-only - Pure vector search (no boost)",
            "/health - Health check",
            "/version - Version info"
        ]
    )

# ============================================================================
# Search Endpoint
# ============================================================================

@app.post("/v1/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest):
    """
    Dense vector search + metadata boosting (ALL 7 fields)

    Process:
    1. Get query embedding from Embeddings Service
    2. Search Milvus Storage with dense vector
    3. Apply metadata boost (keywords, topics, questions, summary, semantic_keywords, entity_relationships, attributes)
    4. Return top-k results sorted by boosted score

    Example:
    ```json
    {
        "query_text": "What damage did vajra cause to Hanuman?",
        "collection": "test_jaishreeram_v1",
        "top_k": 10,
        "use_metadata_boost": true
    }
    ```
    """
    start_time = time.time()

    try:
        # Step 1: Get query embedding
        t1 = time.time()
        embedding_response = await get_query_embedding(request.query_text)
        query_vector = embedding_response["dense_vector"]
        embedding_time_ms = (time.time() - t1) * 1000

        # Step 2: Search Milvus Storage (get 2x results for boosting)
        t2 = time.time()
        search_limit = min(request.top_k * 2, config.MAX_TOP_K)
        search_results = await search_milvus(
            collection=request.collection,
            query_vector=query_vector,
            tenant_id=request.tenant_id,
            limit=search_limit,
            filter_expr=request.filter_expr
        )
        milvus_time_ms = (time.time() - t2) * 1000

        # Step 3: Apply metadata boost
        t3 = time.time()
        boost_weights = request.boost_weights or config.BOOST_WEIGHTS

        boosted_results = []
        for result in search_results:
            # Apply metadata boost if enabled
            if request.use_metadata_boost:
                metadata_boost, metadata_match = apply_metadata_boost(
                    query=request.query_text,
                    chunk=result,
                    weights=boost_weights,
                    max_boost=config.MAX_TOTAL_BOOST
                )
                final_score = result.get("score", 0.0) + metadata_boost
            else:
                metadata_boost = 0.0
                metadata_match = MetadataMatch()
                final_score = result.get("score", 0.0)

            # Build result item
            boosted_results.append(
                SearchResultItem(
                    chunk_id=result.get("id", ""),
                    text=result.get("text", ""),
                    score=final_score,
                    vector_score=result.get("score", 0.0),
                    metadata_boost=metadata_boost,
                    metadata_matches=metadata_match,
                    document_id=result.get("document_id"),
                    chunk_index=result.get("chunk_index"),
                    # Standard metadata (4 fields)
                    keywords=result.get("keywords"),
                    topics=result.get("topics"),
                    questions=result.get("questions"),
                    summary=result.get("summary"),
                    # Enhanced metadata (3 NEW fields)
                    semantic_keywords=result.get("semantic_keywords"),
                    entity_relationships=result.get("entity_relationships"),
                    attributes=result.get("attributes")
                )
            )

        # Step 4: Sort by final score and take top-k
        boosted_results.sort(key=lambda x: x.score, reverse=True)
        final_results = boosted_results[:request.top_k]
        metadata_boost_time_ms = (time.time() - t3) * 1000

        # Calculate search time
        search_time_ms = (time.time() - start_time) * 1000

        # Log detailed timing breakdown
        print(f"[TIMING] Total: {search_time_ms:.1f}ms | Embedding: {embedding_time_ms:.1f}ms | Milvus: {milvus_time_ms:.1f}ms | Metadata Boost: {metadata_boost_time_ms:.1f}ms")

        return SearchResponse(
            success=True,
            results=final_results,
            total_found=len(final_results),
            collection=request.collection,
            search_time_ms=search_time_ms,
            metadata_boost_applied=request.use_metadata_boost,
            api_version=config.API_VERSION
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/v1/search/vector-only")
async def search_vector_only(request: SearchRequest):
    """
    Pure vector search without metadata boosting
    Useful for comparing with/without boost
    """
    # Force metadata boost off
    request.use_metadata_boost = False
    return await search_endpoint(request)

# ============================================================================
# Error Handler
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "api_version": config.API_VERSION
        }
    )

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.DEFAULT_HOST,
        port=config.DEFAULT_PORT,
        log_level="info"
    )
