#!/usr/bin/env python3
"""
Ingestion Pipeline API v1.0.0
Main orchestrator for document ingestion into vector database

Pipeline: Document → Chunking → Metadata → Embeddings → Storage
Internal Services: ports 8061-8065
Public API: port 8060

Management:
  Use Tools/pipeline-manager to start/stop/monitor this service:
  - ./pipeline-manager start          # Start all services
  - ./pipeline-manager start-ingestion  # Start Ingestion pipeline only
  - ./pipeline-manager ingestion      # Start this API service individually
  - ./pipeline-manager status         # Check service status
  - ./pipeline-manager health         # Check health of all dependencies
  See Tools/pipeline-manager help for full command list

Author: CrawlEnginePro
"""

import os
import sys
import time
import httpx
import logging
import tiktoken
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add shared directory to path FIRST (before imports that need it)
SHARED_DIR = Path(__file__).resolve().parents[3] / "shared"
sys.path.insert(0, str(SHARED_DIR))

# Import and load environment using config_loader
from config_loader import load_shared_env, get_env

# Load environment configuration (dev/prod/staging)
load_shared_env()

# Import service_registry and model_registry
from service_registry import get_registry
from model_registry import DEFAULT_EMBEDDING_MODEL, get_embedding_dimension, get_llm_for_task, get_metadata_enum_for_model

# ============================================================================
# Configuration
# ============================================================================
API_VERSION = "1.0.0"
SERVICE_NAME = "Ingestion Pipeline API"
SERVICE_DESCRIPTION = "Document ingestion orchestrator with CRUD operations"

# Model configuration (from shared registry)
METADATA_MODEL = get_llm_for_task("metadata_extraction", complexity="complex")

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("INGESTION_API_PORT", "8060"))

# Internal service URLs - using service_registry (environment-aware)
registry = get_registry()
CHUNKING_URL = registry.get_service_url('chunking')  # Already includes /v1/orchestrate
METADATA_URL = registry.get_service_url('metadata')  # Already includes /v1/metadata
EMBEDDINGS_URL = registry.get_service_url('embeddings')  # Already includes /v1/embeddings
STORAGE_URL = registry.get_service_url('storage')  # Already includes /v1
LLM_GATEWAY_URL = registry.get_service_url('llm_gateway')  # Already includes /v1/chat/completions

# Connection pooling for internal service calls
CONNECTION_POOL_SIZE = int(os.getenv("CONNECTION_POOL_SIZE", "20"))
CONNECTION_POOL_MAX = int(os.getenv("CONNECTION_POOL_MAX", "100"))
CONNECTION_TIMEOUT = int(os.getenv("CONNECTION_TIMEOUT", "60"))

# Input validation limits (Security: prevent memory exhaustion)
MAX_DOCUMENT_SIZE = int(os.getenv("MAX_DOCUMENT_SIZE", "10485760"))  # 10MB
MAX_CHUNKS_PER_DOCUMENT = int(os.getenv("MAX_CHUNKS_PER_DOCUMENT", "1000"))
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "100"))
MIN_DOCUMENT_LENGTH = 50  # Minimum 50 characters
MAX_COLLECTION_NAME_LENGTH = 255
MAX_DOCUMENT_ID_LENGTH = 255

# Rate limiting (Pipeline Optimization: prevent pipeline overwhelm)
MAX_CONCURRENT_INGESTIONS = int(os.getenv("MAX_CONCURRENT_INGESTIONS", "10"))

