#!/usr/bin/env python3
"""
Embeddings Service v3.0.2 - Multi-Provider (Dense-only, Fast)
Dense embeddings via Nebius AI Studio + Jina AI APIs with parallel processing
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import uvicorn
import time
import asyncio
from contextlib import asynccontextmanager
from typing import List

# Import configurations and models
from config import *
from models import *
from cache import embeddings_cache

# ============================================================================
# Service Initialization
# ============================================================================

START_TIME = time.time()
TOTAL_REQUESTS = 0

# Global HTTP client with connection pooling
http_client = None

# Semaphore for concurrent request limiting
request_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global http_client

    # Startup
    print("=" * 80)
    print(f"{SERVICE_NAME} v{API_VERSION} - Starting")
    print("=" * 80)
    print(f"Providers:")
    if NEBIUS_API_KEY:
        print(f"  ✓ Nebius AI Studio: {NEBIUS_API_URL}")
    if SAMBANOVA_API_KEY:
        print(f"  ✓ SambaNova AI (FREE): {SAMBANOVA_API_URL}")
    if JINA_API_KEY:
        print(f"  ✓ Jina AI: {JINA_API_URL}")
    print(f"Default Model: {DEFAULT_MODEL}")
    print(f"Model Dimension: {MODEL_DIMENSIONS[DEFAULT_MODEL]}")
    print(f"Model Provider: {get_provider_for_model(DEFAULT_MODEL)}")
    print(f"Caching enabled: {ENABLE_CACHING} (TTL={CACHE_TTL}s, Max={CACHE_MAX_SIZE})")
    print(f"Max concurrent requests: {MAX_CONCURRENT_REQUESTS}")
    print("=" * 80)

    # Create persistent HTTP client with connection pooling
    limits = httpx.Limits(max_keepalive_connections=50, max_connections=100)
    timeout = httpx.Timeout(DEFAULT_TIMEOUT, connect=10.0)
    http_client = httpx.AsyncClient(limits=limits, timeout=timeout)

    print("✅ HTTP client initialized")
    providers = []
    if NEBIUS_API_KEY:
        providers.append("Nebius AI")
    if SAMBANOVA_API_KEY:
        providers.append("SambaNova AI")
    if JINA_API_KEY:
        providers.append("Jina AI")
    print(f"✅ Ready to generate dense embeddings via {' + '.join(providers)}")

    # Warmup: Prefetch embedding model with dummy text (reduces first-query latency)
    print("🔥 Warming up embedding model...")
    try:
        from models import EmbeddingRequest as WarmupRequest
        warmup_text = "warmup"
        warmup_req = WarmupRequest(input=warmup_text, model=DEFAULT_MODEL)
        # Call the endpoint function directly (not via HTTP)
        _ = await create_dense_embeddings(warmup_req)
        print(f"✅ Model warmup complete ({DEFAULT_MODEL} ready)")
    except Exception as e:
        print(f"⚠️  Model warmup failed (first request will be slower): {e}")

    print("=" * 80)

    yield

    # Shutdown
    await http_client.aclose()
    print("Embeddings Service shut down")

app = FastAPI(
    title=f"{SERVICE_NAME} v{API_VERSION}",
    description=SERVICE_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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
        content={"error": "Access forbidden", "detail": "This service is for internal use only"}
    )

# ============================================================================
# Helper Functions
# ============================================================================

def count_tokens_approx(texts: List[str]) -> int:
    """Approximate token count (4 chars ≈ 1 token)"""
    return sum(len(text) // 4 for text in texts)

async def call_nebius_api(texts: List[str], model: str) -> dict:
    """
    Call Nebius AI Studio embeddings API

    Args:
        texts: List of texts to embed
        model: Model name

    Returns:
        API response dict

    Raises:
        HTTPException on API errors
    """
    async with request_semaphore:  # Limit concurrent API calls
        headers = {
            "Authorization": f"Bearer {NEBIUS_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "input": texts,
            "model": model
        }

        try:
            response = await http_client.post(
                NEBIUS_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please retry after a moment."
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Nebius API error: {e.response.text}"
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Nebius API timeout. Please retry."
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to call Nebius API: {str(e)}"
            )

async def call_sambanova_api(texts: List[str], model: str) -> dict:
    """
    Call SambaNova AI embeddings API

    Args:
        texts: List of texts to embed
        model: Model name

    Returns:
        API response dict

    Raises:
        HTTPException on API errors
    """
    async with request_semaphore:  # Limit concurrent API calls
        headers = {
            "Authorization": f"Bearer {SAMBANOVA_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "input": texts,
            "model": model
        }

        try:
            response = await http_client.post(
                SAMBANOVA_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please retry after a moment."
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"SambaNova API error: {e.response.text}"
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="SambaNova API timeout. Please retry."
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to call SambaNova API: {str(e)}"
            )

async def call_jina_api(texts: List[str], model: str) -> dict:
    """
    Call Jina AI embeddings API

    Args:
        texts: List of texts to embed
        model: Model name

    Returns:
        API response dict

    Raises:
        HTTPException on API errors
    """
    async with request_semaphore:  # Limit concurrent API calls
        headers = {
            "Authorization": f"Bearer {JINA_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "input": texts,
            "model": model
        }

        try:
            response = await http_client.post(
                JINA_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please retry after a moment."
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Jina API error: {e.response.text}"
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Jina API timeout. Please retry."
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to call Jina API: {str(e)}"
            )

def get_provider_for_model(model: str) -> str:
    """
    Get the API provider for a given model

    Args:
        model: Model name

    Returns:
        Provider name ("nebius", "sambanova", or "jina")

    Raises:
        HTTPException if model is not supported
    """
    # Try to get from MODEL_PROVIDERS mapping
    for model_enum, provider in MODEL_PROVIDERS.items():
        if model_enum.value == model or model_enum == model:
            return provider

    # Fallback: infer from model name
    if "jina" in model.lower():
        return "jina"
    elif "E5-Mistral-7B-Instruct" in model or model.startswith("E5-"):
        return "sambanova"  # SambaNova uses this specific naming
    elif any(nebius_model in model for nebius_model in ["e5-mistral", "bge", "qwen"]):
        return "nebius"

    # Default to nebius if unknown
    return "nebius"

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with actual API connectivity test"""
    uptime = time.time() - START_TIME
    provider = get_provider_for_model(DEFAULT_MODEL)

    # Test actual API connectivity (FIXED: was always returning "healthy")
    api_connected = False
    try:
        if provider == "jina" and JINA_API_KEY:
            # Test Jina AI connectivity
            response = await http_client.get(
                "https://api.jina.ai/v1/embeddings",  # Jina health/models endpoint
                headers={"Authorization": f"Bearer {JINA_API_KEY}"},
                timeout=2.0
            )
            api_connected = response.status_code in [200, 405]  # 405 = method not allowed (GET on POST endpoint)
        elif provider == "nebius" and NEBIUS_API_KEY:
            # Test Nebius AI connectivity
            response = await http_client.get(
                f"{NEBIUS_API_URL.replace('/embeddings', '/models')}",  # Models list endpoint
                headers={"Authorization": f"Bearer {NEBIUS_API_KEY}"},
                timeout=2.0
            )
            api_connected = response.status_code == 200
    except Exception:
        api_connected = False

    # Determine status based on API connectivity
    status = "healthy" if api_connected else "degraded"

    device = f"{provider}_cloud_gpu"
    source = f"{provider}_api"

    # Get cache stats
    cache_info = embeddings_cache.stats()

    return HealthResponse(
        status=status,
        version=API_VERSION,
        service=SERVICE_NAME,
        model=DEFAULT_MODEL,
        dense_dimension=MODEL_DIMENSIONS[DEFAULT_MODEL],
        device=device,
        uptime_seconds=uptime,
        total_requests=TOTAL_REQUESTS,
        source=source,
        api_connected=api_connected,
        cache_enabled=cache_info.get("enabled", False),
        cache_entries=cache_info.get("entries", 0),
        cache_hit_rate=cache_info.get("hit_rate", 0.0)
    )

