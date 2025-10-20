"""
Milvus Storage Service v1.0.0 - FastAPI Application
Complete CRUD API for vector storage with multi-tenancy support
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
from datetime import datetime
from pymilvus import utility

import config
import operations
from models import (
    HealthResponse, VersionResponse,
    InsertRequest, InsertResponse,
    UpdateRequest, UpdateResponse,
    DeleteRequest, DeleteResponse,
    SearchRequest, SearchResponse,
    CreateCollectionRequest, CreateCollectionResponse,
    CollectionInfoResponse, DeleteCollectionResponse,
    ErrorResponse
)

# ============================================================================
# Lifespan Management
# ============================================================================
# Startup time
SERVICE_START_TIME = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    print(f"\n{'='*60}")
    print(f"🚀 {config.SERVICE_NAME} v{config.API_VERSION}")
    print(f"{'='*60}")
    print(f"Port: {config.DEFAULT_PORT}")
    print(f"Milvus: {config.MILVUS_HOST}:{config.MILVUS_PORT}")
    print(f"{'='*60}\n")

    # Connect to Milvus
    if operations.connect_to_milvus():
        print("✅ Milvus Storage Service ready\n")
    else:
        print("⚠️  Warning: Milvus connection failed\n")

    yield

    # Shutdown
    operations.disconnect_from_milvus()
    print("\n👋 Milvus Storage Service stopped")

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title=config.SERVICE_NAME,
    description=config.SERVICE_DESCRIPTION,
    version=config.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Security Middleware (Block External Access)
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
            "detail": f"Direct access forbidden. Use gateway: https://storage.mindmate247.com",
            "api_version": config.API_VERSION
        }
    )


# ============================================================================
# Startup/Shutdown Events (Now handled by lifespan context manager above)
# ============================================================================
# REMOVED: @app.on_event("startup") - Replaced with lifespan context manager
# REMOVED: @app.on_event("shutdown") - Replaced with lifespan context manager


# ============================================================================
# Health & Version Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    milvus_connected = operations.check_connection()
    collections_count = len(utility.list_collections()) if milvus_connected else 0

    return HealthResponse(
        status="healthy" if milvus_connected else "degraded",
        version=config.API_VERSION,
        service=config.SERVICE_NAME,
        milvus_connected=milvus_connected,
        collections_count=collections_count,
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
            "/v1/insert - Insert chunks",
            "/v1/update - Update chunks",
            "/v1/delete - Delete chunks",
            "/v1/search - Hybrid search",
            "/v1/collection/{name} - Collection info",
            "/v1/collection/create - Create collection",
            "/v1/collection/delete/{name} - Delete collection"
        ]
    )


# ============================================================================
# INSERT Operation
# ============================================================================

@app.post("/v1/insert", response_model=InsertResponse)
async def insert_chunks_endpoint(request: InsertRequest):
    """
    Insert chunks with metadata and vectors into collection

    Multi-tenancy: Include tenant_id in each ChunkData object

    Example:
    ```json
    {
        "collection_name": "client_acme_products_v3",
        "chunks": [
            {
                "id": "chunk_001",
                "document_id": "doc_123",
                "chunk_index": 0,
                "text": "...",
                "tenant_id": "client_acme",
                "dense_vector": [0.1, 0.2, ...],
                "keywords": "...",
                "brand": "Apple",
                ...
            }
        ]
    }
    ```
    """
    result = operations.insert_chunks(
        collection_name=request.collection_name,
        chunks=request.chunks,
        create_if_not_exists=request.create_collection,
        source_document=request.source_document,
        preset_name=request.preset_name,
        metadata_model_used=request.metadata_model_used,
        embedding_model_used=request.embedding_model_used
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Insert failed"))

    return InsertResponse(
        success=True,
        inserted_count=result["inserted_count"],
        chunk_ids=result["chunk_ids"],
        collection_name=request.collection_name,
        processing_time_ms=result["processing_time_ms"],
        api_version=config.API_VERSION
    )


# ============================================================================
# UPDATE Operation
# ============================================================================

@app.post("/v1/update", response_model=UpdateResponse)
async def update_chunks_endpoint(request: UpdateRequest):
    """
    Update specific fields without re-processing text

    Use case: Product price changed, update price field only

    Multi-tenancy: Use tenant_id parameter to filter by tenant

    Example:
    ```json
    {
        "collection_name": "client_acme_products_v3",
        "filter": "sku == 'IPHONE-15-PRO'",
        "updates": {
            "price": 899.0,
            "sale_price": 799.0
        },
        "tenant_id": "client_acme"
    }
    ```
    """
    result = operations.update_chunks(
        collection_name=request.collection_name,
        filter_expr=request.filter,
        updates=request.updates,
        tenant_id=request.tenant_id
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Update failed"))

    return UpdateResponse(
        success=True,
        updated_count=result["updated_count"],
        collection_name=request.collection_name,
        processing_time_ms=result["processing_time_ms"],
        api_version=config.API_VERSION
    )


# ============================================================================
# DELETE Operation
# ============================================================================

@app.post("/v1/delete", response_model=DeleteResponse)
async def delete_chunks_endpoint(request: DeleteRequest):
    """
    Delete chunks matching filter

    Multi-tenancy: Use tenant_id parameter to ensure tenant isolation

    Example:
    ```json
    {
        "collection_name": "client_acme_products_v3",
        "filter": "document_id == 'doc_obsolete_123'",
        "tenant_id": "client_acme"
    }
    ```
    """
    result = operations.delete_chunks(
        collection_name=request.collection_name,
        filter_expr=request.filter,
        tenant_id=request.tenant_id
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Delete failed"))

    return DeleteResponse(
        success=True,
        deleted_count=result["deleted_count"],
        collection_name=request.collection_name,
        processing_time_ms=result["processing_time_ms"],
        api_version=config.API_VERSION
    )


@app.delete("/v1/delete/{chunk_id}")
async def delete_by_id_endpoint(
    chunk_id: str,
    collection_name: str,
    tenant_id: str = None
):
    """
    Delete single chunk by ID

    Query params:
    - collection_name: Collection name (required)
    - tenant_id: Tenant ID for multi-tenancy (optional)
    """
    filter_expr = f'id == "{chunk_id}"'

    result = operations.delete_chunks(
        collection_name=collection_name,
        filter_expr=filter_expr,
        tenant_id=tenant_id
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Delete failed"))

    return DeleteResponse(
        success=True,
        deleted_count=result["deleted_count"],
        collection_name=collection_name,
        processing_time_ms=result["processing_time_ms"],
        api_version=config.API_VERSION
    )


# ============================================================================
# SEARCH Operation
# ============================================================================

@app.post("/v1/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest):
    """
    Hybrid search (dense + sparse vectors) with metadata filtering

    Multi-tenancy: Use tenant_id parameter to filter by tenant

    Search modes:
    - "dense": Semantic search only
    - "sparse": Keyword search only
    - "hybrid": Combined (RRF fusion) - RECOMMENDED

    Example:
    ```json
    {
        "collection_name": "client_acme_products_v3",
        "query_dense": [0.1, 0.2, ...],
        "query_sparse": {45: 0.8, 123: 0.6},
        "filter": "brand == 'Apple' and price < 1000",
        "tenant_id": "client_acme",
        "limit": 20,
        "search_mode": "hybrid"
    }
    ```
    """
    result = operations.hybrid_search(
        collection_name=request.collection_name,
        query_dense=request.query_dense,
        query_sparse=request.query_sparse,
        filter_expr=request.filter,
        tenant_id=request.tenant_id,
        limit=request.limit,
        output_fields=request.output_fields,
        search_mode=request.search_mode
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Search failed"))

    return SearchResponse(
        success=True,
        results=result["results"],
        total_results=result["total_results"],
        collection_name=request.collection_name,
        search_mode=result["search_mode"],
        processing_time_ms=result["processing_time_ms"],
        api_version=config.API_VERSION
    )


# ============================================================================
# COLLECTION Management
# ============================================================================

@app.post("/v1/collection/create", response_model=CreateCollectionResponse)
async def create_collection_endpoint(request: CreateCollectionRequest):
    """
    Create new collection with v1.0.0 schema (14 fields)

    Example:
    ```json
    {
        "collection_name": "client_newcorp_docs_v3",
        "dimension": null,  // Optional: uses model registry default if not specified
        "description": "NewCorp document collection"
    }
    ```
    """
    result = operations.create_collection(
        collection_name=request.collection_name,
        dimension=request.dimension,
        source_document=request.source_document,
        preset_name=request.preset_name,
        metadata_model_used=request.metadata_model_used,
        embedding_model_used=request.embedding_model_used
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Collection creation failed"))

    return CreateCollectionResponse(
        success=True,
        collection_name=request.collection_name,
        fields_count=result["fields_count"],
        message=f"Collection created with {result['fields_count']} fields and indexes",
        api_version=config.API_VERSION
    )


@app.get("/v1/collection/{collection_name}", response_model=CollectionInfoResponse)
async def get_collection_info_endpoint(collection_name: str):
    """Get collection schema, count, and indexes"""
    result = operations.get_collection_info(collection_name)

    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "Collection not found"))

    return CollectionInfoResponse(
        success=True,
        collection_name=collection_name,
        schema=result["schema"],
        num_entities=result["num_entities"],
        indexes=result["indexes"],
        api_version=config.API_VERSION
    )


@app.delete("/v1/collection/{collection_name}", response_model=DeleteCollectionResponse)
async def delete_collection_endpoint(collection_name: str):
    """Delete entire collection (DANGEROUS - use with caution)"""
    result = operations.delete_collection(collection_name)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Collection deletion failed"))

    return DeleteCollectionResponse(
        success=True,
        collection_name=collection_name,
        message=result["message"],
        api_version=config.API_VERSION
    )


@app.get("/v1/collections")
async def list_collections_endpoint():
    """List all collections"""
    try:
        collections = utility.list_collections()
        return {
            "success": True,
            "collections": collections,
            "total_count": len(collections),
            "api_version": config.API_VERSION
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