# Retry configuration (Resilience: handle transient failures)
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_BASE_DELAY = float(os.getenv("RETRY_BASE_DELAY", "1.0"))  # seconds
RETRY_MAX_DELAY = float(os.getenv("RETRY_MAX_DELAY", "10.0"))  # seconds

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# HTTP Client & Lifespan Management
# ============================================================================
http_client = None
ingestion_semaphore = None  # Rate limiter for concurrent ingestions

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global http_client, ingestion_semaphore

    # Startup
    logger.info("=" * 80)
    logger.info(f"Starting {SERVICE_NAME} v{API_VERSION}")
    logger.info("=" * 80)
    logger.info(f"Listening on {HOST}:{PORT}")
    logger.info("")
    logger.info("Internal Services Configuration:")
    logger.info(f"  Chunking:    {CHUNKING_URL}")
    logger.info(f"  Metadata:    {METADATA_URL}")
    logger.info(f"  Embeddings:  {EMBEDDINGS_URL}")
    logger.info(f"  Storage:     {STORAGE_URL}")
    logger.info(f"  LLM Gateway: {LLM_GATEWAY_URL}")
    logger.info("")
    logger.info(f"Rate Limiting: Max {MAX_CONCURRENT_INGESTIONS} concurrent ingestions")
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

    # Initialize rate limiter for ingestion requests
    import asyncio
    ingestion_semaphore = asyncio.Semaphore(MAX_CONCURRENT_INGESTIONS)

    # Quick health check on startup (non-blocking)
    services_to_check = {
        "Chunking": CHUNKING_URL.replace("/v1/orchestrate", "/health"),
        "Metadata": METADATA_URL.replace("/v1/metadata", "/health"),
        "Embeddings": EMBEDDINGS_URL.replace("/v1/embeddings", "/health"),
        "Storage": STORAGE_URL.replace("/v1", "") + "/health",
        "LLM Gateway": LLM_GATEWAY_URL.replace("/v1/chat/completions", "/health")  # Fixed: strip /v1/chat/completions first
    }

    healthy_services = 0
    unhealthy_services = []

    for service_name, health_url in services_to_check.items():
        try:
            response = await http_client.get(health_url, timeout=2.0)
            if response.status_code == 200:
                data = response.json()
                version = data.get("version", "unknown")
                logger.info(f"  ✓ {service_name:<12} - healthy (v{version})")
                healthy_services += 1
            else:
                logger.warning(f"  ✗ {service_name:<12} - HTTP {response.status_code}")
                unhealthy_services.append(service_name)
        except httpx.TimeoutException:
            logger.warning(f"  ✗ {service_name:<12} - timeout")
            unhealthy_services.append(service_name)
        except Exception as e:
            logger.warning(f"  ✗ {service_name:<12} - {str(e)[:50]}")
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
# Request/Response Models
# ============================================================================
class IngestDocumentRequest(BaseModel):
    """Request model for document ingestion with full parameter control"""
    # Document fields
    text: str = Field(
        ...,
        description="Document text content",
        min_length=MIN_DOCUMENT_LENGTH,
        max_length=MAX_DOCUMENT_SIZE
    )
    document_id: str = Field(
        ...,
        description="Unique document identifier",
        min_length=1,
        max_length=MAX_DOCUMENT_ID_LENGTH
    )
    collection_name: str = Field(
        ...,
        description="Target collection name",
        min_length=1,
        max_length=MAX_COLLECTION_NAME_LENGTH
    )
    tenant_id: str = Field(
        default="default",
        description="Tenant ID for multi-tenancy",
        max_length=MAX_COLLECTION_NAME_LENGTH
    )

    # Chunking parameters (passed to Chunking Service)
    chunking_method: str = Field(default="recursive", description="Chunking method: recursive, markdown, token")
    max_chunk_size: int = Field(default=1000, ge=100, le=10000, description="Maximum chunk size in characters")
    chunk_overlap: int = Field(default=300, ge=0, le=1000, description="Overlap between chunks in characters")
    separators: Optional[List[str]] = Field(default=None, description="Custom separators for recursive chunking")
    markdown_headers: Optional[List[str]] = Field(default=None, description="Headers to split on for markdown chunking")
    encoding: str = Field(default="cl100k_base", description="Tokenizer encoding (cl100k_base for GPT-4)")

    # Metadata parameters (passed to Metadata Service via Chunking Service)
    generate_metadata: bool = Field(default=True, description="Generate semantic metadata for chunks")
    keywords_count: str = Field(default="5", description="Number of keywords to extract per chunk (e.g., '5', '5-10')")
    topics_count: str = Field(default="3", description="Number of topics to extract per chunk (e.g., '3', '2-5')")
    questions_count: str = Field(default="3", description="Number of questions to generate per chunk (e.g., '3', '3-5')")
    summary_length: str = Field(default="1-2 sentences", description="Length of summary (e.g., '1-2 sentences', 'brief', 'detailed')")

    # Embedding parameters (passed to Embeddings Service via Chunking Service)
    generate_embeddings: bool = Field(default=True, description="Generate vector embeddings for chunks")
    embedding_model: str = Field(default=DEFAULT_EMBEDDING_MODEL, description="Embedding model to use (jina-embeddings-v3, E5-Mistral-7B-Instruct, etc.)")

    # Storage parameters (passed to Storage Service via Chunking Service)
    storage_mode: str = Field(default="new_collection", description="Storage mode: none, new_collection, existing")
    create_collection_if_missing: bool = Field(default=True, description="Auto-create collection if it doesn't exist")

