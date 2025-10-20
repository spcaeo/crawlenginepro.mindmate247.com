#!/usr/bin/env python3
"""
Chunking Orchestrator v5.0.0
Simplified RAG Pipeline - Delegates to Metadata v3 and Milvus Storage v1
https://chunking.mindmate247.com/

KEY CHANGES FROM v4.0.0:
- Calls metadata v3.0.0 (45 fields) instead of v2.0.0 (4 fields)
- Calls Milvus Storage v1.0.0 API instead of direct pymilvus
- NO pymilvus imports - pure orchestration only
- Simpler, cleaner code - focused on coordination
"""

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import time
from datetime import datetime, timezone
import tiktoken
import httpx
import asyncio
from contextlib import asynccontextmanager
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    TokenTextSplitter
)
import uuid
from datetime import datetime
import uvicorn

# Import configurations and models
from config import *
from models import *

# Import shared model registry for embedding model selection
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared"))
from model_registry import DEFAULT_EMBEDDING_MODEL

# ============================================================================
# Service Initialization
# ============================================================================

START_TIME = time.time()
TOTAL_REQUESTS = 0

# HTTP client for connection pooling
http_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global http_client

    # Startup
    print("=" * 80)
    print(f"{SERVICE_NAME} v{API_VERSION} - Starting")
    print("=" * 80)
    print(f"Connection pooling: Size={CONNECTION_POOL_SIZE}, Max={CONNECTION_POOL_MAX}")
    print(f"Max workers: {MAX_WORKERS}")
    print("=" * 80)
    print("SIMPLIFIED ARCHITECTURE:")
    print("  → Chunking v5.0.0 (This service)")
    print("  → Metadata v3.0.0 (port 8062) - 45 fields")
    print("  → Embeddings v3.0.1 (port 8063) - Hybrid vectors")
    print("  → Milvus Storage v1.0.0 (port 8064) - CRUD API")
    print("=" * 80)

    # Create persistent HTTP client with connection pooling
    limits = httpx.Limits(
        max_keepalive_connections=CONNECTION_POOL_SIZE,
        max_connections=CONNECTION_POOL_MAX
    )
    timeout = httpx.Timeout(CONNECTION_TIMEOUT, connect=10.0)
    http_client = httpx.AsyncClient(limits=limits, timeout=timeout)

    yield

    # Shutdown
    await http_client.aclose()
    print(f"{SERVICE_NAME} shut down")

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
            "detail": f"Direct access forbidden. Use gateway: https://chunking.mindmate247.com",
            "api_version": API_VERSION
        }
    )

# ============================================================================
# Permission Management (INTERNAL_MODE only - no external auth)
# ============================================================================
# REMOVED: get_consumer_info() - Not needed in INTERNAL_MODE
# REMOVED: validate_permission() - Not needed in INTERNAL_MODE

# ============================================================================
# Helper Functions
# ============================================================================

def safe_float(value: Any) -> Optional[float]:
    """Safely convert value to float, returning None if invalid"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None

def safe_int(value: Any) -> Optional[int]:
    """Safely convert value to int, returning None if invalid"""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None

def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens using tiktoken"""
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception:
        return len(text) // 4

def is_valid_chunk(chunk_text: str) -> bool:
    """Check if chunk contains meaningful content"""
    # Strip whitespace
    stripped = chunk_text.strip()
    
    # Empty or whitespace-only
    if not stripped:
        return False
    
    # Just separator characters (---, ***, ___, etc.)
    if all(c in '-*_ \t\n' for c in stripped):
        return False
    
    # Keep headers (start with #)
    if stripped.startswith('#'):
        return True
    
    # Keep if has at least 5 alphanumeric characters
    alphanum_count = sum(1 for c in stripped if c.isalnum())
    if alphanum_count >= 5:
        return True
    
    return False

