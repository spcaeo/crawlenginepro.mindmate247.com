#!/usr/bin/env python3
"""
Answer Generation Service v1.0.0
LLM-based answer generation with context and citations
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
import time
from typing import List, Dict
import json
import re
import sys
from pathlib import Path

# Add parent directories to path for shared module access
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))  # PipeLineServices root

from shared import (
    get_llm_for_task,
    requires_output_cleaning,
    get_cleaning_pattern,
    get_model_info
)

import config
from models import (
    AnswerRequest, AnswerResponse, Citation,
    HealthResponse, VersionResponse, ContextChunk
)
from cache import answer_cache

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
# Lifespan Events
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
    print(f"LLM Gateway: {config.LLM_GATEWAY_URL}")
    print(f"Default Model: {config.DEFAULT_LLM_MODEL}")
    print(f"Max Context Chunks: {config.MAX_CONTEXT_CHUNKS}")
    print(f"Citations: {'Enabled' if config.ENABLE_CITATIONS else 'Disabled'}")
    print(f"Streaming: {'Enabled' if config.ENABLE_STREAMING else 'Disabled'}")
    print(f"Cache: {'Enabled' if answer_cache.enabled else 'Disabled'}")
    print(f"{'='*60}")

    # Check dependencies before starting
    print("\n🔍 Checking dependencies...")
    llm_ok = await wait_for_dependency("LLM Gateway", config.LLM_GATEWAY_URL + "/health")

    if not llm_ok:
        print("\n❌ STARTUP FAILED: Required dependencies not available")
        print("Please ensure the following services are running:")
        print(f"  - LLM Gateway Service (port 8065)")
        print("\nExiting...")
        import sys
        sys.exit(1)

    print("\n✅ All dependencies healthy - starting Answer Generation Service")
    print(f"{'='*60}\n")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("\n👋 Answer Generation Service stopped")

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

def build_context_prompt(query: str, context_chunks: List[ContextChunk], enable_citations: bool, include_metadata_questions: bool = False) -> str:
    """
    Build context prompt from retrieved chunks

    Args:
        query: User query
        context_chunks: Retrieved context chunks
        enable_citations: Whether to include citation instructions
        include_metadata_questions: Whether to include questions field in metadata (default: False for performance)

    Returns:
        Formatted prompt with context
    """
    # Limit to max chunks
    chunks_to_use = context_chunks[:config.MAX_CONTEXT_CHUNKS]

    # Build context section WITH METADATA
    context_parts = []
    for i, chunk in enumerate(chunks_to_use, 1):
        context_parts.append(f"[Source {i}]")

        # Add metadata if available
        metadata_lines = []
        if hasattr(chunk, 'topics') and chunk.topics:
            metadata_lines.append(f"Topics: {chunk.topics}")
        if hasattr(chunk, 'keywords') and chunk.keywords:
            metadata_lines.append(f"Keywords: {chunk.keywords}")
        # OPTIONAL: Include questions field (disabled by default for performance - reduces token usage ~50-100 tokens/chunk)
        if include_metadata_questions and hasattr(chunk, 'questions') and chunk.questions:
            metadata_lines.append(f"Questions: {chunk.questions}")
        if hasattr(chunk, 'summary') and chunk.summary:
            metadata_lines.append(f"Summary: {chunk.summary}")

        if metadata_lines:
            context_parts.append("\n".join(metadata_lines))
            context_parts.append("")  # Empty line between metadata and text

        # Add text
        context_parts.append(chunk.text)

        if chunk.document_id:
            context_parts.append(f"(Document: {chunk.document_id})")
        context_parts.append("")  # Empty line between sources

    context_text = "\n".join(context_parts)

    # Build user prompt
    citation_instruction = ""
    if enable_citations:
        citation_instruction = "\n\nWhen referencing information, cite the source using [Source X] notation."

    user_prompt = f"""Question: {query}

Context:
{context_text}