@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics"""
    return embeddings_cache.stats()

@app.post("/cache/clear")
async def clear_cache():
    """Clear all cached embeddings"""
    embeddings_cache.clear()
    return {"status": "ok", "message": "Cache cleared successfully"}

@app.post("/v1/embeddings", response_model=DenseEmbeddingResponse)
async def create_dense_embeddings(request: EmbeddingRequest):
    """
    Generate dense embeddings via Nebius AI Studio or Jina AI API

    NEW in v3.0.2:
    - Multi-provider support: Nebius AI + Jina AI
    - Auto-routing based on model
    - Dense vectors only (no sparse)
    - Parallel API calls for batch requests
    - 10-20x faster than local CPU inference

    Request:
    {
        "input": "Your text here",
        "model": "jina-embeddings-v3",  // or "intfloat/e5-mistral-7b-instruct"
        "normalize": true
    }

    Response:
    {
        "data": [
            {
                "dense_embedding": [0.123, ...],  // Dimension depends on model
                "index": 0
            }
        ],
        "model": "jina-embeddings-v3",
        "dense_dimension": 1024,  // Varies by model (from model registry)
        "source": "jina_api",  // or "nebius_api"
        ...
    }
    """
    try:
        # Convert input to list
        texts = [request.input] if isinstance(request.input, str) else request.input

        if not texts:
            raise HTTPException(status_code=400, detail="Input cannot be empty")

        # Validate batch size
        if len(texts) > MAX_BATCH_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Batch size {len(texts)} exceeds maximum {MAX_BATCH_SIZE}"
            )

        # Check cache first
        cached_result = None
        if ENABLE_CACHING:
            cached_result = embeddings_cache.get(texts, request.model, request.normalize)

        if cached_result:
            # Return cached embeddings
            return DenseEmbeddingResponse(**cached_result)

        # Cache miss - determine provider and call API
        start_time = time.time()
        provider = get_provider_for_model(request.model)

        # Call appropriate API based on provider
        if provider == "jina":
            if not JINA_API_KEY:
                raise HTTPException(
                    status_code=503,
                    detail="Jina AI provider not configured. Please set JINA_API_KEY."
                )
            api_response = await call_jina_api(texts, request.model)
        elif provider == "sambanova":
            if not SAMBANOVA_API_KEY:
                raise HTTPException(
                    status_code=503,
                    detail="SambaNova AI provider not configured. Please set SAMBANOVA_API_KEY."
                )
            api_response = await call_sambanova_api(texts, request.model)
        else:  # nebius
            if not NEBIUS_API_KEY:
                raise HTTPException(
                    status_code=503,
                    detail="Nebius AI provider not configured. Please set NEBIUS_API_KEY."
                )
            api_response = await call_nebius_api(texts, request.model)

        processing_time = (time.time() - start_time) * 1000

        # Extract embeddings from API response
        # Both Nebius and Jina follow OpenAI format: {"data": [{"embedding": [...], "index": 0}, ...]}
        embedding_data = []
        for item in api_response.get("data", []):
            embedding_data.append(
                DenseEmbeddingData(
                    dense_embedding=item["embedding"],
                    index=item["index"]
                )
            )

        # Get dimension from first embedding
        dense_dimension = len(embedding_data[0].dense_embedding) if embedding_data else MODEL_DIMENSIONS.get(
            request.model, MODEL_DIMENSIONS[DEFAULT_MODEL])

        response = DenseEmbeddingResponse(
            data=embedding_data,
            model=request.model,
            dense_dimension=dense_dimension,
            total_tokens=count_tokens_approx(texts),
            api_version=API_VERSION,
            processing_time_ms=processing_time,
            cached=False,
            source=f"{provider}_api"
        )

        # Cache the result
        if ENABLE_CACHING:
            embeddings_cache.set(texts, request.model, request.normalize, response.dict())

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Dense embedding generation failed: {str(e)}"
        )

# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        log_level="info"
    )
