#!/usr/bin/env python3
"""
Retrieval Pipeline API v1.0.0
Main orchestrator for RAG retrieval

Pipeline: Query → Search → Rerank → Compress → Answer Generation
Internal Services: ports 8071-8074
Public API: port 8070

Management:
  Use Tools/pipeline-manager to start/stop/monitor this service:
  - ./pipeline-manager start          # Start all services
  - ./pipeline-manager start-retrieval  # Start Retrieval pipeline only
  - ./pipeline-manager retrieval      # Start this API service individually
  - ./pipeline-manager status         # Check service status
  - ./pipeline-manager health         # Check health of all dependencies
  See Tools/pipeline-manager help for full command list

Author: CrawlEnginePro
"""

import os
import time
import httpx
import logging
import random
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse

# Import configuration and models
from config import *
from models import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# HTTP Client & Lifespan Management
# ============================================================================
http_client = None
retrieval_semaphore = None  # Rate limiter for concurrent retrievals

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global http_client, retrieval_semaphore

    # Startup
    logger.info("=" * 80)
    logger.info(f"Starting {SERVICE_NAME} v{API_VERSION}")
    logger.info("=" * 80)
    logger.info(f"Listening on {DEFAULT_HOST}:{DEFAULT_PORT}")
    logger.info("")
    logger.info("Internal Services Configuration:")
    logger.info(f"  Intent:      {INTENT_SERVICE_URL}")
    logger.info(f"  Search:      {SEARCH_SERVICE_URL}")
    logger.info(f"  Reranking:   {RERANK_SERVICE_URL}")
    logger.info(f"  Compression: {COMPRESS_SERVICE_URL}")
    logger.info(f"  Answer Gen:  {ANSWER_SERVICE_URL}")
    logger.info("")
    logger.info(f"Pipeline Configuration:")
    logger.info(f"  Search Top-K:         {DEFAULT_SEARCH_TOP_K}")
    logger.info(f"  Rerank Top-K:         {DEFAULT_RERANK_TOP_K}")
    logger.info(f"  Compression Ratio:    {DEFAULT_COMPRESSION_RATIO}")
    logger.info(f"  Score Threshold:      {DEFAULT_SCORE_THRESHOLD}")
    logger.info(f"  Max Context Chunks:   {DEFAULT_MAX_CONTEXT_CHUNKS}")
    logger.info("")
    logger.info(f"Rate Limiting: Max {MAX_CONCURRENT_RETRIEVALS} concurrent retrievals")
    logger.info("")
    logger.info("Checking dependency health...")

    # Create HTTP client with connection pooling
    http_client = httpx.AsyncClient(
        limits=httpx.Limits(
            max_connections=CONNECTION_POOL_MAX,
            max_keepalive_connections=CONNECTION_POOL_SIZE
        ),
        timeout=httpx.Timeout(CONNECTION_TIMEOUT)
    )

    # Initialize rate limiter for retrieval requests
    retrieval_semaphore = asyncio.Semaphore(MAX_CONCURRENT_RETRIEVALS)

    # Quick health check on startup (non-blocking)
    services_to_check = {
        "Intent": f"{INTENT_SERVICE_URL.replace('/v1', '')}/health",
        "Search": f"{SEARCH_SERVICE_URL.replace('/v1', '')}/health",
        "Reranking": f"{RERANK_SERVICE_URL.replace('/v1', '')}/health",
        "Compression": f"{COMPRESS_SERVICE_URL.replace('/v1', '')}/health",
        "Answer Gen": f"{ANSWER_SERVICE_URL.replace('/v1', '')}/health"
    }

    healthy_services = 0
    unhealthy_services = []

    for service_name, health_url in services_to_check.items():
        try:
            response = await http_client.get(health_url, timeout=2.0)
            if response.status_code == 200:
                data = response.json()
                version = data.get("api_version") or data.get("version", "unknown")
                logger.info(f"  ✓ {service_name:<13} - healthy (v{version})")
                healthy_services += 1
            else:
                logger.warning(f"  ✗ {service_name:<13} - HTTP {response.status_code}")
                unhealthy_services.append(service_name)
        except httpx.TimeoutException:
            logger.warning(f"  ✗ {service_name:<13} - timeout")
            unhealthy_services.append(service_name)
        except Exception as e:
            logger.warning(f"  ✗ {service_name:<13} - {str(e)[:50]}")
            unhealthy_services.append(service_name)

    logger.info("")
    logger.info(f"Dependency Health: {healthy_services}/5 services healthy")

    if unhealthy_services:
        logger.warning(f"WARNING: Some services are unavailable: {', '.join(unhealthy_services)}")
        logger.warning("API will operate in degraded mode. Some endpoints may fail.")
    else:
        logger.info("✓ All dependencies healthy - ready for requests")

    logger.info("=" * 80)

    yield

    # Shutdown
    await http_client.aclose()
    logger.info(f"Shutting down {SERVICE_NAME}")

