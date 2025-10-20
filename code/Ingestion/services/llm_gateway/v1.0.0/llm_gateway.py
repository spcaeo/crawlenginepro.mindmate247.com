#!/usr/bin/env python3
"""
LLM Gateway Service v2.0.0
Proxy to Nebius AI Studio with tenant API key management and cost tracking
https://llm.mindmate247.com/

NOTE: This service is shared between Ingestion and Retrieval pipelines.
The original service is located at:
  Ingestion/services/llm_gateway/v1.0.0/
This location (Retrieval/services/llm_gateway/) contains a Unix symlink pointing to the original.

Management:
  Use Tools/pipeline-manager to start/stop/monitor this service:
  - ./pipeline-manager llm-gateway  # Start LLM Gateway service
  - ./pipeline-manager status       # Check service status
  - ./pipeline-manager health       # Check health of all dependencies
  See Tools/pipeline-manager help for full command list
"""

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import time
from typing import Optional
import uvicorn
import asyncio
from contextlib import asynccontextmanager

# Import configurations and models
from config import *
from models import *
from cache import response_cache

# Import provider detection functions from model_registry (via config.py's path setup)
from model_registry import is_sambanova_model, is_nebius_model, requires_output_cleaning, get_cleaning_pattern
import re

# ============================================================================
# Service Initialization
# ============================================================================

START_TIME = time.time()
TOTAL_REQUESTS = 0

# Global HTTP client with connection pooling
http_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global http_client

    # Startup
    print("=" * 80)
    print(f"{SERVICE_NAME} v{API_VERSION} - Starting")
    print("=" * 80)
    print(f"Nebius API URL: {NEBIUS_API_URL}")
    print(f"Supported Models: {[m.value for m in ModelType]}")
    print(f"Default Models: {DEFAULT_MODELS}")
    print(f"Cache enabled: TTL={response_cache.ttl}s, Max Size={response_cache.max_size}")
    print("=" * 80)

    # Create persistent HTTP client with connection pooling
    # Increased limits for handling 30-60 parallel metadata extraction requests
    limits = httpx.Limits(max_keepalive_connections=60, max_connections=200)
    timeout = httpx.Timeout(DEFAULT_TIMEOUT, connect=10.0)
    http_client = httpx.AsyncClient(limits=limits, timeout=timeout)

    yield

    # Shutdown
    await http_client.aclose()
    print("LLM Gateway shut down")

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
        content={
            "error": "Forbidden",
            "detail": f"Direct access forbidden. Use gateway: https://llm.mindmate247.com",
            "api_version": API_VERSION
        }
    )

# ============================================================================
# Security
# ============================================================================

def verify_api_key(
    authorization: Optional[str] = Header(None),
    apikey: Optional[str] = Header(None)
) -> str:
    """Verify tenant API key from Authorization or apikey header"""
    # Try apikey header first (from APISIX), then Authorization header
    api_key_raw = apikey or authorization

    if not api_key_raw:
        raise HTTPException(status_code=401, detail="Missing API key (provide Authorization or apikey header)")

    # Support both 'Bearer token' and 'token' formats
    api_key = api_key_raw.replace("Bearer ", "").strip()

    # Find tenant by API key
    for tenant_name, valid_key in TENANT_API_KEYS.items():
        if api_key == valid_key:
            return tenant_name

    raise HTTPException(status_code=403, detail="Invalid API key")

# ============================================================================
# Helper Functions
# ============================================================================

def determine_model(request: ChatCompletionRequest) -> str:
    """Determine which model to use based on request"""
    if request.model:
        # Explicit model specified
        return request.model
    elif request.use_case and request.use_case in DEFAULT_MODELS:
        # Use case specified (fast, basic, code, etc.)
        return DEFAULT_MODELS[request.use_case]
    else:
        # Default to basic model
        return DEFAULT_MODELS["basic"]

def estimate_cost(model: str, total_tokens: int) -> float:
    """Estimate cost based on model and tokens"""
    price_per_1m = MODEL_PRICING.get(model, 0.50)  # Default to $0.50 if unknown
    return (total_tokens / 1_000_000) * price_per_1m

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with optimized timeout and cache stats"""
    # Test Nebius connection (OPTIMIZED: 2s timeout instead of 5s)
    nebius_connected = False
    try:
        response = await http_client.get(
            f"{NEBIUS_API_URL}/models",
            headers={"Authorization": f"Bearer {NEBIUS_API_KEY}"},
            timeout=2.0  # Standardized timeout
        )
        nebius_connected = response.status_code == 200
    except Exception:
        pass

    uptime = time.time() - START_TIME
    status = "healthy" if nebius_connected else "degraded"

    # Get cache statistics
    cache_info = response_cache.stats()

    return HealthResponse(
        status=status,
        version=API_VERSION,
        service=SERVICE_NAME,
        nebius_connected=nebius_connected,
        uptime_seconds=uptime,
        total_requests=TOTAL_REQUESTS,
        cache_enabled=cache_info.get("enabled", False),
        cache_entries=cache_info.get("entries", 0),
        cache_hit_rate=cache_info.get("hit_rate", 0.0)
    )

@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics"""
    return response_cache.stats()

