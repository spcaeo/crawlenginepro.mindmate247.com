#!/usr/bin/env python3
"""
Pydantic Models for Retrieval Pipeline API v1.0.0
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "shared"))
from model_registry import LLMModels

# ============================================================================
# Request Models
# ============================================================================

class RetrievalRequest(BaseModel):
    """Request model for RAG retrieval"""
    query: str = Field(
        ...,
        description="User query text",
        min_length=3,
        max_length=1000
    )
    collection_name: str = Field(
        ...,
        description="Target collection name",
        min_length=1,
        max_length=255
    )
    tenant_id: str = Field(
        default="default",
        description="Tenant ID for multi-tenancy",
        max_length=255
    )

    # Pipeline configuration (SPEED-OPTIMIZED DEFAULTS - synced with config.py)
    search_top_k: int = Field(
        default=10,  # Changed from 20 to match config.DEFAULT_SEARCH_TOP_K (speed optimization)
        description="Number of chunks to retrieve in search stage",
        ge=1,
        le=100
    )
    rerank_top_k: int = Field(
        default=3,  # Changed from 10 to match config.DEFAULT_RERANK_TOP_K (speed optimization)
        description="Number of chunks to keep after reranking",
        ge=1,
        le=50
    )
    max_context_chunks: int = Field(
        default=3,  # Changed from 5 to match config.DEFAULT_MAX_CONTEXT_CHUNKS (speed optimization)
        description="Maximum chunks to include in answer context",
        ge=1,
        le=20
    )
    compression_ratio: float = Field(
        default=0.5,
        description="Compression ratio (0.0 = no compression, 1.0 = full retention)",
        ge=0.0,
        le=1.0
    )
    score_threshold: float = Field(
        default=0.3,
        description="Minimum relevance score for compression filtering (0.0 to disable)",
        ge=0.0,
        le=1.0
    )

    # Feature toggles
    use_metadata_boost: bool = Field(
        default=True,
        description="Enable metadata boosting in search"
    )
    enable_reranking: bool = Field(
        default=True,
        description="Enable reranking stage"
    )
    enable_compression: bool = Field(
        default=False,  # Changed from True to match config.ENABLE_COMPRESSION (speed optimization)
        description="Enable compression stage"
    )
    enable_citations: bool = Field(
        default=False,  # Disabled by default (user preference)
        description="Include source citations in answer"
    )
    stream: bool = Field(
        default=True,  # Enabled by default for faster perceived response (TTFT optimization)
        description="Stream answer only (returns text/event-stream instead of JSON with full pipeline metadata)"
    )

    # Answer style and format configuration
    response_style: Optional[str] = Field(
        default=None,  # None = auto-detect based on intent (concise/balanced/comprehensive)
        description="Answer verbosity style: 'concise' (2-4 bullet points), 'balanced' (organized, moderate detail), 'comprehensive' (full analysis with tables/sections). None = auto-detect from query intent.",
        pattern="^(concise|balanced|comprehensive)$"
    )
    response_format: str = Field(
        default="markdown",  # Default to markdown for rich formatting
        description="Answer format: 'markdown' (tables, headings, bold, lists) or 'plain' (simple text, no formatting)",
        pattern="^(markdown|plain)$"
    )

    # LLM configuration
    model: Optional[str] = Field(
        default=None,  # None = use Intent Service recommendation, otherwise use specified model
        description="LLM model for answer generation (None = use Intent recommendation)"
    )
    temperature: float = Field(
        default=0.3,
        description="LLM temperature (0.0 = deterministic, 1.0 = creative)",
        ge=0.0,
        le=1.0
    )

# ============================================================================
# Response Models
# ============================================================================

class SearchResult(BaseModel):
    """Individual search result"""
    chunk_id: str
    text: str
    score: float
    vector_score: float
    metadata_boost: float
    document_id: str
    chunk_index: int
    keywords: Optional[str] = None
    topics: Optional[str] = None
    questions: Optional[str] = None
    summary: Optional[str] = None

class RerankedChunk(BaseModel):
    """Individual reranked chunk"""
    chunk_id: str
    text: str
    relevance_score: float
    document_id: str
    original_rank: int
    new_rank: int

class CompressedChunk(BaseModel):
    """Individual compressed chunk"""
    id: str
    compressed_text: str
    original_text: str
    compressed_length: int
    original_length: int
    compression_score: float

class Citation(BaseModel):
    """Source citation"""
    source_id: int  # Changed from str to int to match Answer Service
    chunk_id: str
    document_id: str
    text_preview: Optional[str] = None

class PipelineStageInfo(BaseModel):
    """Information about a pipeline stage"""
    time_ms: float
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class RetrievalResponse(BaseModel):
    """Response model for RAG retrieval"""
    success: bool
    query: str
    collection_name: str
    tenant_id: str

    # Final answer
    answer: str
    citations: List[Citation] = []

    # Retrieved context
    context_chunks: List[Dict[str, Any]] = []

    # Pipeline stages info
    stages: Dict[str, PipelineStageInfo]

    # Performance metrics
    total_time_ms: float
    search_results_count: int
    reranked_count: int
    compressed_count: int
    context_count: int

    # API metadata
    api_version: str = "1.0.0"
    timestamp: str

# ============================================================================
# Health Check Models
# ============================================================================

class ServiceHealth(BaseModel):
    """Health status of a service"""
    status: str  # healthy, unhealthy, degraded, timeout, unreachable
    version: Optional[str] = None
    response_time_ms: Optional[float] = None
    error: Optional[str] = None

class HealthCheckResponse(BaseModel):
    """Aggregated health check response"""
    status: str  # healthy, degraded, unhealthy
    service: str
    version: str
    timestamp: str
    dependencies: Dict[str, ServiceHealth]
    health_summary: Dict[str, int]
    response_time_ms: float
