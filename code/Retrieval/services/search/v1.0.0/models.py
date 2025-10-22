#!/usr/bin/env python3
"""
Pydantic models for Search Service v1.0.0
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict

# ============================================================================
# Request Models
# ============================================================================

class SearchRequest(BaseModel):
    """Search request with metadata boosting"""
    query_text: str = Field(..., description="Query text to search")
    collection: str = Field(..., description="Milvus collection name")
    tenant_id: Optional[str] = Field(default=None, description="Tenant filter")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results (speed-optimized, changed from 20)")
    use_metadata_boost: bool = Field(default=True, description="Apply metadata boosting")
    boost_weights: Optional[Dict[str, float]] = Field(default=None, description="Custom boost weights")
    filter_expr: Optional[str] = Field(default=None, description="Milvus filter expression")

# ============================================================================
# Response Models
# ============================================================================

class MetadataMatch(BaseModel):
    """Metadata matching details (ALL 7 fields)"""
    # Standard metadata matches (4 fields)
    keywords_matched: List[str] = Field(default_factory=list, description="Keywords that matched")
    topics_matched: List[str] = Field(default_factory=list, description="Topics that matched")
    question_similarity: float = Field(default=0.0, description="Question similarity score (0-1)")
    summary_coverage: float = Field(default=0.0, description="Summary coverage score (0-1)")
    # Enhanced metadata matches (3 NEW fields)
    semantic_keywords_matched: List[str] = Field(default_factory=list, description="Semantic keywords that matched")
    entity_relationships_score: float = Field(default=0.0, description="Entity relationship relevance (0-1)")
    attributes_coverage: float = Field(default=0.0, description="Attributes coverage score (0-1)")

class SearchResultItem(BaseModel):
    """Single search result with metadata boosting details"""
    chunk_id: str = Field(..., description="Chunk ID")
    text: str = Field(..., description="Chunk text")
    score: float = Field(..., description="Final boosted score")
    vector_score: float = Field(..., description="Original vector similarity score")
    metadata_boost: float = Field(..., description="Total boost applied from metadata")
    metadata_matches: MetadataMatch = Field(..., description="Metadata matching details")
    document_id: Optional[str] = Field(default=None, description="Parent document ID")
    chunk_index: Optional[int] = Field(default=None, description="Chunk sequence number")
    # Standard metadata fields (4 fields)
    keywords: Optional[str] = Field(default=None, description="Chunk keywords")
    topics: Optional[str] = Field(default=None, description="Chunk topics")
    questions: Optional[str] = Field(default=None, description="Chunk questions")
    summary: Optional[str] = Field(default=None, description="Chunk summary")
    # Enhanced metadata fields (3 NEW fields)
    semantic_keywords: Optional[str] = Field(default=None, description="LLM-extracted semantic/conceptual keywords")
    entity_relationships: Optional[str] = Field(default=None, description="Entity relationships extracted from chunk")
    attributes: Optional[str] = Field(default=None, description="Entity attributes/properties extracted from chunk")

class SearchResponse(BaseModel):
    """Search response"""
    success: bool = Field(..., description="Success status")
    results: List[SearchResultItem] = Field(..., description="Search results")
    total_found: int = Field(..., description="Total results found")
    collection: str = Field(..., description="Collection searched")
    search_time_ms: float = Field(..., description="Search time in milliseconds")
    metadata_boost_applied: bool = Field(..., description="Whether metadata boost was applied")
    api_version: str = Field(..., description="API version")

# ============================================================================
# Health & Version Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    service: str
    dependencies: Dict[str, bool]
    uptime_seconds: float

class VersionResponse(BaseModel):
    """Version response"""
    version: str
    service: str
    description: str
    endpoints: List[str]
