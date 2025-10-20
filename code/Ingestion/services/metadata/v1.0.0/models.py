#!/usr/bin/env python3
"""
Metadata Extraction Service v1.0.0 - Data Models
7 semantic fields optimized for RAG applications
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

from config import (
    MIN_TEXT_LENGTH, MAX_TEXT_LENGTH, MAX_BATCH_SIZE,
    DEFAULT_KEYWORDS_COUNT, DEFAULT_TOPICS_COUNT,
    DEFAULT_QUESTIONS_COUNT, DEFAULT_SUMMARY_LENGTH,
    ModelType, FlavorType, API_VERSION, DEFAULT_FLAVOR, DEFAULT_MODEL
)

# ============================================================================
# Request Models
# ============================================================================

class MetadataRequest(BaseModel):
    """Single metadata extraction request"""
    text: str = Field(
        ...,
        description="Text to extract metadata from",
        min_length=MIN_TEXT_LENGTH,
        max_length=MAX_TEXT_LENGTH
    )
    chunk_id: Optional[str] = Field(
        default=None,
        description="Optional chunk identifier"
    )
    extraction_mode: Optional[str] = Field(
        default="full",
        description="Extraction mode: 'basic' (7 fields optimized for RAG)"
    )
    model: Optional[ModelType] = Field(
        default=DEFAULT_MODEL,  # Use DEFAULT_MODEL from config (now BALANCED = Llama 70B)
        description="LLM model to use: 32B-fast (fastest), 480B (balanced), 72B (most accurate)"
    )
    flavor: Optional[FlavorType] = Field(
        default=DEFAULT_FLAVOR,
        description="Model flavor: base (lower cost, standard latency) or fast (higher cost, lower latency)"
    )
    keywords_count: Optional[str] = Field(
        default=DEFAULT_KEYWORDS_COUNT,
        description="Number of keywords to extract"
    )
    topics_count: Optional[str] = Field(
        default=DEFAULT_TOPICS_COUNT,
        description="Number of topics to extract"
    )
    questions_count: Optional[str] = Field(
        default=DEFAULT_QUESTIONS_COUNT,
        description="Number of questions to extract"
    )
    summary_length: Optional[str] = Field(
        default=DEFAULT_SUMMARY_LENGTH,
        description="Length of summary"
    )
    skip_cache: Optional[bool] = Field(
        default=False,
        description="Skip cache and force fresh extraction (default: False)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Python is a high-level programming language...",
                "chunk_id": "chunk_001",
                "model": "7B-fast",
                "keywords_count": "5-10",
                "topics_count": "2-5",
                "questions_count": "3",
                "summary_length": "1-2 sentences",
                "skip_cache": False
            }
        }

class BatchMetadataRequest(BaseModel):
    """Batch metadata extraction request"""
    chunks: List[MetadataRequest] = Field(
        ...,
        description="List of chunks to process",
        max_length=MAX_BATCH_SIZE
    )

# ============================================================================
# Response Models
# ============================================================================

class MetadataResponse(BaseModel):
    """Metadata extraction response - 7 fields with semantic expansion"""
    keywords: str = Field(description="Comma-separated structured keywords")
    topics: str = Field(description="Comma-separated topics")
    questions: str = Field(description="Comma-separated questions")
    summary: str = Field(description="Text summary")
    semantic_keywords: str = Field(description="Comma-separated semantic expansion keywords (synonyms, industry terms, status descriptors)")
    entity_relationships: str = Field(description="Entity relationship triplets separated by |")
    attributes: str = Field(description="Comma-separated key-value pairs for filtering")
    chunk_id: Optional[str] = Field(default=None, description="Chunk identifier")
    model_used: str = Field(description="Model used for extraction")
    processing_time_ms: float = Field(description="Processing time in milliseconds")
    api_version: str = Field(default=API_VERSION, description="API version")

    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "keywords": "Python, programming language, high-level, interpreted",
                "topics": "Programming Languages, Software Development",
                "questions": "What is Python?, Why use Python?, How does Python work?",
                "summary": "Python is a high-level interpreted programming language known for its simplicity and versatility.",
                "semantic_keywords": "scripting language, dynamic typing, object-oriented, general-purpose programming, Guido van Rossum, code readability, indentation-based syntax, interpreted language, high-level language",
                "entity_relationships": "Python → created-by → Guido van Rossum|Python → type-of → Programming Language|Python → supports → Object-Oriented Programming",
                "attributes": "language: Python, paradigm: Object-Oriented, typing: Dynamic, level: High-Level, interpretation: Interpreted",
                "chunk_id": "chunk_001",
                "model_used": "7B-fast",
                "processing_time_ms": 350.5,
                "api_version": "3.0.0"
            }
        }
    }

class BatchMetadataResponse(BaseModel):
    """Batch metadata extraction response"""
    results: List[MetadataResponse]
    total_chunks: int
    successful: int
    failed: int
    total_processing_time_ms: float
    api_version: str = Field(default=API_VERSION)

# ============================================================================
# Health & Version Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(description="Service status: healthy, degraded, unhealthy")
    version: str = Field(description="API version")
    service: str = Field(description="Service name")
    llm_gateway_connected: bool = Field(description="LLM Gateway connection status")
    uptime_seconds: float = Field(description="Service uptime in seconds")
    total_requests: int = Field(description="Total requests processed")
    cache_enabled: bool = Field(default=False, description="Whether caching is enabled")
    cache_entries: int = Field(default=0, description="Number of cached entries")
    cache_hit_rate: float = Field(default=0.0, description="Cache hit rate percentage")

class VersionResponse(BaseModel):
    """Version information response"""
    version: str
    service: str
    description: str
    supported_models: List[str]
    default_model: str
    endpoints: List[str]

class ModelInfo(BaseModel):
    """Model information"""
    model_id: str
    model_type: str
    description: str
    avg_response_time_ms: float
    recommended_for: str

    model_config = {"protected_namespaces": ()}

class ModelsResponse(BaseModel):
    """Available models response"""
    models: List[ModelInfo]
    default_model: str
    api_version: str = Field(default=API_VERSION)

# ============================================================================
# Error Models
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(description="Error type")
    detail: str = Field(description="Error details")
    chunk_id: Optional[str] = Field(default=None, description="Chunk identifier if applicable")
    api_version: str = Field(default=API_VERSION)