# ============================================================================
# FastAPI App
# ============================================================================
app = FastAPI(
    title=SERVICE_NAME,
    description=SERVICE_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ============================================================================
# Helper Functions
# ============================================================================
async def retry_with_exponential_backoff(
    func,
    *args,
    max_retries: int = MAX_RETRIES,
    base_delay: float = RETRY_BASE_DELAY,
    max_delay: float = RETRY_MAX_DELAY,
    **kwargs
):
    """
    Retry async function with exponential backoff and jitter

    Retry strategy: 1s, 2s, 4s (with jitter)
    Prevents thundering herd by adding random jitter
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except (httpx.TimeoutException, httpx.ConnectError, httpx.ConnectTimeout) as e:
            last_exception = e
            if attempt < max_retries - 1:
                # Exponential backoff: 1s, 2s, 4s, 8s, ...
                delay = min(base_delay * (2 ** attempt), max_delay)
                # Add jitter (±25%) to prevent thundering herd
                jitter = delay * 0.25 * (2 * random.random() - 1)
                sleep_time = delay + jitter

                logger.warning(
                    f"Retry {attempt + 1}/{max_retries} after {sleep_time:.2f}s "
                    f"(transient error: {type(e).__name__})"
                )
                await asyncio.sleep(sleep_time)
            else:
                logger.error(f"All {max_retries} retries exhausted")
                raise
        except httpx.HTTPStatusError as e:
            # Don't retry on 4xx client errors (except 429 rate limit)
            if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                logger.error(f"Client error {e.response.status_code}, not retrying")
                raise

            last_exception = e
            if attempt < max_retries - 1:
                delay = min(base_delay * (2 ** attempt), max_delay)
                jitter = delay * 0.25 * (2 * random.random() - 1)
                sleep_time = delay + jitter

                logger.warning(
                    f"Retry {attempt + 1}/{max_retries} after {sleep_time:.2f}s "
                    f"(HTTP {e.response.status_code})"
                )
                await asyncio.sleep(sleep_time)
            else:
                raise

    # Should never reach here, but just in case
    raise last_exception

# ============================================================================
# Internal Service Functions
# ============================================================================
async def call_intent_service(query: str, enable_citations: bool = True, response_style: str = None, response_format: str = "markdown") -> Dict[str, Any]:
    """Call Intent Service for query analysis and prompt adaptation"""
    async def _call():
        call_start = time.time()
        response = await http_client.post(
            f"{INTENT_SERVICE_URL}/analyze",
            json={
                "query": query,
                "enable_citations": enable_citations,
                "response_style": response_style,
                "response_format": response_format
            },
            timeout=INTENT_TIMEOUT
        )
        call_time_ms = (time.time() - call_start) * 1000
        print(f"[TIMING] HTTP call to Intent Service: {call_time_ms:.0f}ms")
        response.raise_for_status()
        return response.json()

    try:
        return await retry_with_exponential_backoff(_call)
    except httpx.HTTPError as e:
        logger.error(f"Intent service error after retries: {e}")
        # Return default fallback if intent detection fails
        return {
            "intent": "factual_retrieval",
            "language": "en",
            "complexity": "moderate",
            "requires_math": False,
            "system_prompt": None,  # Will use default in Answer service
            "confidence": 0.0,
            "analysis_time_ms": 0,
            "error": str(e)
        }

async def call_search_service(
    query: str,
    collection: str,
    tenant_id: str = "default",
    top_k: int = 20,
    use_metadata_boost: bool = True
) -> Dict[str, Any]:
    """Call Search Service with retry logic"""
    async def _call():
        response = await http_client.post(
            f"{SEARCH_SERVICE_URL}/search",
            json={
                "query_text": query,
                "collection": collection,
                "tenant_id": tenant_id,
                "top_k": top_k,
                "use_metadata_boost": use_metadata_boost
            },
            timeout=SEARCH_TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    try:
        return await retry_with_exponential_backoff(_call)
    except httpx.HTTPError as e:
        logger.error(f"Search service error after retries: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Search service error: {str(e)}"
        )

async def call_rerank_service(
    query: str,
    chunks: List[Dict[str, Any]],
    top_k: int = 10
) -> Dict[str, Any]:
    """Call Reranking Service with retry logic"""
    async def _call():
        response = await http_client.post(
            f"{RERANK_SERVICE_URL}/rerank",
            json={
                "query": query,
                "chunks": chunks,
                "top_k": top_k
            },
            timeout=RERANK_TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    try:
        return await retry_with_exponential_backoff(_call)
    except httpx.HTTPError as e:
        logger.error(f"Reranking service error after retries: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Reranking service error: {str(e)}"
        )

async def call_compression_service(
    query: str,
    chunks: List[Dict[str, Any]],
    compression_ratio: float = 0.5,
    score_threshold: float = 0.3
) -> Dict[str, Any]:
    """Call Compression Service with retry logic"""
    async def _call():
        response = await http_client.post(
            f"{COMPRESS_SERVICE_URL}/compress",
            json={
                "query": query,
                "chunks": chunks,
                "compression_ratio": compression_ratio,
                "score_threshold": score_threshold
            },
            timeout=COMPRESS_TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    try:
        return await retry_with_exponential_backoff(_call)
    except httpx.HTTPError as e:
        logger.error(f"Compression service error after retries: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Compression service error: {str(e)}"
        )

async def call_answer_service(
    query: str,
    context_chunks: List[Dict[str, Any]],
    enable_citations: bool = True,
    model: str = None,  # Will use DEFAULT_ANSWER_MODEL if not specified
    max_tokens: int = None,  # Will use service default if not specified
    temperature: float = 0.3,
    system_prompt: Optional[str] = None,
    stream: bool = True  # Enable streaming by default for better UX
):
    """Call Answer Generation Service with retry logic"""
    async def _call():
        # Use default model if not specified
        model_to_use = model if model else DEFAULT_ANSWER_MODEL

        payload = {
            "query": query,
            "context_chunks": context_chunks,
            "enable_citations": enable_citations,
            "llm_model": model_to_use,  # Use llm_model field (correct field name for Answer Generation API)
            "temperature": temperature,
            "stream": stream  # Pass streaming preference
        }

        # Add max_tokens if provided (otherwise Answer Service will use its default)
        if max_tokens:
            payload["max_tokens"] = max_tokens

        # Add custom system prompt if provided
        if system_prompt:
            payload["system_prompt"] = system_prompt

        response = await http_client.post(
            f"{ANSWER_SERVICE_URL}/generate",
            json=payload,
            timeout=ANSWER_TIMEOUT
        )
        response.raise_for_status()

        # If streaming, return the raw response (caller will handle the stream)
        if stream:
            return response
        else:
            return response.json()

    try:
        return await retry_with_exponential_backoff(_call)
    except httpx.HTTPError as e:
        logger.error(f"Answer generation service error after retries: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Answer generation service error: {str(e)}"
        )

# ============================================================================
# API Endpoints
# ============================================================================
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": SERVICE_NAME,
        "version": API_VERSION,
        "description": SERVICE_DESCRIPTION,
        "endpoints": {
            "health": "/health",
            "retrieve": "POST /v1/retrieve",
            "docs": "/docs"
        },
        "pipeline_stages": [
            "0. Intent Detection (parallel with search, LLM-based)",
            "1. Search (Dense vector + metadata boost)",
            "2. Reranking (BGE-Reranker-v2-M3)",
            "3. Compression (LLM-powered)",
            "4. Answer Generation (LLM with intent-adapted prompts)"
        ]
    }

@app.get("/health")
async def health_check():
    """
    Aggregated health check endpoint

    Checks all downstream microservices and returns comprehensive status.
    """
    start_time = time.time()

    # Initialize service health status
    services = {
        "intent": {"status": "unknown", "url": f"{INTENT_SERVICE_URL.replace('/v1', '')}/health"},
        "search": {"status": "unknown", "url": f"{SEARCH_SERVICE_URL.replace('/v1', '')}/health"},
        "reranking": {"status": "unknown", "url": f"{RERANK_SERVICE_URL.replace('/v1', '')}/health"},
        "compression": {"status": "unknown", "url": f"{COMPRESS_SERVICE_URL.replace('/v1', '')}/health"},
        "answer_generation": {"status": "unknown", "url": f"{ANSWER_SERVICE_URL.replace('/v1', '')}/health"}
    }

    # Check each service (async, with timeout)
    async def check_service(name: str, url: str) -> dict:
        try:
            response = await http_client.get(url, timeout=2.0)  # STANDARDIZED: 2s timeout
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "version": data.get("api_version") or data.get("version", "unknown"),
                    "response_time_ms": round((time.time() - start_time) * 1000, 2)
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "response_time_ms": round((time.time() - start_time) * 1000, 2)
                }
        except httpx.TimeoutException:
            return {
                "status": "timeout",
                "error": "Health check timeout (2s)",
                "response_time_ms": 2000
            }
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e),
                "response_time_ms": round((time.time() - start_time) * 1000, 2)
            }

    # Check all services in parallel
    service_checks = {
        name: check_service(name, info["url"])
        for name, info in services.items()
    }
    results = await asyncio.gather(*service_checks.values(), return_exceptions=True)

    # Update service status
    for (name, _), result in zip(services.items(), results):
        if isinstance(result, Exception):
            services[name] = {
                "status": "error",
                "error": str(result)
            }
        else:
            services[name] = result

    # Determine overall status
    healthy_count = sum(1 for s in services.values() if s.get("status") == "healthy")
    total_count = len(services)

    if healthy_count == total_count:
        overall_status = "healthy"
    elif healthy_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "service": SERVICE_NAME,
        "version": API_VERSION,
        "timestamp": datetime.now().isoformat(),
        "dependencies": services,
        "health_summary": {
            "total_services": total_count,
            "healthy": healthy_count,
            "unhealthy": total_count - healthy_count
        },
        "response_time_ms": round((time.time() - start_time) * 1000, 2)
    }

@app.post("/v1/retrieve", response_model=RetrievalResponse)
async def retrieve(request: RetrievalRequest):
    """
    RAG Retrieval Pipeline

    Pipeline: Query → Search → Rerank → Compress → Answer Generation

    Rate Limited: Max {MAX_CONCURRENT_RETRIEVALS} concurrent retrievals
    """
    # Rate limiting: acquire semaphore (wait if limit reached)
    async with retrieval_semaphore:
        logger.info(f"Retrieving for query: '{request.query[:50]}...' in collection: {request.collection_name}")

        pipeline_start = time.time()
        stages = {}

        try:
            # Stage 0: Intent Detection (parallel with Stage 1: Search)
            intent_task = None
            intent_data = None

            if ENABLE_INTENT_DETECTION:
                # Start intent detection in parallel (non-blocking)
                intent_start = time.time()
                print(f"[TIMING] Creating Intent Service task at {time.time():.3f}")
                intent_task = asyncio.create_task(call_intent_service(
                    query=request.query,
                    enable_citations=request.enable_citations,
                    response_style=request.response_style,
                    response_format=request.response_format
                ))
                print(f"[TIMING] Intent Service task created at {time.time():.3f}")
                logger.info("Intent detection started (parallel with search)")

            # Stage 1: Search
            if ENABLE_SEARCH:
                search_start = time.time()
                search_result = await call_search_service(
                    query=request.query,
                    collection=request.collection_name,
                    tenant_id=request.tenant_id,
                    top_k=request.search_top_k,
                    use_metadata_boost=request.use_metadata_boost
                )
                search_results = search_result.get("results", [])
                search_time_ms = (time.time() - search_start) * 1000

                stages["search"] = PipelineStageInfo(
                    time_ms=search_time_ms,
                    success=True,
                    metadata={
                        "results_count": len(search_results),
                        "top_k": request.search_top_k,
                        "metadata_boost_enabled": request.use_metadata_boost
                    }
                )
                logger.info(f"Search complete: {len(search_results)} results ({search_time_ms:.0f}ms)")
            else:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Search stage is disabled"
                )

            if len(search_results) == 0:
                # No results found - return empty response
                return RetrievalResponse(
                    success=False,
                    query=request.query,
                    collection_name=request.collection_name,
                    tenant_id=request.tenant_id,
                    answer="I couldn't find any relevant information to answer your question.",
                    citations=[],
                    context_chunks=[],
                    stages=stages,
                    total_time_ms=(time.time() - pipeline_start) * 1000,
                    search_results_count=0,
                    reranked_count=0,
                    compressed_count=0,
                    context_count=0,
                    timestamp=datetime.now().isoformat()
                )

            # Create metadata lookup for later use
            metadata_lookup = {
                r.get('chunk_id'): {
                    'topics': r.get('topics', ''),
                    'keywords': r.get('keywords', ''),
                    'summary': r.get('summary', ''),
                    'questions': r.get('questions', ''),
                    'document_id': r.get('document_id', 'unknown')
                }
                for r in search_results
            }

            # Stage 2: Reranking
            if ENABLE_RERANKING and request.enable_reranking:
                rerank_start = time.time()

                # Prepare chunks for reranking
                chunks_for_rerank = [
                    {
                        "chunk_id": r.get("chunk_id"),
                        "text": r.get("text"),
                        "document_id": r.get("document_id", "unknown")
                    }
                    for r in search_results
                ]

                rerank_result = await call_rerank_service(
                    query=request.query,
                    chunks=chunks_for_rerank,
                    top_k=request.rerank_top_k
                )
                reranked_chunks = rerank_result.get("reranked_chunks", [])
                rerank_time_ms = (time.time() - rerank_start) * 1000

                stages["reranking"] = PipelineStageInfo(
                    time_ms=rerank_time_ms,
                    success=True,
                    metadata={
                        "input_count": len(chunks_for_rerank),
                        "output_count": len(reranked_chunks),
                        "top_k": request.rerank_top_k
                    }
                )
                logger.info(f"Reranking complete: {len(reranked_chunks)} results ({rerank_time_ms:.0f}ms)")
            else:
                # Skip reranking - use search results directly
                reranked_chunks = [
                    {
                        "chunk_id": r.get("chunk_id"),
                        "text": r.get("text"),
                        "document_id": r.get("document_id", "unknown"),
                        "relevance_score": r.get("score", 0.0)
                    }
                    for r in search_results[:request.rerank_top_k]
                ]
                stages["reranking"] = PipelineStageInfo(
                    time_ms=0,
                    success=True,
                    metadata={"skipped": True}
                )

            # Stage 3: Compression
            if ENABLE_COMPRESSION and request.enable_compression:
                compress_start = time.time()

                compress_result = await call_compression_service(
                    query=request.query,
                    chunks=reranked_chunks,
                    compression_ratio=request.compression_ratio,
                    score_threshold=request.score_threshold
                )
                compressed_chunks = compress_result.get("compressed_chunks", [])
                compress_time_ms = (time.time() - compress_start) * 1000

                stages["compression"] = PipelineStageInfo(
                    time_ms=compress_time_ms,
                    success=True,
                    metadata={
                        "input_count": len(reranked_chunks),
                        "output_count": len(compressed_chunks),
                        "compression_ratio": request.compression_ratio,
                        "score_threshold": request.score_threshold
                    }
                )
                logger.info(f"Compression complete: {len(compressed_chunks)} results ({compress_time_ms:.0f}ms)")
            else:
                # Skip compression - use reranked chunks directly
                compressed_chunks = [
                    {
                        "id": chunk.get("chunk_id"),
                        "compressed_text": chunk.get("text"),
                        "original_text": chunk.get("text")
                    }
                    for chunk in reranked_chunks
                ]
                stages["compression"] = PipelineStageInfo(
                    time_ms=0,
                    success=True,
                    metadata={"skipped": True}
                )

            # Stage 4: Answer Generation
            if ENABLE_ANSWER_GENERATION:
                answer_start = time.time()

                # Await intent detection result (if enabled)
                custom_system_prompt = None
                recommended_model = None
                recommended_max_tokens = None
                if intent_task:
                    try:
                        print(f"[TIMING] Awaiting Intent Service task at {time.time():.3f}")
                        intent_data = await intent_task
                        print(f"[TIMING] Intent Service task completed at {time.time():.3f}")
                        intent_time_ms = (time.time() - intent_start) * 1000
                        custom_system_prompt = intent_data.get("system_prompt")
                        recommended_model = intent_data.get("recommended_model")  # Get recommended model from Intent Service
                        recommended_max_tokens = intent_data.get("recommended_max_tokens")  # Get recommended max_tokens from Intent Service

                        # Build intent metadata - include v2.0 pattern scoring if available
                        intent_metadata = {
                            "intent": intent_data.get("intent"),
                            "language": intent_data.get("language"),
                            "complexity": intent_data.get("complexity"),
                            "confidence": intent_data.get("confidence"),
                            "recommended_model": recommended_model,
                            "recommended_max_tokens": recommended_max_tokens,
                            "has_custom_prompt": custom_system_prompt is not None
                        }

                        # Forward v2.0 pattern matcher metadata if present
                        if "metadata" in intent_data:
                            intent_service_metadata = intent_data["metadata"]
                            if "used_pattern" in intent_service_metadata:
                                intent_metadata["used_pattern"] = intent_service_metadata["used_pattern"]
                            if "analysis_method" in intent_service_metadata:
                                intent_metadata["analysis_method"] = intent_service_metadata["analysis_method"]
                            if "pattern_scoring" in intent_service_metadata:
                                intent_metadata["pattern_scoring"] = intent_service_metadata["pattern_scoring"]

                        stages["intent_detection"] = PipelineStageInfo(
                            time_ms=intent_time_ms,
                            success=True,
                            metadata=intent_metadata
                        )
                        logger.info(f"Intent detection complete: {intent_data.get('intent')} ({intent_time_ms:.0f}ms)")
                    except Exception as e:
                        intent_time_ms = (time.time() - intent_start) * 1000
                        logger.warning(f"Intent detection failed ({intent_time_ms:.0f}ms): {str(e)} - continuing with defaults")
                        stages["intent_detection"] = PipelineStageInfo(
                            time_ms=intent_time_ms,
                            success=False,
                            error=str(e)
                        )
                        # Continue with None values (will use request.model as fallback)

                # Prepare context chunks with metadata
                context_chunks = []
                for chunk in compressed_chunks[:request.max_context_chunks]:
                    chunk_id = chunk.get('id')
                    metadata = metadata_lookup.get(chunk_id, {})
                    context_chunks.append({
                        "chunk_id": chunk_id,
                        "text": chunk.get('compressed_text', chunk.get('original_text', '')),
                        "document_id": metadata.get('document_id', 'unknown'),
                        "topics": metadata.get('topics', ''),
                        "keywords": metadata.get('keywords', ''),
                        "summary": metadata.get('summary', ''),
                        "questions": metadata.get('questions', '')
                    })

                # Use recommended model from Intent Service if available, otherwise fall back to request.model
                model_to_use = recommended_model or request.model

                # If streaming requested, return stream directly (no pipeline metadata)
                if request.stream:
                    answer_response = await call_answer_service(
                        query=request.query,
                        context_chunks=context_chunks,
                        enable_citations=request.enable_citations,
                        model=model_to_use,
                        max_tokens=recommended_max_tokens,
                        temperature=request.temperature,
                        system_prompt=custom_system_prompt,
                        stream=True
                    )
                    # Return the streaming response directly
                    return StreamingResponse(
                        answer_response.aiter_bytes(),
                        media_type="text/event-stream"
                    )

                # Non-streaming: collect full answer and return with pipeline metadata
                answer_result = await call_answer_service(
                    query=request.query,
                    context_chunks=context_chunks,
                    enable_citations=request.enable_citations,
                    model=model_to_use,
                    max_tokens=recommended_max_tokens,
                    temperature=request.temperature,
                    system_prompt=custom_system_prompt,
                    stream=False
                )
                answer_time_ms = (time.time() - answer_start) * 1000

                # Extract answer and citations safely
                answer = answer_result.get("answer", "")
                citations_data = answer_result.get("citations") or []
                citations = [Citation(**cit) for cit in citations_data] if citations_data else []

                stages["answer_generation"] = PipelineStageInfo(
                    time_ms=answer_time_ms,
                    success=True,
                    metadata={
                        "context_chunks": len(context_chunks),
                        "citations": len(citations),
                        "model_used": model_to_use,
                        "model_requested": request.model,
                        "max_tokens_used": recommended_max_tokens,
                        "temperature": request.temperature,
                        "used_custom_prompt": custom_system_prompt is not None,
                        "used_recommended_model": recommended_model is not None,
                        "used_recommended_max_tokens": recommended_max_tokens is not None
                    }
                )
                logger.info(f"Answer generation complete ({answer_time_ms:.0f}ms, model: {model_to_use})")
            else:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Answer generation stage is disabled"
                )

            # Calculate total processing time
            total_time_ms = (time.time() - pipeline_start) * 1000

            logger.info(f"Pipeline complete: {total_time_ms:.0f}ms total")

            return RetrievalResponse(
                success=True,
                query=request.query,
                collection_name=request.collection_name,
                tenant_id=request.tenant_id,
                answer=answer,
                citations=citations,
                context_chunks=context_chunks,
                stages=stages,
                total_time_ms=total_time_ms,
                search_results_count=len(search_results),
                reranked_count=len(reranked_chunks),
                compressed_count=len(compressed_chunks),
                context_count=len(context_chunks),
                timestamp=datetime.now().isoformat()
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Pipeline processing error: {str(e)}"
            )

# ============================================================================
# Run Server
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        log_level="info"
    )