@app.post("/cache/clear")
async def cache_clear():
    """Clear cache"""
    response_cache.clear()
    return {"status": "ok", "message": "Cache cleared"}

@app.get("/version", response_model=VersionResponse)
async def version_info():
    """Get version information"""
    return VersionResponse(
        version=API_VERSION,
        service=SERVICE_NAME,
        description=SERVICE_DESCRIPTION,
        supported_models=[m.value for m in ModelType],
        default_models=DEFAULT_MODELS,
        endpoints=[
            "/health",
            "/version",
            "/models",
            "/v1/chat/completions",
            "/v2/chat/completions"
        ]
    )

@app.get("/models", response_model=ModelsResponse)
async def list_models():
    """List available models"""
    models = [
        ModelInfo(
            model_id=MODEL_NAMES[ModelType.FAST],
            model_type=ModelType.FAST.value,
            description="Fast 7B model, ~0.3s response",
            pricing_per_1m_tokens=MODEL_PRICING[MODEL_NAMES[ModelType.FAST]],
            recommended_for="Quick responses, high throughput"
        ),
        ModelInfo(
            model_id=MODEL_NAMES[ModelType.BALANCED],
            model_type=ModelType.BALANCED.value,
            description="Balanced 72B model, ~3.5s response",
            pricing_per_1m_tokens=MODEL_PRICING[MODEL_NAMES[ModelType.BALANCED]],
            recommended_for="General tasks, good quality"
        ),
        ModelInfo(
            model_id=MODEL_NAMES[ModelType.ADVANCED],
            model_type=ModelType.ADVANCED.value,
            description="Advanced 480B model, ~0.8s response",
            pricing_per_1m_tokens=MODEL_PRICING[MODEL_NAMES[ModelType.ADVANCED]],
            recommended_for="Complex coding, best quality"
        ),
        ModelInfo(
            model_id=MODEL_NAMES[ModelType.REASONING],
            model_type=ModelType.REASONING.value,
            description="Reasoning model for complex problems",
            pricing_per_1m_tokens=MODEL_PRICING[MODEL_NAMES[ModelType.REASONING]],
            recommended_for="Math, logic, reasoning tasks"
        ),
        ModelInfo(
            model_id=MODEL_NAMES[ModelType.VISION],
            model_type=ModelType.VISION.value,
            description="Vision model for image understanding",
            pricing_per_1m_tokens=MODEL_PRICING[MODEL_NAMES[ModelType.VISION]],
            recommended_for="Image analysis, OCR"
        )
    ]

    return ModelsResponse(
        models=models,
        default_models=DEFAULT_MODELS
    )