def perform_chunking(text: str, config: OrchestrationRequest) -> List[str]:
    """Chunk text using specified method"""
    if config.method == ChunkingMethod.recursive:
        # Markdown-aware separators (non-regex version for compatibility)
        # Priority: Headers > Horizontal rules > Paragraphs > Lines > Words > Chars
        separators = config.separators or [
            '\n### ',    # H3 headers
            '\n## ',     # H2 headers
            '\n# ',      # H1 headers
            '\n---\n',   # Horizontal rule (---) - Fixes section mixing!
            '\n***\n',   # Horizontal rule (***)
            '\n___\n',   # Horizontal rule (___)
            '\n\n',      # Double newline (paragraphs)
            '\n',        # Single newline
            ' ',         # Space
            ''           # Empty (character-by-character)
        ]
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.max_chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=separators
        )

    elif config.method == ChunkingMethod.markdown:
        headers = config.markdown_headers or ["#", "##", "###"]
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[(h, h) for h in headers]
        )

    elif config.method == ChunkingMethod.token:
        splitter = TokenTextSplitter(
            chunk_size=config.max_chunk_size,
            chunk_overlap=config.chunk_overlap,
            encoding_name=config.encoding
        )

    # Split text
    if config.method == ChunkingMethod.markdown:
        docs = splitter.split_text(text)
        chunks = [doc.page_content if hasattr(doc, 'page_content') else str(doc) for doc in docs]
    else:
        chunks = splitter.split_text(text)

    # Filter out invalid chunks (separators, empty, etc.)
    chunks = [c for c in chunks if is_valid_chunk(c)]
    return chunks

async def generate_embeddings_batch(chunks: List[str], api_key: str) -> List[Dict[str, Any]]:
    """
    Generate hybrid embeddings (dense + sparse) for all chunks using embeddings v3.0.0
    Returns list of dicts with 'dense_embedding' and 'sparse_embedding' fields
    """
    try:
        # Build headers - only include apikey if NOT in internal mode
        headers = {"Content-Type": "application/json"}
        if not INTERNAL_MODE:
            headers["apikey"] = api_key

        # Call embeddings v3 endpoint for hybrid vectors
        response = await http_client.post(
            EMBEDDINGS_SERVICE_URL,  # Points to http://localhost:8016/v3/embeddings
            headers=headers,
            json={
                "input": chunks,
                "model": DEFAULT_EMBEDDING_MODEL,  # Use shared registry instead of hardcoded value
                "return_dense": True,
                "return_sparse": True
            }
        )

        if response.status_code != 200:
            raise Exception(f"Embeddings service returned {response.status_code}: {response.text}")

        result = response.json()
        # Sort by index to maintain order
        embeddings_data = sorted(result['data'], key=lambda x: x['index'])

        # Extract model used from response
        embedding_model_used = result.get('model', DEFAULT_EMBEDDING_MODEL)

        # Return tuple: (embeddings list, model used)
        embeddings_list = [{
            'dense_embedding': item['dense_embedding'],
            'sparse_embedding': item.get('sparse_embedding', {})
        } for item in embeddings_data]

        return (embeddings_list, embedding_model_used)

    except Exception as e:
        print(f"⚠️  Embeddings generation failed: {e}")
        return (None, None)