class IngestDocumentResponse(BaseModel):
    """Response model for document ingestion"""
    success: bool
    document_id: str
    collection_name: str
    tenant_id: str
    chunks_created: int
    chunks_inserted: int
    processing_time_ms: float
    stages: Dict[str, Any]

class CreateCollectionRequest(BaseModel):
    """Request model for creating a new collection"""
    collection_name: str = Field(..., description="Name of the collection to create")
    dimension: int = Field(default_factory=lambda: get_embedding_dimension(), description="Vector dimension (from model registry)")
    description: Optional[str] = Field(None, description="Collection description")

class DeleteCollectionRequest(BaseModel):
    """Request model for deleting a collection"""
    collection_name: str = Field(..., description="Name of the collection to delete")

class UpdateDocumentRequest(BaseModel):
    """Request model for updating (delete + re-insert) a document"""
    text: str = Field(..., description="Updated document text content", min_length=50)
    collection_name: str = Field(..., description="Target collection name")
    tenant_id: str = Field(default="default", description="Tenant ID for multi-tenancy")
    chunking_mode: str = Field(default="comprehensive", description="Chunking mode")
    metadata_mode: str = Field(default="basic", description="Metadata extraction mode")

class DeleteDocumentRequest(BaseModel):
    """Request model for deleting a document"""
    document_id: str = Field(..., description="Document ID to delete")
    collection_name: str = Field(..., description="Target collection name")

# ============================================================================
# Helper Functions
# ============================================================================
def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """
    Count tokens in text using tiktoken

    Args:
        text: Text to tokenize
        encoding_name: Encoding to use (default: cl100k_base for GPT-4/3.5)

    Returns:
        Token count
    """
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Token counting failed, using char/4 estimate: {e}")
        # Fallback: rough estimate (1 token ≈ 4 characters)
        return len(text) // 4

import random
import asyncio

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
async def call_chunking_service(request: IngestDocumentRequest) -> Dict[str, Any]:
    """
    Call internal chunking service with full parameter pass-through

    This passes all chunking, metadata, embedding, and storage parameters
    to the Chunking Orchestrator Service which coordinates the full pipeline.
    """
    try:
        # Build metadata config
        metadata_config = {
            "keywords_count": str(request.keywords_count),
            "topics_count": str(request.topics_count),
            "questions_count": str(request.questions_count),
            "summary_length": request.summary_length
        }

        # Build full orchestration request
        orchestration_request = {
            # Text and document ID
            "text": request.text,
            "document_id": request.document_id,

            # Chunking configuration
            "method": request.chunking_method,
            "max_chunk_size": request.max_chunk_size,
            "chunk_overlap": request.chunk_overlap,
            "separators": request.separators,
            "markdown_headers": request.markdown_headers,
            "encoding": request.encoding,

            # Metadata generation
            "generate_metadata": request.generate_metadata,
            "metadata_config": metadata_config,

            # Embeddings generation
            "generate_embeddings": request.generate_embeddings,

            # Storage configuration
            # Translate user-facing storage_mode to chunking service enum values
            "storage_mode": "new" if request.storage_mode == "new_collection" else request.storage_mode,
            "collection_name": request.collection_name,
            "tenant_id": request.tenant_id
        }

        response = await http_client.post(
            CHUNKING_URL,
            json=orchestration_request,
            timeout=120.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Chunking service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Chunking service error: {str(e)}"
        )

