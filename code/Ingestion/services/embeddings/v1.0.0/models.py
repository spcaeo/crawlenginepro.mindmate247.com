#!/usr/bin/env python3
"""
Data models for Embeddings Service v3.0.1 (Nebius API)
"""

from pydantic import BaseModel, Field
from typing import List, Union, Optional
from config import DEFAULT_MODEL

# ============================================================================
# Request Models
# ============================================================================

class EmbeddingRequest(BaseModel):
    """Request model for dense embedding generation via Nebius API"""
    input: Union[str, List[str]] = Field(..., description="Text or list of texts to embed")
    model: str = Field(default=DEFAULT_MODEL, description="Embedding model name")
    normalize: bool = Field(default=True, description="Normalize embeddings to unit length")

# ============================================================================
# Response Models
# ============================================================================

class DenseEmbeddingData(BaseModel):
    """Single dense embedding result"""
    dense_embedding: List[float] = Field(..., description="Dense semantic vector")
    index: int = Field(..., description="Index in the input batch")

class DenseEmbeddingResponse(BaseModel):
    """Response model for dense embedding generation"""
    data: List[DenseEmbeddingData]
    model: str
    dense_dimension: int = Field(..., description="Dense vector dimension")
    total_tokens: Optional[int] = None
    api_version: str
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    cached: bool = Field(default=False, description="Whether result was served from cache")
    cache_age_seconds: Optional[float] = Field(default=None, description="Age of cached result")
    source: str = Field(default="nebius_api", description="Source of embeddings (nebius_api)")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    service: str
    model: str
    dense_dimension: int
    device: str
    uptime_seconds: float
    total_requests: int
    source: str
    api_connected: bool = Field(default=False, description="Whether external API is reachable")
    cache_enabled: bool = Field(default=False, description="Whether caching is enabled")
    cache_entries: int = Field(default=0, description="Number of cached entries")
    cache_hit_rate: float = Field(default=0.0, description="Cache hit rate percentage")
