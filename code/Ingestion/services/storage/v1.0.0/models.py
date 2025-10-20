"""
Milvus Storage Service v1.0.0 - Pydantic Models
14-field minimal schema (base metadata only)
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import config

# ============================================================================
# Health & Version Models
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    version: str
    service: str
    milvus_connected: bool
    collections_count: int
    uptime_seconds: float

class VersionResponse(BaseModel):
    version: str
    service: str
    description: str
    endpoints: List[str]

# ============================================================================
# Chunk Data Model (17 fields total: 9 core + 1 vector + 7 metadata)
# ============================================================================

class ChunkData(BaseModel):
    """
    ChunkData v1.0.0 - 17 fields (base schema with semantic expansion)

    Fields:
    - Core (9): id, document_id, chunk_index, text, tenant_id, created_at, updated_at, char_count, token_count
    - Vector (1): dense_vector
    - Metadata (7): keywords, topics, questions, summary, semantic_keywords, entity_relationships, attributes
    """
    # Core fields (9)
    id: str = Field(..., description="Unique chunk ID")
    document_id: str = Field(..., max_length=100, description="Parent document ID")
    chunk_index: int = Field(..., description="Chunk position in document")
    text: str = Field(..., max_length=65535, description="Chunk text content")
    tenant_id: str = Field(default="default", max_length=100, description="Tenant ID for multi-tenancy")
    created_at: str = Field(..., max_length=50, description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(..., max_length=50, description="Last update timestamp (ISO 8601)")
    char_count: int = Field(..., description="Character count")
    token_count: int = Field(default=0, description="Token count")

    # Vector field (1)
    dense_vector: List[float] = Field(..., description="Dense semantic vector (dimension set by model)")

    # Base metadata (7 fields with semantic expansion)
    keywords: Optional[str] = Field(default="", max_length=500, description="Extracted keywords")
    topics: Optional[str] = Field(default="", max_length=500, description="Document topics")
    questions: Optional[str] = Field(default="", max_length=500, description="Related questions")
    summary: Optional[str] = Field(default="", max_length=1000, description="Chunk summary")
    semantic_keywords: Optional[str] = Field(default="", max_length=800, description="Semantic expansion keywords")
    entity_relationships: Optional[str] = Field(default="", max_length=1000, description="Entity relationship triplets")
    attributes: Optional[str] = Field(default="", max_length=1000, description="Key-value attribute pairs")

# ============================================================================
# INSERT Operation Models
# ============================================================================

class InsertRequest(BaseModel):
    collection_name: str = Field(..., description="Milvus collection name")
    chunks: List[ChunkData] = Field(..., description="List of chunks to insert")
    create_collection: bool = Field(default=True, description="Create collection if not exists")
    source_document: Optional[str] = Field(default=None, description="Source document path/name for collection description")
    preset_name: Optional[str] = Field(default=None, description="Model preset name for collection description")
    metadata_model_used: Optional[str] = Field(default=None, description="Actual metadata model used (overrides preset)")
    embedding_model_used: Optional[str] = Field(default=None, description="Actual embedding model used (overrides preset)")

class InsertResponse(BaseModel):
    success: bool
    inserted_count: int
    chunk_ids: List[str]
    collection_name: str
    processing_time_ms: float
    api_version: Optional[str] = None

# ============================================================================
# UPDATE Operation Models
# ============================================================================

class UpdateRequest(BaseModel):
    collection_name: str = Field(..., description="Milvus collection name")
    filter: str = Field(..., description="Filter expression")
    updates: Dict[str, Any] = Field(..., description="Fields to update")
    tenant_id: Optional[str] = Field(default=None, description="Filter by tenant")

class UpdateResponse(BaseModel):
    success: bool
    updated_count: int
    collection_name: str
    processing_time_ms: float
    api_version: Optional[str] = None

# ============================================================================
# DELETE Operation Models
# ============================================================================

class DeleteRequest(BaseModel):
    collection_name: str = Field(..., description="Milvus collection name")
    filter: str = Field(..., description="Filter expression")
    tenant_id: Optional[str] = Field(default=None, description="Filter by tenant")

class DeleteResponse(BaseModel):
    success: bool
    deleted_count: int
    collection_name: str
    processing_time_ms: float
    api_version: Optional[str] = None

# ============================================================================
# SEARCH Operation Models
# ============================================================================

class SearchRequest(BaseModel):
    collection_name: str = Field(..., description="Milvus collection name")
    query_dense: List[float] = Field(..., description="Dense query vector (dimension matches model)")
    query_sparse: Optional[Dict[int, float]] = Field(default=None, description="Sparse query vector (not used in v1.0.0)")
    filter: Optional[str] = Field(default=None, description="Metadata filter expression")
    tenant_id: Optional[str] = Field(default=None, description="Filter by tenant")
    limit: int = Field(default=20, ge=1, le=100, description="Number of results")
    output_fields: Optional[List[str]] = Field(default=None, description="Fields to return")
    search_mode: str = Field(default="dense", description="Search mode: dense only (v1.0.0)")

class SearchResult(BaseModel):
    model_config = {"extra": "allow"}

    score: float
    distance: Optional[float] = None
    id: Optional[str] = None
    chunk_index: Optional[int] = None
    text: Optional[str] = None
    document_id: Optional[str] = None
    tenant_id: Optional[str] = None

class SearchResponse(BaseModel):
    success: bool
    results: List[SearchResult]
    total_results: int
    collection_name: str
    search_mode: str
    processing_time_ms: float
    api_version: Optional[str] = None

# ============================================================================
# COLLECTION Management Models
# ============================================================================

class CreateCollectionRequest(BaseModel):
    collection_name: str = Field(..., description="Collection name")
    dimension: int = Field(default_factory=lambda: config.DEFAULT_DIMENSION, description="Dense vector dimension (from model registry)")
    source_document: Optional[str] = Field(default=None, description="Source document path/name for collection description")
    preset_name: Optional[str] = Field(default=None, description="Model preset name for collection description")
    metadata_model_used: Optional[str] = Field(default=None, description="Actual metadata model used (overrides preset)")
    embedding_model_used: Optional[str] = Field(default=None, description="Actual embedding model used (overrides preset)")

class CreateCollectionResponse(BaseModel):
    success: bool
    collection_name: str
    fields_count: int
    message: str
    api_version: Optional[str] = None

class CollectionInfoResponse(BaseModel):
    success: bool
    collection_name: str
    schema: Dict[str, Any]
    num_entities: int
    indexes: List[Dict[str, Any]]
    api_version: Optional[str] = None

class DeleteCollectionResponse(BaseModel):
    success: bool
    collection_name: str
    message: str
    api_version: Optional[str] = None

# ============================================================================
# Error Models
# ============================================================================

class ErrorResponse(BaseModel):
    error: str
    detail: str
    collection_name: Optional[str] = None