async def call_metadata_service_batch(
    chunks: List[Dict[str, Any]],
    extraction_mode: str = "basic",
    skip_cache: bool = False
) -> Dict[str, Any]:
    """Call internal metadata service (batch) with retry logic and automatic batching

    Filters out chunks shorter than 10 characters before sending to metadata service.
    Metadata service has MAX_BATCH_SIZE=50 limit. For large documents (200+ chunks),
    we split into batches of 40 to stay under the limit safely.
    """
    # Filter out chunks that are too short for metadata extraction (< 10 chars)
    MIN_CHUNK_LENGTH = 10
    valid_chunks = [
        (i, chunk) for i, chunk in enumerate(chunks)
        if len(chunk.get("text", "")) >= MIN_CHUNK_LENGTH
    ]

    if not valid_chunks:
        # All chunks too short - return empty result
        logger.warning(f"All {len(chunks)} chunks too short (<{MIN_CHUNK_LENGTH} chars), skipping metadata extraction")
        return {
            "results": [{}] * len(chunks),  # Empty metadata for all chunks
            "total_chunks": len(chunks),
            "successful": 0,
            "failed": len(chunks),
            "total_processing_time_ms": 0,
            "api_version": "1.0.0"
        }

    skipped_count = len(chunks) - len(valid_chunks)
    if skipped_count > 0:
        logger.info(f"Skipping {skipped_count} short chunks (<{MIN_CHUNK_LENGTH} chars), processing {len(valid_chunks)}")

    # Batch size limit (stay under metadata service MAX_BATCH_SIZE=50)
    METADATA_BATCH_SIZE = 40

    # If small enough, send in single request
    if len(valid_chunks) <= METADATA_BATCH_SIZE:
        async def _call():
            chunk_requests = [
                {
                    "text": chunk["text"],
                    "chunk_id": chunk.get("chunk_id", f"chunk_{i}"),
                    "extraction_mode": extraction_mode,
                    "model": get_metadata_enum_for_model(METADATA_MODEL),
                    "skip_cache": skip_cache
                }
                for i, chunk in valid_chunks
            ]

            response = await http_client.post(
                f"{METADATA_URL}/batch",
                json={"chunks": chunk_requests},
                timeout=120.0
            )
            response.raise_for_status()
            return response.json()

        try:
            result = await retry_with_exponential_backoff(_call)

            # Re-insert empty metadata for skipped chunks at their original positions
            if skipped_count > 0:
                full_results = []
                result_idx = 0
                for i in range(len(chunks)):
                    # Check if this index was in valid_chunks
                    if any(idx == i for idx, _ in valid_chunks):
                        full_results.append(result["results"][result_idx])
                        result_idx += 1
                    else:
                        # Empty metadata for skipped chunk
                        full_results.append({})

                result["results"] = full_results
                result["total_chunks"] = len(chunks)
                result["failed"] = result.get("failed", 0) + skipped_count

            return result
        except httpx.HTTPError as e:
            logger.error(f"Metadata service error after retries: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Metadata service error: {str(e)}"
            )

    # Large document: split into batches and process in parallel
    logger.info(f"Large document ({len(valid_chunks)} chunks) - batching metadata extraction into groups of {METADATA_BATCH_SIZE}")

    batches = []
    for i in range(0, len(valid_chunks), METADATA_BATCH_SIZE):
        batch = valid_chunks[i:i + METADATA_BATCH_SIZE]
        batches.append(batch)

    logger.info(f"Created {len(batches)} batches for metadata extraction")

    # Process batches in parallel
    async def _call_batch(batch_chunks: List[tuple]) -> Dict[str, Any]:
        chunk_requests = [
            {
                "text": chunk["text"],
                "chunk_id": chunk.get("chunk_id", f"chunk_{i}"),
                "extraction_mode": extraction_mode,
                "model": get_metadata_enum_for_model(METADATA_MODEL),
                "skip_cache": skip_cache
            }
            for i, chunk in batch_chunks
        ]

        response = await http_client.post(
            f"{METADATA_URL}/batch",
            json={"chunks": chunk_requests},
            timeout=120.0
        )
        response.raise_for_status()
        return response.json()

    try:
        # Process all batches in parallel with retry logic
        import asyncio
        batch_tasks = [
            retry_with_exponential_backoff(_call_batch, batch)
            for batch in batches
        ]
        batch_results = await asyncio.gather(*batch_tasks)

        # Combine results from all batches
        all_metadata = []
        total_successful = 0
        total_failed = 0
        total_time_ms = 0

        for result in batch_results:
            all_metadata.extend(result.get("results", []))
            total_successful += result.get("successful", 0)
            total_failed += result.get("failed", 0)
            total_time_ms += result.get("total_processing_time_ms", 0)

        # Re-insert empty metadata for skipped chunks at their original positions
        if skipped_count > 0:
            full_results = []
            result_idx = 0
            for i in range(len(chunks)):
                # Check if this index was in valid_chunks
                if any(idx == i for idx, _ in valid_chunks):
                    full_results.append(all_metadata[result_idx])
                    result_idx += 1
                else:
                    # Empty metadata for skipped chunk
                    full_results.append({})

            all_metadata = full_results
            total_failed += skipped_count

        # Return combined result in same format as single request
        return {
            "results": all_metadata,
            "total_chunks": len(chunks),
            "successful": total_successful,
            "failed": total_failed,
            "total_processing_time_ms": total_time_ms,
            "api_version": "1.0.0"
        }
    except httpx.HTTPError as e:
        logger.error(f"Metadata service error after retries: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Metadata service error: {str(e)}"
        )

