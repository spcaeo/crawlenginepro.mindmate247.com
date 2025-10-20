#!/usr/bin/env python3
"""
Data models for Answer Generation Service v1.0.0
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class ContextChunk(BaseModel):
    """Single context chunk for answer generation"""
    chunk_id: str = Field(..., description="Unique chunk ID")
    text: str = Field(..., description="Chunk text content")
    document_id: Optional[str] = Field(None, description="Source document ID")
    chunk_index: Optional[int] = Field(None, description="Chunk index in document")
    score: Optional[float] = Field(None, description="Relevance score")
    # Metadata fields (optional)
    topics: Optional[str] = Field(None, description="Topics/categories extracted from chunk")
    keywords: Optional[str] = Field(None, description="Keywords extracted from chunk")
    questions: Optional[str] = Field(None, description="Questions this chunk answers")
    summary: Optional[str] = Field(None, description="Summary of chunk content")

class AnswerRequest(BaseModel):
    """Request for answer generation"""
    query: str = Field(..., description="User query/question")
    context_chunks: List[ContextChunk] = Field(
        ...,
        description="Retrieved context chunks for answer generation"
    )
    llm_model: Optional[str] = Field(
        default=None,
        description="LLM model to use (default: 32B-fast)"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        le=4096,
        description="Maximum tokens for answer"
    )
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Temperature for generation"
    )
    enable_citations: bool = Field(
        default=False,  # Disabled by default (user preference)
        description="Include citations in answer"
    )
    cite_only_relevant_sources: bool = Field(
        default=True,
        description="Only cite sources relevant to answer (true) or explain all sources including irrelevant ones (false)"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="Custom system prompt for answer generation (overrides default prompt based on intent)"
    )
    stream: bool = Field(
        default=True,  # Enabled by default for faster perceived response (TTFT optimization)
        description="Stream response as Server-Sent Events"
    )
    use_cache: bool = Field(
        default=True,
        description="Use cached results if available"
    )
    include_metadata_questions: bool = Field(
        default=False,
        description="Include questions field in context metadata (default: False for performance optimization - reduces token usage and latency)"
    )

class Citation(BaseModel):
    """Citation reference in answer"""
    source_id: int = Field(..., description="Source number (e.g., 1, 2, 3)")
    chunk_id: str = Field(..., description="Referenced chunk ID")
    document_id: Optional[str] = Field(None, description="Source document ID")
    text_snippet: str = Field(..., description="Relevant text snippet from source")

class AnswerResponse(BaseModel):
    """Response from answer generation"""
    success: bool = Field(..., description="Whether request succeeded")
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    citations: Optional[List[Citation]] = Field(
        default=None,
        description="Citations used in answer"
    )
    num_chunks_used: int = Field(..., description="Number of context chunks used")
    generation_time_ms: float = Field(..., description="Time taken to generate (ms)")
    cache_hit: bool = Field(default=False, description="Whether result was from cache")
    llm_model_used: str = Field(..., description="LLM model used")
    tokens_used: Optional[int] = Field(None, description="Approximate tokens used")
    api_version: str = Field(..., description="API version")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    service: str = Field(..., description="Service name")
    dependencies: Dict[str, bool] = Field(..., description="Dependency health")
    uptime_seconds: float = Field(..., description="Service uptime")

class VersionResponse(BaseModel):
    """Version information response"""
    version: str = Field(..., description="API version")
    service: str = Field(..., description="Service name")
    description: str = Field(..., description="Service description")
    endpoints: List[str] = Field(..., description="Available endpoints")