Please provide a comprehensive answer to the question based on the context above.{citation_instruction}"""

    return user_prompt

def extract_citations(answer: str, context_chunks: List[ContextChunk]) -> List[Citation]:
    """
    Extract citations from answer text

    Args:
        answer: Generated answer with [Source X] citations
        context_chunks: Original context chunks

    Returns:
        List of Citation objects
    """
    citations = []

    # Find all [Source X] references
    citation_pattern = r'\[Source (\d+)\]'
    matches = re.finditer(citation_pattern, answer)

    seen_sources = set()
    for match in matches:
        source_num = int(match.group(1))

        # Avoid duplicate citations
        if source_num in seen_sources:
            continue
        seen_sources.add(source_num)

        # Get corresponding chunk (1-indexed)
        if 1 <= source_num <= len(context_chunks):
            chunk = context_chunks[source_num - 1]

            # Extract relevant snippet (first 200 chars)
            snippet = chunk.text[:200]
            if len(chunk.text) > 200:
                snippet += "..."

            citations.append(Citation(
                source_id=source_num,
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                text_snippet=snippet
            ))

    return citations

async def generate_answer(
    query: str,
    context_chunks: List[ContextChunk],
    model: str,
    max_tokens: int,
    temperature: float,
    enable_citations: bool,
    cite_only_relevant_sources: bool,
    custom_system_prompt: str = None,
    include_metadata_questions: bool = False
) -> Dict:
    """
    Generate answer using LLM Gateway (non-streaming)

    Args:
        query: User query
        context_chunks: Retrieved context chunks
        model: LLM model to use
        max_tokens: Maximum tokens for answer
        temperature: Temperature for generation
        enable_citations: Whether to include citations
        cite_only_relevant_sources: Only cite relevant sources (true) or explain all sources (false)
        custom_system_prompt: Custom system prompt from Intent Service (overrides default)

    Returns:
        Dict with answer and metadata
    """
    # Build prompt with optional metadata questions
    user_prompt = build_context_prompt(query, context_chunks, enable_citations, include_metadata_questions)

    # Use custom system prompt if provided, otherwise select based on cite_only_relevant_sources
    if custom_system_prompt:
        system_prompt = custom_system_prompt
    else:
        system_prompt = (
            config.ANSWER_GENERATION_SYSTEM_PROMPT_RELEVANT_ONLY
            if cite_only_relevant_sources
            else config.ANSWER_GENERATION_SYSTEM_PROMPT_ALL_SOURCES
        )

    payload = {
        "model": model,  # Use "model" field for explicit model names
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    try:
        async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{config.LLM_GATEWAY_URL}/v1/chat/completions",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            # Extract answer
            answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Clean reasoning tags if model requires it (e.g., <think> tags from Qwen/DeepSeek models)
            if requires_output_cleaning(model):
                pattern = get_cleaning_pattern(model)
                if pattern:
                    answer = re.sub(pattern, '', answer, flags=re.DOTALL)

            answer = answer.strip()

            # Extract usage info
            usage = data.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)

            return {
                "answer": answer,
                "tokens_used": tokens_used
            }

    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"LLM Gateway error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")

async def generate_answer_stream(
    query: str,
    context_chunks: List[ContextChunk],
    model: str,
    max_tokens: int,
    temperature: float,
    enable_citations: bool,
    cite_only_relevant_sources: bool,
    custom_system_prompt: str = None,
    include_metadata_questions: bool = False
):
    """
    Generate answer using LLM Gateway with streaming (progressive delivery)

    Args:
        query: User query
        context_chunks: Retrieved context chunks
        model: LLM model to use
        max_tokens: Maximum tokens for answer
        temperature: Temperature for generation
        enable_citations: Whether to include citations
        cite_only_relevant_sources: Only cite relevant sources (true) or explain all sources (false)
        custom_system_prompt: Custom system prompt from Intent Service (overrides default)
        include_metadata_questions: Whether to include questions field in metadata (default: False for performance)

    Yields:
        SSE-formatted chunks as they arrive from LLM
    """
    # Build prompt with optional metadata questions
    user_prompt = build_context_prompt(query, context_chunks, enable_citations, include_metadata_questions)

    # Use custom system prompt if provided, otherwise select based on cite_only_relevant_sources
    if custom_system_prompt:
        system_prompt = custom_system_prompt
    else:
        system_prompt = (
            config.ANSWER_GENERATION_SYSTEM_PROMPT_RELEVANT_ONLY
            if cite_only_relevant_sources
            else config.ANSWER_GENERATION_SYSTEM_PROMPT_ALL_SOURCES
        )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True  # Enable streaming
    }

    try:
        async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT) as client:
            async with client.stream(
                "POST",
                f"{config.LLM_GATEWAY_URL}/v1/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()

                # Stream SSE chunks from LLM Gateway
                async for line in response.aiter_lines():
                    if line.strip():
                        # Forward SSE chunks directly to client
                        yield f"{line}\n\n"

    except httpx.HTTPError as e:
        # Send error as SSE event
        error_data = {"error": f"LLM Gateway error: {str(e)}"}
        yield f"data: {json.dumps(error_data)}\n\n"
    except Exception as e:
        # Send error as SSE event
        error_data = {"error": f"Failed to generate answer: {str(e)}"}
        yield f"data: {json.dumps(error_data)}\n\n"

# ============================================================================
# Health & Version Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    # Check dependent services
    llm_gateway_ok = await check_service(config.LLM_GATEWAY_URL + "/health")

    return HealthResponse(
        status="healthy" if llm_gateway_ok else "degraded",
        version=config.API_VERSION,
        service=config.SERVICE_NAME,
        dependencies={
            "llm_gateway": llm_gateway_ok,
            "cache": answer_cache.enabled
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
            "/v1/generate - Generate answer from context (non-streaming)",
            "/v1/generate/stream - Generate answer with streaming (progressive delivery)",
            "/v1/cache/clear - Clear answer cache",
            "/health - Health check",
            "/version - Version info"
        ]
    )

# ============================================================================
# Answer Generation Endpoint
# ============================================================================

@app.post("/v1/generate", response_model=AnswerResponse)
async def generate_answer_endpoint(request: AnswerRequest):
    """
    Generate answer from retrieved context using LLM

    Process:
    1. Check cache for existing answer
    2. Build context prompt from chunks
    3. Generate answer using LLM Gateway
    4. Extract citations if enabled
    5. Cache results for future use

    Example:
    ```json
    {
        "query": "What damage did vajra cause to Hanuman?",
        "context_chunks": [
            {
                "chunk_id": "doc1_chunk5",
                "text": "The vajra struck Hanuman's jaw...",
                "document_id": "jaishreeram_v1",
                "chunk_index": 5,
                "score": 0.95
            }
        ],
        "enable_citations": true
    }
    ```

    Returns answer with optional citations
    """
    start_time = time.time()
    cache_hit = False

    try:
        # Use defaults from config if not provided
        llm_model = request.llm_model or config.DEFAULT_LLM_MODEL
        max_tokens = request.max_tokens or config.DEFAULT_MAX_TOKENS
        temperature = request.temperature or config.DEFAULT_TEMPERATURE

        # Validate context chunks
        if not request.context_chunks:
            raise HTTPException(
                status_code=400,
                detail="No context chunks provided"
            )

        # If streaming is requested, delegate to streaming endpoint logic
        if request.stream:
            return StreamingResponse(
                generate_answer_stream(
                    query=request.query,
                    context_chunks=request.context_chunks,
                    model=llm_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    enable_citations=request.enable_citations,
                    cite_only_relevant_sources=request.cite_only_relevant_sources,
                    custom_system_prompt=request.system_prompt,
                    include_metadata_questions=request.include_metadata_questions
                ),
                media_type="text/event-stream"
            )

        # Check cache first
        cached_answer = None
        if request.use_cache:
            # Convert context chunks to dict for caching
            context_dicts = [chunk.dict() for chunk in request.context_chunks]
            cached_answer = answer_cache.get(
                query=request.query,
                context_chunks=context_dicts,
                model=llm_model,
                temperature=temperature
            )

        if cached_answer:
            # Cache hit - return cached answer
            cache_hit = True
            answer_text = cached_answer["answer"]
            tokens_used = cached_answer.get("tokens_used", 0)
            citations_list = [Citation(**c) for c in cached_answer.get("citations", [])]
        else:
            # Generate new answer
            result = await generate_answer(
                query=request.query,
                context_chunks=request.context_chunks,
                model=llm_model,
                max_tokens=max_tokens,
                temperature=temperature,
                enable_citations=request.enable_citations,
                cite_only_relevant_sources=request.cite_only_relevant_sources,
                custom_system_prompt=request.system_prompt,
                include_metadata_questions=request.include_metadata_questions
            )

            answer_text = result["answer"]
            tokens_used = result["tokens_used"]

            # Extract citations if enabled
            citations_list = []
            if request.enable_citations:
                citations_list = extract_citations(answer_text, request.context_chunks)

            # Cache the results
            if request.use_cache:
                context_dicts = [chunk.dict() for chunk in request.context_chunks]
                answer_cache.set(
                    query=request.query,
                    context_chunks=context_dicts,
                    model=llm_model,
                    temperature=temperature,
                    answer_data={
                        "answer": answer_text,
                        "tokens_used": tokens_used,
                        "citations": [c.dict() for c in citations_list]
                    }
                )

        # Calculate generation time
        generation_time_ms = (time.time() - start_time) * 1000

        return AnswerResponse(
            success=True,
            query=request.query,
            answer=answer_text,
            citations=citations_list if request.enable_citations else None,
            num_chunks_used=len(request.context_chunks[:config.MAX_CONTEXT_CHUNKS]),
            generation_time_ms=generation_time_ms,
            cache_hit=cache_hit,
            llm_model_used=llm_model,
            tokens_used=tokens_used,
            api_version=config.API_VERSION
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Answer generation failed: {str(e)}")

@app.post("/v1/generate/stream")
async def generate_answer_stream_endpoint(request: AnswerRequest):
    """
    Generate answer with streaming for progressive delivery (better UX)

    Same as /v1/generate but streams response chunks as they arrive from LLM.
    This provides a better user experience - users see partial answers immediately
    instead of waiting for the full response.

    IMPORTANT:
    - Streaming responses are NOT cached (cache is write-only for final answers)
    - Returns Server-Sent Events (SSE) format
    - Compatible with OpenAI streaming format

    Example usage:
    ```python
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url, json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    print(data["choices"][0]["delta"]["content"], end="")
    ```
    """
    try:
        # Use defaults from config
        llm_model = request.llm_model or config.DEFAULT_LLM_MODEL
        max_tokens = request.max_tokens or config.DEFAULT_MAX_TOKENS
        temperature = request.temperature or config.DEFAULT_TEMPERATURE

        # Validate context chunks
        if not request.context_chunks:
            raise HTTPException(
                status_code=400,
                detail="No context chunks provided"
            )

        # NOTE: Streaming responses are NOT cached
        # Cache is write-only - we only cache complete answers from non-streaming requests

        # Return streaming response
        return StreamingResponse(
            generate_answer_stream(
                query=request.query,
                context_chunks=request.context_chunks,
                model=llm_model,
                max_tokens=max_tokens,
                temperature=temperature,
                enable_citations=request.enable_citations,
                cite_only_relevant_sources=request.cite_only_relevant_sources,
                custom_system_prompt=request.system_prompt,
                include_metadata_questions=request.include_metadata_questions
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming answer generation failed: {str(e)}")

@app.post("/v1/cache/clear")
async def clear_cache():
    """Clear answer cache"""
    try:
        num_deleted = answer_cache.clear()
        return {
            "success": True,
            "message": f"Cleared {num_deleted} cache entries",
            "api_version": config.API_VERSION
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

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