async def call_embeddings_service(
    texts: List[str],
    model: str = None
) -> Dict[str, Any]:
    """Call internal embeddings service with retry logic and automatic batching

    Args:
        texts: List of texts to embed
        model: Embedding model to use (if None, uses DEFAULT_EMBEDDING_MODEL)

    Embeddings service has MAX_BATCH_SIZE=128 limit. For large documents (200+ chunks),
    we split into batches of 100 to stay under the limit safely.
    """
    # Use default if not specified
    if model is None:
        model = DEFAULT_EMBEDDING_MODEL

    # Batch size limit (stay under embeddings service MAX_BATCH_SIZE=128)
    EMBEDDINGS_BATCH_SIZE = 100

    # If small enough, send in single request
    if len(texts) <= EMBEDDINGS_BATCH_SIZE:
        async def _call():
            response = await http_client.post(
                EMBEDDINGS_URL,
                json={
                    "input": texts,
                    "model": model,
                    "normalize": True
                },
                timeout=120.0
            )
            response.raise_for_status()
            return response.json()

        try:
            return await retry_with_exponential_backoff(_call)
        except httpx.HTTPError as e:
            logger.error(f"Embeddings service error after retries: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Embeddings service error: {str(e)}"
            )

    # Large document: split into batches and process in parallel
    logger.info(f"Large document ({len(texts)} chunks) - batching embeddings into groups of {EMBEDDINGS_BATCH_SIZE}")

    batches = []
    for i in range(0, len(texts), EMBEDDINGS_BATCH_SIZE):
        batch = texts[i:i + EMBEDDINGS_BATCH_SIZE]
        batches.append(batch)

    logger.info(f"Created {len(batches)} batches for embeddings generation")

    # Process batches in parallel
    async def _call_batch(batch_texts: List[str]) -> Dict[str, Any]:
        response = await http_client.post(
            EMBEDDINGS_URL,
            json={
                "input": batch_texts,
                "model": model,
                "normalize": True
            },
            timeout=120.0
        )
        response.raise_for_status()
        return response.json()

    try:
        # Process all batches in parallel with retry logic
        import asyncio
        batch_tasks = [
            retry_with_exponential_backoff(_call_batch, batch)
            for batch in batches
        ]
        batch_results = await asyncio.gather(*batch_tasks)

        # Combine results from all batches
        all_embeddings = []
        for result in batch_results:
            all_embeddings.extend(result.get("data", []))

        # Return combined result in same format as single request
        return {
            "data": all_embeddings,
            "model": model,
            "usage": {
                "prompt_tokens": sum(r.get("usage", {}).get("prompt_tokens", 0) for r in batch_results),
                "total_tokens": sum(r.get("usage", {}).get("total_tokens", 0) for r in batch_results)
            }
        }
    except httpx.HTTPError as e:
        logger.error(f"Embeddings service error after retries: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Embeddings service error: {str(e)}"
        )

async def call_storage_service_insert(
    collection_name: str,
    chunks: List[Dict[str, Any]],
    tenant_id: str = "default",
    create_collection: bool = True
) -> Dict[str, Any]:
    """Call internal storage service for insertion"""
    try:
        response = await http_client.post(
            f"{STORAGE_URL}/insert",
            json={
                "collection_name": collection_name,
                "chunks": chunks,
                "tenant_id": tenant_id,
                "create_collection": create_collection
            },
            timeout=120.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Storage service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage service error: {str(e)}"
        )