@app.post("/v2/chat/completions", response_model=ChatCompletionResponse)
@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: Request,
    chat_request: ChatCompletionRequest,
    authorization: Optional[str] = Header(None),
    apikey: Optional[str] = Header(None),
    use_cache: bool = True
):
    """Proxy chat completions to Nebius AI Studio with caching"""
    global TOTAL_REQUESTS
    TOTAL_REQUESTS += 1

    # Allow localhost calls without authentication (internal services)
    client_host = request.client.host
    if client_host in ["127.0.0.1", "localhost", "::1"]:
        tenant = "Internal"
    else:
        tenant = verify_api_key(authorization, apikey)

    model = determine_model(chat_request)

    # Convert messages to list of dicts for caching
    messages_list = [msg.dict() for msg in chat_request.messages]

    # Check cache first (if not streaming and caching enabled)
    cached_response = None
    if use_cache and not chat_request.stream:
        cached_response = response_cache.get(
            model=model,
            messages=messages_list,
            temperature=chat_request.temperature,
            max_tokens=chat_request.max_tokens
        )

    if cached_response:
        # Return cached response with tenant
        cached_response["tenant"] = tenant
        cached_response["metadata"]["tenant"] = tenant
        return cached_response

    # Build request payload
    payload = {
        "model": model,
        "messages": messages_list,
        "temperature": chat_request.temperature,
    }
    if chat_request.max_tokens:
        payload["max_tokens"] = chat_request.max_tokens
    if chat_request.stream:
        payload["stream"] = chat_request.stream
    if chat_request.response_format:
        payload["response_format"] = chat_request.response_format.dict(exclude_none=True)

    # Track timing
    start_time = time.time()
    api_call_start = None
    first_response_time = None

    try:
        # Determine which provider to use based on model
        if is_sambanova_model(model):
            # Route to SambaNova API
            if not SAMBANOVA_API_KEY:
                raise HTTPException(status_code=500, detail=f"SambaNova model '{model}' requested but SAMBANOVA_API_KEY not configured")

            api_url = SAMBANOVA_API_URL
            api_key = SAMBANOVA_API_KEY
            provider_name = "SambaNova"
        else:
            # Route to Nebius API (default)
            api_url = f"{NEBIUS_API_URL}/chat/completions"
            api_key = NEBIUS_API_KEY
            provider_name = "Nebius"

        # Log the routing decision
        print(f"[ROUTING] Model '{model}' → {provider_name} API: {api_url}")

        # Track API call timing
        api_call_start = time.time()

        # Handle streaming vs non-streaming requests differently
        if chat_request.stream:
            # For streaming, use stream=True and return StreamingResponse
            async def stream_generator():
                async with http_client.stream(
                    "POST",
                    api_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                ) as stream_response:
                    stream_response.raise_for_status()
                    async for chunk in stream_response.aiter_text():
                        yield chunk

            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream"
            )

        # Non-streaming: use regular post and parse JSON
        response = await http_client.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload
        )

        # Log rate limit headers from SambaNova
        rate_limit_headers = {
            "x-ratelimit-limit": response.headers.get("x-ratelimit-limit"),
            "x-ratelimit-remaining": response.headers.get("x-ratelimit-remaining"),
            "x-ratelimit-reset": response.headers.get("x-ratelimit-reset"),
            "retry-after": response.headers.get("retry-after"),
        }
        if any(rate_limit_headers.values()):
            print(f"[RATE LIMITS] {provider_name} API: {rate_limit_headers}")

        response.raise_for_status()
        first_response_time = time.time()
        api_call_duration = (first_response_time - api_call_start) * 1000 if api_call_start else 0
        print(f"[TIMING] {provider_name} API call took {api_call_duration:.0f}ms")

        result = response.json()

        # Clean output if model requires it (e.g., remove <think> tags from reasoning models)
        if requires_output_cleaning(model):
            cleaning_pattern = get_cleaning_pattern(model)
            if cleaning_pattern and "choices" in result:
                for choice in result["choices"]:
                    if "message" in choice and "content" in choice["message"]:
                        original_content = choice["message"]["content"]
                        cleaned_content = re.sub(cleaning_pattern, '', original_content, flags=re.DOTALL | re.IGNORECASE).strip()
                        choice["message"]["content"] = cleaned_content
                        print(f"[CLEANING] Removed reasoning tags from {provider_name} response (saved {len(original_content) - len(cleaned_content)} chars)")

        # Calculate metrics
        response_time = time.time() - start_time
        service_overhead = (response_time * 1000) - api_call_duration if api_call_duration else 0
        print(f"[TIMING] Total response: {response_time*1000:.0f}ms, API: {api_call_duration:.0f}ms, Overhead: {service_overhead:.0f}ms")

        usage = result.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)
        estimated_cost = estimate_cost(model, total_tokens)

        # Add metadata
        result["tenant"] = tenant
        result["metadata"] = {
            "response_time_seconds": response_time,
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "total_tokens": total_tokens,
            "estimated_cost_usd": estimated_cost,
            "model_used": model,
            "tenant": tenant,
            "cached": False
        }

        # Cache the response (if not streaming)
        if use_cache and not chat_request.stream:
            response_cache.set(
                model=model,
                messages=messages_list,
                temperature=chat_request.temperature,
                max_tokens=chat_request.max_tokens,
                response=result
            )

        return result

    except httpx.HTTPStatusError as e:
        error_text = e.response.text
        print(f"[ERROR] {provider_name} API returned {e.response.status_code}: {error_text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"{provider_name} API error: {error_text}"
        )
    except httpx.TimeoutException:
        print(f"[ERROR] Request timeout after {DEFAULT_TIMEOUT}s to {provider_name}")
        raise HTTPException(
            status_code=504,
            detail=f"Request timeout after {DEFAULT_TIMEOUT}s"
        )
    except Exception as e:
        print(f"[ERROR] LLM Gateway exception: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"LLM Gateway error: {str(e)}"
        )

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=DEFAULT_HOST,
        port=DEFAULT_PORT
    )