async def generate_metadata_for_chunk(chunk_text: str, chunk_id: str, config: MetadataConfig, api_key: str) -> Optional[Dict]:
    """
    Generate enriched metadata for a single chunk using metadata v3.0.0
    Returns 45 fields instead of 4!
    """
    try:
        # Build headers - only include apikey if NOT in internal mode
        headers = {"Content-Type": "application/json"}
        if not INTERNAL_MODE:
            headers["apikey"] = api_key

        response = await http_client.post(
            METADATA_SERVICE_URL,  # Now points to v3 endpoint!
            headers=headers,
            json={
                "text": chunk_text,
                "chunk_id": chunk_id,
                "keywords_count": config.keywords_count,
                "topics_count": config.topics_count,
                "questions_count": config.questions_count,
                "summary_length": config.summary_length
            },
            timeout=30.0  # Longer timeout for enriched extraction
        )

        if response.status_code == 200:
            result = response.json()
            # DEBUG: Print FULL response keys and URL called
            print(f"DEBUG {chunk_id}: URL={METADATA_SERVICE_URL}")
            print(f"DEBUG {chunk_id}: Response keys: {list(result.keys())}")
            print(f"DEBUG {chunk_id}: semantic_keywords={result.get('semantic_keywords', 'KEY_MISSING')}")
            return result
        else:
            print(f"⚠️  Metadata service error for {chunk_id}: {response.status_code} URL={METADATA_SERVICE_URL} INTERNAL_MODE={INTERNAL_MODE}")
            return None

    except Exception as e:
        print(f"⚠️  Metadata generation error for {chunk_id}: {e}")
        return None

async def generate_metadata_parallel(chunks: List[str], config: MetadataConfig, api_key: str) -> List[Optional[Dict]]:
    """Generate metadata for all chunks in parallel"""

    # Filter: Skip chunks shorter than 50 chars (metadata service minimum)
    MIN_METADATA_LENGTH = 50

    tasks = []
    skip_indices = []

    for i, chunk_text in enumerate(chunks):
        if len(chunk_text.strip()) < MIN_METADATA_LENGTH:
            # Too short for metadata extraction - skip API call
            tasks.append(None)
            skip_indices.append(i)
        else:
            tasks.append(generate_metadata_for_chunk(chunk_text, f"chunk_{i:04d}", config, api_key))

    if skip_indices:
        print(f"  ⏭️  Skipped {len(skip_indices)} chunks (< {MIN_METADATA_LENGTH} chars): {skip_indices}")

    # Execute all valid tasks in parallel (no concurrency limit - testing showed this is fastest)
    valid_tasks = [t for t in tasks if t is not None]
    if valid_tasks:
        results = await asyncio.gather(*valid_tasks, return_exceptions=True)
    else:
        results = []

    # Merge results back with None for skipped chunks
    metadata_results = []
    metadata_model_used = None  # Track model used
    result_idx = 0
    for i, task in enumerate(tasks):
        if task is None:
            metadata_results.append(None)
        else:
            result = results[result_idx]
            if isinstance(result, Exception):
                print(f"⚠️  Error processing chunk {i}: {result}")
                metadata_results.append(None)
            else:
                # Extract model_used from first successful result
                if metadata_model_used is None and result and isinstance(result, dict):
                    metadata_model_used = result.get('model_used')
                metadata_results.append(result)
            result_idx += 1

    # Return tuple: (metadata list, model used)
    return (list(metadata_results), metadata_model_used)