async def call_storage_service_create_collection(
    collection_name: str,
    dimension: int = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Call internal storage service to create collection

    Args:
        collection_name: Name of collection to create
        dimension: Vector dimension (if None, uses model registry default)
        description: Optional collection description
    """
    # Use model registry default if not specified
    if dimension is None:
        dimension = get_embedding_dimension()
    try:
        response = await http_client.post(
            f"{STORAGE_URL}/collections",
            json={
                "name": collection_name,
                "dimension": dimension,
                "description": description or f"Collection created on {datetime.now().isoformat()}"
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Storage service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage service error: {str(e)}"
        )

async def call_storage_service_delete_collection(
    collection_name: str
) -> Dict[str, Any]:
    """Call internal storage service to delete collection"""
    try:
        response = await http_client.delete(
            f"{STORAGE_URL}/collections/{collection_name}",
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Storage service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage service error: {str(e)}"
        )

async def call_storage_service_delete_document(
    collection_name: str,
    document_id: str
) -> Dict[str, Any]:
    """Call internal storage service to delete document by filter"""
    try:
        # Delete by document_id field filter
        response = await http_client.post(
            f"{STORAGE_URL}/delete",
            json={
                "collection_name": collection_name,
                "filter": f'document_id == "{document_id}"'
            },
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Storage service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Storage service error: {str(e)}"
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
            "ingest": "POST /v1/ingest",
            "create_collection": "POST /v1/collections",
            "delete_collection": "DELETE /v1/collections/{name}",
            "update_document": "PUT /v1/documents/{doc_id}",
            "delete_document": "DELETE /v1/documents/{doc_id}"
        }
    }

@app.get("/health")
async def health_check():
    """
    Aggregated health check endpoint (Enterprise Pattern)

    Checks all downstream microservices and returns comprehensive status.
    This follows the API Gateway Health Aggregation pattern used by Netflix, Uber, etc.
    """
    start_time = time.time()

    # Initialize service health status
    services = {
        "chunking": {"status": "unknown", "url": CHUNKING_URL.replace("/v1/orchestrate", "/health")},
        "metadata": {"status": "unknown", "url": METADATA_URL.replace("/v1/metadata", "/health")},
        "embeddings": {"status": "unknown", "url": EMBEDDINGS_URL.replace("/v1/embeddings", "/health")},
        "storage": {"status": "unknown", "url": STORAGE_URL.replace("/v1", "") + "/health"},
        "llm_gateway": {"status": "unknown", "url": LLM_GATEWAY_URL.replace("/v1/chat/completions", "/health")}  # Fixed
    }

    # Check each service (async, with timeout)
    async def check_service(name: str, url: str) -> dict:
        try:
            response = await http_client.get(url, timeout=2.0)  # OPTIMIZED: 2s timeout (was 3s)
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "version": data.get("version", "unknown"),
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
                "error": "Health check timeout (2s)",  # Updated error message
                "response_time_ms": 2000  # Updated to 2s
            }
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e),
                "response_time_ms": round((time.time() - start_time) * 1000, 2)
            }

    # Check all services in parallel
    import asyncio
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

@app.post("/v1/ingest", response_model=IngestDocumentResponse)
async def ingest_document(request: IngestDocumentRequest):
    """
    Ingest a document into the vector database

    Pipeline: Document → Chunking → Metadata → Embeddings → Storage

    Rate Limited: Max {MAX_CONCURRENT_INGESTIONS} concurrent ingestions
    """
    # Rate limiting: acquire semaphore (wait if limit reached)
    async with ingestion_semaphore:
        logger.info(f"Ingesting document: {request.document_id} into collection: {request.collection_name}")

        pipeline_start = time.time()
        stages = {}

        try:
            # NEW SIMPLIFIED PIPELINE:
            # Chunking Orchestrator now handles the FULL pipeline internally!
            # It orchestrates: Chunking → Metadata → Embeddings → Storage
            # We just pass all parameters and it returns the complete result

            logger.info(f"Delegating to Chunking Orchestrator with parameters:")
            logger.info(f"  - Chunking: method={request.chunking_method}, max_chunk_size={request.max_chunk_size}, chunk_overlap={request.chunk_overlap}")
            logger.info(f"  - Metadata: generate={request.generate_metadata}, keywords={request.keywords_count}, topics={request.topics_count}")
            logger.info(f"  - Embeddings: generate={request.generate_embeddings}, model={request.embedding_model}")
            logger.info(f"  - Storage: mode={request.storage_mode}, collection={request.collection_name}")

            orchestration_result = await call_chunking_service(request)

            # Extract results from orchestration
            chunks_created = orchestration_result.get("total_chunks", 0)
            chunks_inserted = orchestration_result.get("collection_name") and chunks_created or 0  # Assume all chunks inserted if stored

            # Security: Validate chunks count
            if chunks_created > MAX_CHUNKS_PER_DOCUMENT:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Document produced {chunks_created} chunks, exceeding limit of {MAX_CHUNKS_PER_DOCUMENT}"
                )

            # Extract timing information from orchestration response
            stages = {
                "chunking": {
                    "time_ms": orchestration_result.get("chunking_time_ms", 0),
                    "chunks_created": chunks_created
                },
                "metadata": {
                    "time_ms": orchestration_result.get("metadata_time_ms", 0),
                    "generated": orchestration_result.get("metadata_generated", False)
                },
                "embeddings": {
                    "time_ms": orchestration_result.get("embeddings_time_ms", 0),
                    "generated": orchestration_result.get("embeddings_generated", False),
                    "model": request.embedding_model
                },
                "storage": {
                    "time_ms": orchestration_result.get("storage_time_ms", 0),
                    "stored": orchestration_result.get("stored_in_milvus", False),
                    "collection_name": orchestration_result.get("collection_name")
                }
            }

            logger.info(f"Pipeline complete: {chunks_created} chunks created, {chunks_inserted} chunks stored")

            # Return response directly - orchestration service handled everything
            pipeline_time = (time.time() - pipeline_start) * 1000
            return IngestDocumentResponse(
                success=True,
                document_id=request.document_id,
                collection_name=request.collection_name,
                tenant_id=request.tenant_id,
                chunks_created=chunks_created,
                chunks_inserted=chunks_inserted,
                processing_time_ms=pipeline_time,
                stages=stages
            )

            # OLD CODE BELOW (UNREACHABLE - kept for reference, will be removed in next version)
            # Stage 2 & 3: Metadata Extraction + Embeddings Generation (PARALLEL)
            # Run both services concurrently to save time (5-10s improvement for 50 chunks)
            parallel_start = time.time()
            chunk_texts = [chunk["text"] for chunk in chunks]

            import asyncio
            metadata_task = call_metadata_service_batch(
                chunks=chunks,
                extraction_mode=request.metadata_mode,
                skip_cache=request.skip_cache
            )
            embeddings_task = call_embeddings_service(texts=chunk_texts, model=request.embedding_model)

            # Execute both tasks in parallel
            metadata_result, embeddings_result = await asyncio.gather(
                metadata_task,
                embeddings_task,
                return_exceptions=False  # Propagate exceptions
            )

            parallel_time = (time.time() - parallel_start) * 1000

            # Process metadata results
            metadata_results = metadata_result.get("results", [])
            stages["metadata"] = {
                "time_ms": parallel_time,  # Actual time includes parallel execution
                "successful": metadata_result.get("successful", 0),
                "failed": metadata_result.get("failed", 0),
                "mode": request.metadata_mode,
                "parallel": True
            }
            logger.info(f"Metadata extraction complete: {metadata_result.get('successful', 0)}/{chunks_created} successful (parallel)")

            # Process embeddings results
            embeddings_list = embeddings_result.get("data", [])
            stages["embeddings"] = {
                "time_ms": parallel_time,  # Same parallel execution time
                "count": len(embeddings_list),
                "model": embeddings_result.get("model", DEFAULT_EMBEDDING_MODEL),
                "dimension": len(embeddings_list[0]['dense_embedding']) if embeddings_list else 0,
                "parallel": True
            }
            logger.info(f"Embeddings generation complete: {len(embeddings_list)} vectors (parallel)")
            logger.info(f"Parallel execution saved ~{max(0, parallel_time/2 - parallel_time):.0f}ms")

            # Stage 4: Storage Insertion
            storage_start = time.time()

            # Prepare chunks for storage
            storage_chunks = []
            skipped_chunks = 0

            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings_list)):
                # Get metadata if available (by index if metadata_results matches chunks length)
                metadata = None
                if i < len(metadata_results):
                    metadata = metadata_results[i]

                # Skip ONLY if metadata explicitly indicates fatal error
                # (but allow empty/failed metadata - just use empty strings)
                if metadata and isinstance(metadata, dict):
                    summary = metadata.get("summary", "")
                    # Only skip if there's a truly fatal error that would corrupt data
                    if "FATAL" in summary.upper():
                        skipped_chunks += 1
                        logger.warning(f"Skipping chunk {i} due to fatal metadata error: {summary[:100]}")
                        continue

                timestamp_now = datetime.now().isoformat()
                chunk_data = {
                    # Core fields (9)
                    "id": f"{request.document_id}_chunk_{i}",
                    "document_id": request.document_id,
                    "chunk_index": i,
                    "text": chunk["text"],
                    "tenant_id": request.tenant_id,
                    "created_at": timestamp_now,
                    "updated_at": timestamp_now,
                    "char_count": len(chunk["text"]),
                    "token_count": count_tokens(chunk["text"]),  # Actual token count

                    # Vector field (1)
                    "dense_vector": embedding["dense_embedding"],

                    # Base metadata (4) - use empty strings if metadata failed
                    "keywords": metadata.get("keywords", "") if (metadata and isinstance(metadata, dict)) else "",
                    "topics": metadata.get("topics", "") if (metadata and isinstance(metadata, dict)) else "",
                    "questions": metadata.get("questions", "") if (metadata and isinstance(metadata, dict)) else "",
                    "summary": metadata.get("summary", "") if (metadata and isinstance(metadata, dict)) else ""
                }
                storage_chunks.append(chunk_data)

            # Debug: Log what we're about to send
            logger.info(f"Prepared {len(storage_chunks)} chunks for storage (skipped: {skipped_chunks})")
            if len(storage_chunks) == 0:
                logger.error("CRITICAL: storage_chunks is EMPTY! Cannot insert into storage.")
                logger.error(f"  chunks count: {len(chunks)}")
                logger.error(f"  metadata_results count: {len(metadata_results)}")
                logger.error(f"  embeddings_list count: {len(embeddings_list)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"All chunks were skipped during preparation. Check metadata extraction."
                )

            storage_result = await call_storage_service_insert(
                collection_name=request.collection_name,
                chunks=storage_chunks,
                tenant_id=request.tenant_id,
                create_collection=True
            )

            chunks_inserted = storage_result.get("inserted_count", 0)
            stages["storage"] = {
                "time_ms": (time.time() - storage_start) * 1000,
                "inserted_count": chunks_inserted,
                "skipped_chunks": skipped_chunks,
                "collection_name": request.collection_name
            }
            logger.info(f"Storage insertion complete: {chunks_inserted} chunks inserted")

            # Calculate total processing time
            processing_time_ms = (time.time() - pipeline_start) * 1000

            return IngestDocumentResponse(
                success=True,
                document_id=request.document_id,
                collection_name=request.collection_name,
                tenant_id=request.tenant_id,
                chunks_created=chunks_created,
                chunks_inserted=chunks_inserted,
                processing_time_ms=processing_time_ms,
                stages=stages
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Pipeline processing error: {str(e)}"
            )

@app.post("/v1/collections")
async def create_collection(request: CreateCollectionRequest):
    """Create a new collection in the vector database"""
    logger.info(f"Creating collection: {request.collection_name}")

    try:
        result = await call_storage_service_create_collection(
            collection_name=request.collection_name,
            dimension=request.dimension,
            description=request.description
        )
        return result
    except HTTPException:
        raise

@app.delete("/v1/collections/{collection_name}")
async def delete_collection(collection_name: str):
    """Delete a collection from the vector database"""
    logger.info(f"Deleting collection: {collection_name}")

    try:
        result = await call_storage_service_delete_collection(collection_name)
        return result
    except HTTPException:
        raise

@app.put("/v1/documents/{document_id}")
async def update_document(document_id: str, request: UpdateDocumentRequest):
    """
    Update a document (delete old + insert new)

    This is a simple update strategy: delete all chunks with the same document_id,
    then re-ingest the updated document.
    """
    logger.info(f"Updating document: {document_id} in collection: {request.collection_name}")

    try:
        # Step 1: Delete existing document
        delete_result = await call_storage_service_delete_document(
            collection_name=request.collection_name,
            document_id=document_id
        )
        logger.info(f"Deleted {delete_result.get('deleted_count', 0)} old chunks")

        # Step 2: Re-ingest updated document
        ingest_request = IngestDocumentRequest(
            text=request.text,
            document_id=document_id,
            collection_name=request.collection_name,
            tenant_id=request.tenant_id,
            chunking_mode=request.chunking_mode,
            metadata_mode=request.metadata_mode,
            skip_cache=True  # Force fresh processing for updated content
        )

        ingest_result = await ingest_document(ingest_request)

        return {
            "success": True,
            "operation": "update",
            "document_id": document_id,
            "deleted_chunks": delete_result.get("deleted_count", 0),
            "inserted_chunks": ingest_result.chunks_inserted,
            "processing_time_ms": ingest_result.processing_time_ms
        }

    except HTTPException:
        raise

@app.delete("/v1/documents/{document_id}")
async def delete_document(document_id: str, collection_name: str):
    """Delete a document and all its chunks from a collection"""
    logger.info(f"Deleting document: {document_id} from collection: {collection_name}")

    try:
        result = await call_storage_service_delete_document(
            collection_name=collection_name,
            document_id=document_id
        )
        return result
    except HTTPException:
        raise

# ============================================================================
# Startup/Shutdown Events (Now handled by lifespan context manager above)
# ============================================================================
# REMOVED: @app.on_event("startup") - Replaced with lifespan context manager
# REMOVED: @app.on_event("shutdown") - Replaced with lifespan context manager

# ============================================================================
# Run Server
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info"
    )
