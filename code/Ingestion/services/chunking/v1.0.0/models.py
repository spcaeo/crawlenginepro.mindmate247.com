#!/usr/bin/env python3
"""
Pydantic models for Chunking Orchestrator v5.0.0
Includes enriched metadata (45 fields from metadata v3.0.0)
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class ChunkingMethod(str, Enum):
    recursive = "recursive"
    markdown = "markdown"
    token = "token"

class StorageMode(str, Enum):
    """How to handle vector storage"""
    none = "none"           # Don't store (just return data)
    new_collection = "new"  # Create new collection
    existing = "existing"   # Add to existing collection

class MetadataConfig(BaseModel):
    """Configuration for metadata generation"""
    keywords_count: str = Field(default="5", description="Number of keywords to extract")
    topics_count: str = Field(default="3", description="Number of topics to extract")
    questions_count: str = Field(default="3", description="Number of questions to generate")
    summary_length: str = Field(default="1-2 sentences", description="Length of summary")

class OrchestrationRequest(BaseModel):
    # Text input
    text: str = Field(..., description="Text to process", min_length=1, max_length=10_000_000)

    # Chunking configuration
    method: ChunkingMethod = Field(default=ChunkingMethod.recursive)
    max_chunk_size: int = Field(default=1000, ge=100, le=10000)
    chunk_overlap: int = Field(default=300, ge=0, le=1000)
    separators: Optional[List[str]] = Field(default=None)
    markdown_headers: Optional[List[str]] = Field(default=None)
    encoding: Optional[str] = Field(default="cl100k_base")

    # Pipeline configuration
    generate_embeddings: bool = Field(default=False, description="Generate embeddings for chunks")
    generate_metadata: bool = Field(default=False, description="Extract semantic metadata")
    metadata_config: Optional[MetadataConfig] = Field(default=None)

    # Storage configuration
    storage_mode: StorageMode = Field(default=StorageMode.none, description="Vector storage mode")
    collection_name: Optional[str] = Field(default=None, description="Milvus collection name")
    tenant_id: Optional[str] = Field(default="default", description="Tenant ID for multi-tenancy")

    # Metadata for storage
    document_id: Optional[str] = Field(default=None, description="Document identifier")
    document_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional document metadata")

class ChunkData(BaseModel):
    """
    Single chunk with basic metadata (7 fields with semantic expansion)
    """
    # Core chunk info
    chunk_id: str
    text: str
    index: int
    char_count: int
    token_count: int
    start_char: int
    end_char: int

    # Vector embeddings (hybrid: dense + sparse from embeddings v3.0.0)
    dense_embedding: Optional[List[float]] = None  # Dimension from model registry
    sparse_embedding: Optional[Dict[str, float]] = None  # {token_id: weight}

    # Backward compatibility (deprecated - use dense_embedding instead)
    embedding: Optional[List[float]] = None

    # Basic metadata (7 fields - what gets stored in database)
    keywords: Optional[str] = None
    topics: Optional[str] = None
    questions: Optional[str] = None
    summary: Optional[str] = None
    semantic_keywords: Optional[str] = None
    entity_relationships: Optional[str] = None
    attributes: Optional[str] = None

class OrchestrationResponse(BaseModel):
    # Processing info
    document_id: str
    total_chunks: int
    processing_time_ms: float

    # Chunks with all data (45 metadata fields per chunk)
    chunks: List[ChunkData]

    # Pipeline status
    embeddings_generated: bool
    metadata_generated: bool
    stored_in_milvus: bool
    collection_name: Optional[str] = None

    # Performance metrics
    chunking_time_ms: float
    embeddings_time_ms: Optional[float] = None
    metadata_time_ms: Optional[float] = None
    storage_time_ms: Optional[float] = None

    # Permission info
    consumer: Optional[str] = None
    tier: Optional[str] = None
    permissions_used: Optional[List[str]] = None

    api_version: str = Field(default="5.0.0")

class HealthResponse(BaseModel):
    status: str
    version: str
    service: str
    services: Dict[str, bool]
    uptime_seconds: float
    total_requests: int

class VersionResponse(BaseModel):
    version: str
    service: str
    description: str
    endpoints: List[str]
    supported_methods: List[str]
    permission_system: Dict[str, Any]
    metadata_version: str = Field(default="3.0.0")
    storage_version: str = Field(default="1.0.0")

class ConsumerInfo(BaseModel):
    """Consumer information from APISIX"""
    username: str
    tier: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