async def store_in_milvus_storage(
    chunks_data: List[Dict],
    collection_name: str,
    tenant_id: str,
    api_key: str,
    source_document: str = None,
    metadata_model_used: str = None,
    embedding_model_used: str = None
) -> Dict:
    """
    Store chunks in Milvus via Storage Service v1.0.0 API
    NO direct pymilvus - delegates to storage service!
    """
    try:
        # Build headers - only include apikey if NOT in internal mode
        headers = {"Content-Type": "application/json"}
        if not INTERNAL_MODE:
            headers["apikey"] = api_key

        # Call Milvus Storage Service v1.0.0 with model info
        payload = {
            "collection_name": collection_name,
            "chunks": chunks_data,
            "create_collection": True  # Auto-create if doesn't exist
        }

        # Add optional model information
        if source_document:
            payload["source_document"] = source_document
        if metadata_model_used:
            payload["metadata_model_used"] = metadata_model_used
        if embedding_model_used:
            payload["embedding_model_used"] = embedding_model_used

        response = await http_client.post(
            f"{MILVUS_STORAGE_SERVICE_URL}/insert",
            headers=headers,
            json=payload,
            timeout=60.0
        )

        if response.status_code != 200:
            raise Exception(f"Storage service returned {response.status_code}: {response.text}")

        return response.json()

    except Exception as e:
        print(f"⚠️  Storage service error: {e}")
        raise HTTPException(status_code=500, detail=f"Milvus storage failed: {str(e)}")

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check with service connectivity"""
    services = {
        "embeddings": False,
        "metadata": False,
        "milvus_storage": False
    }

    # Check embeddings service (OPTIMIZED: 2s timeout instead of 5s)
    try:
        resp = await http_client.get(EMBEDDINGS_SERVICE_URL.replace("/embeddings", "").replace("/v2", "") + "/health", timeout=2)
        services["embeddings"] = resp.status_code == 200
    except Exception:
        pass

    # Check metadata service v3 (OPTIMIZED: 2s timeout instead of 5s)
    try:
        resp = await http_client.get(METADATA_SERVICE_URL.replace("/metadata", "").replace("/v3", "") + "/health", timeout=2)
        services["metadata"] = resp.status_code == 200
    except Exception:
        pass

    # Check Milvus Storage service (OPTIMIZED: 2s timeout instead of 5s)
    try:
        resp = await http_client.get(f"{MILVUS_STORAGE_SERVICE_URL}/health", timeout=2)
        services["milvus_storage"] = resp.status_code == 200
    except Exception:
        pass

    uptime = time.time() - START_TIME

    return HealthResponse(
        status="healthy",
        version=API_VERSION,
        service=SERVICE_NAME,
        services=services,
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
        endpoints=["/health", "/version", "/v5/orchestrate"],
        supported_methods=["recursive", "markdown", "token"],
        permission_system={
            "basic": ["chunking"],
            "enhanced": ["chunking", "embeddings", "metadata"],
            "enterprise": ["chunking", "embeddings", "metadata", "milvus"]
        },
        metadata_version="3.0.0",
        storage_version="1.0.0"
    )

@app.post("/v1/orchestrate", response_model=OrchestrationResponse)
async def orchestrate_pipeline(
    request: OrchestrationRequest,
    apikey: Optional[str] = Header(None)
):
    """
    Complete RAG Pipeline Orchestration v5.0.0
    Simplified orchestration - delegates to specialized services

    Changes from v4.0.0:
    - Calls metadata v3.0.0 (45 fields) instead of v2.0.0 (4 fields)
    - Calls Milvus Storage v1.0.0 API instead of direct pymilvus
    - No schema management, no Milvus dependencies
    - Pure orchestration logic only

    Permission Requirements:
    - chunking: Basic text chunking
    - metadata: Extract enriched metadata (45 fields)
    - embeddings: Generate embeddings for chunks
    - milvus: Store in vector database

    Steps:
    1. Validate API key and permissions
    2. Chunk text using specified method
    3. Extract enriched metadata via v3 API (if permitted)
    4. Generate embeddings (if permitted)
    5. Store via Milvus Storage API (if permitted)
    """
    start_time = time.time()

    # Internal mode: all permissions granted (no external auth)
    consumer = ConsumerInfo(
        username="internal",
        tier="unlimited",
        permissions=["chunking", "metadata", "embeddings", "milvus", "llm"]
    )
    permissions_used = ["chunking"]  # Always uses chunking

    # Generate document ID if not provided
    document_id = request.document_id or f"doc_{uuid.uuid4().hex[:12]}"

    # Step 1: Chunk text
    print(f"📄 Processing document: {document_id} (Consumer: {consumer.username}, Tier: {consumer.tier})")
    chunk_start = time.time()

    try:
        chunks = perform_chunking(request.text, request)
        if not chunks:
            raise HTTPException(status_code=500, detail="Chunking produced no results")

        chunking_time = (time.time() - chunk_start) * 1000
        print(f"  ✅ Created {len(chunks)} chunks ({chunking_time:.0f}ms)")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chunking failed: {str(e)}")

    # Step 2: Generate enriched metadata via v3 API
    metadata_list = None
    metadata_model_used = None
    metadata_time = None
    if request.generate_metadata:
        permissions_used.append("metadata")

        meta_start = time.time()
        print(f"  🔍 Extracting enriched metadata (v3.0.0 - 45 fields)...")

        metadata_config = request.metadata_config or MetadataConfig()
        metadata_list, metadata_model_used = await generate_metadata_parallel(chunks, metadata_config, apikey)

        metadata_time = (time.time() - meta_start) * 1000
        successful = sum(1 for m in metadata_list if m is not None)
        print(f"  ✅ Extracted metadata for {successful}/{len(chunks)} chunks ({metadata_time:.0f}ms, model: {metadata_model_used})")

    # Step 3: Generate embeddings
    embeddings = None
    embedding_model_used = None
    embeddings_time = None
    if request.generate_embeddings:
        permissions_used.append("embeddings")

        embed_start = time.time()
        print(f"  🔢 Generating embeddings...")

        embeddings, embedding_model_used = await generate_embeddings_batch(chunks, apikey)
        if not embeddings:
            raise HTTPException(status_code=500, detail="Embeddings generation failed")

        embeddings_time = (time.time() - embed_start) * 1000
        print(f"  ✅ Generated {len(embeddings)} embeddings ({embeddings_time:.0f}ms, model: {embedding_model_used})")

    # Step 4: Build chunk data objects with ALL 45 metadata fields
    chunks_data = []
    char_pos = 0

    for idx, chunk_text in enumerate(chunks):
        char_count = len(chunk_text)
        token_count = count_tokens(chunk_text, request.encoding)

        # Extract metadata (4 core fields only)
        metadata = metadata_list[idx] if metadata_list and idx < len(metadata_list) and metadata_list[idx] else {}

        # Extract hybrid embeddings (dense + sparse)
        dense_emb = None
        sparse_emb = None
        if embeddings and idx < len(embeddings):
            dense_emb = embeddings[idx].get('dense_embedding')
            sparse_emb = embeddings[idx].get('sparse_embedding')

        chunk_data = ChunkData(
            chunk_id=f"{document_id}_chunk_{idx:04d}",
            text=chunk_text,
            index=idx,
            char_count=char_count,
            token_count=token_count,
            start_char=char_pos,
            end_char=char_pos + char_count,
            dense_embedding=dense_emb,
            sparse_embedding=sparse_emb,
            embedding=dense_emb,  # Backward compatibility

            # Basic metadata (7 fields with semantic expansion)
            keywords=metadata.get('keywords', ''),
            topics=metadata.get('topics', ''),
            questions=metadata.get('questions', ''),
            summary=metadata.get('summary', ''),
            semantic_keywords=metadata.get('semantic_keywords', ''),
            entity_relationships=metadata.get('entity_relationships', ''),
            attributes=metadata.get('attributes', '')
        )

        chunks_data.append(chunk_data)
        char_pos += char_count

    # Step 5: Store via Milvus Storage Service v1.0.0
    stored_in_milvus = False
    collection_name = None
    storage_time = None

    if request.storage_mode != StorageMode.none:
        permissions_used.append("milvus")

        if not request.generate_embeddings:
            raise HTTPException(status_code=400, detail="Cannot store in Milvus without embeddings. Set generate_embeddings=true")

        storage_start = time.time()
        print(f"  💾 Storing via Milvus Storage Service v1.0.0...")

        if request.storage_mode == StorageMode.new_collection:
            collection_name = request.collection_name or f"collection_{uuid.uuid4().hex[:8]}"
        else:
            collection_name = request.collection_name
            if not collection_name:
                raise HTTPException(status_code=400, detail="collection_name required for existing storage mode")

        try:
            # Prepare data for storage service (convert ChunkData to dict)
            storage_chunks = []
            for chunk in chunks_data:
                storage_chunk = {
                    "id": chunk.chunk_id,
                    "document_id": document_id,
                    "chunk_index": chunk.index,
                    "text": chunk.text,
                    "dense_vector": chunk.dense_embedding,  # Hybrid: dense vector
                    "sparse_vector": chunk.sparse_embedding,  # Hybrid: sparse vector
                    "tenant_id": request.tenant_id,
                    "char_count": chunk.char_count,
                    "token_count": chunk.token_count,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),

                    # Basic metadata (7 fields with semantic expansion)
                    "keywords": chunk.keywords or "",
                    "topics": chunk.topics or "",
                    "questions": chunk.questions or "",
                    "summary": chunk.summary or "",
                    "semantic_keywords": chunk.semantic_keywords or "",
                    "entity_relationships": chunk.entity_relationships or "",
                    "attributes": chunk.attributes or ""
                }
                # DEBUG: Log what we're sending to storage
                if chunk.index == 0:
                    print(f"DEBUG STORAGE chunk 0: semantic_keywords='{chunk.semantic_keywords}', entity_relationships='{chunk.entity_relationships[:60] if chunk.entity_relationships else 'EMPTY'}', attributes='{chunk.attributes[:60] if chunk.attributes else 'EMPTY'}'")
                storage_chunks.append(storage_chunk)

            # Call storage service with model information
            storage_result = await store_in_milvus_storage(
                chunks_data=storage_chunks,
                collection_name=collection_name,
                tenant_id=request.tenant_id,
                api_key=apikey,
                source_document=document_id,
                metadata_model_used=metadata_model_used,
                embedding_model_used=embedding_model_used
            )

            stored_in_milvus = storage_result.get("success", False)
            storage_time = (time.time() - storage_start) * 1000
            inserted_count = storage_result.get("inserted_count", 0)
            print(f"  ✅ Stored {inserted_count} chunks in '{collection_name}' ({storage_time:.0f}ms)")

        except Exception as e:
            print(f"  ⚠️  Milvus storage failed: {e}")
            raise HTTPException(status_code=500, detail=f"Milvus storage failed: {str(e)}")

    # Final response
    total_time = (time.time() - start_time) * 1000
    print(f"  ✅ Pipeline complete: {total_time:.0f}ms total")

    return OrchestrationResponse(
        document_id=document_id,
        total_chunks=len(chunks_data),
        processing_time_ms=round(total_time, 2),
        chunks=chunks_data,
        embeddings_generated=request.generate_embeddings,
        metadata_generated=request.generate_metadata,
        stored_in_milvus=stored_in_milvus,
        collection_name=collection_name,
        chunking_time_ms=round(chunking_time, 2),
        embeddings_time_ms=round(embeddings_time, 2) if embeddings_time else None,
        metadata_time_ms=round(metadata_time, 2) if metadata_time else None,
        storage_time_ms=round(storage_time, 2) if storage_time else None,
        consumer=consumer.username,
        tier=consumer.tier,
        permissions_used=permissions_used
    )

if __name__ == "__main__":
    print("=" * 80)
    print(f"{SERVICE_NAME} v{API_VERSION}")
    print("=" * 80)
    print("FEATURES:")
    print("  ✅ Internal-mode service (localhost only)")
    print("  ✅ Intelligent text chunking")
    print("  ✅ Enriched metadata extraction (45 fields via v3.0.0)")
    print("  ✅ Hybrid embedding generation (dense + sparse via v3.0.1)")
    print("  ✅ Milvus Storage Service integration (v1.0.0 API)")
    print("  ✅ Parallel processing for speed")
    print("  ✅ NO direct Milvus dependencies")
    print("=" * 80)
    uvicorn.run(app, host=DEFAULT_HOST, port=DEFAULT_PORT)
