#!/usr/bin/env python3
"""
Pydantic models for Compression Service v2.0.0
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from config import API_VERSION, DEFAULT_MODEL

class Chunk(BaseModel):
    """Input chunk to compress"""
    relevance_score: Optional[float] = Field(default=None, description="Relevance score from reranking (0-1)")
    id: Optional[str] = Field(default=None, description="Chunk identifier (string or int)")
    chunk_id: Optional[str] = Field(default=None, description="Alternative chunk ID field")
    text: str = Field(description="Full chunk text", min_length=1)
    document_id: Optional[str] = Field(default=None, description="Parent document ID")
    summary: Optional[str] = Field(default="", description="Optional summary (fallback if compression fails)")
    keywords: Optional[str] = Field(default="", description="Optional keywords")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 0,
                "text": "Lord Hanuman is a Hindu deity. He has immense strength and can fly. The weather today is sunny. He is devoted to Lord Rama.",
                "summary": "Description of Hanuman",
                "keywords": "Hanuman, strength, devotion"
            }
        }
    }

class CompressionRequest(BaseModel):
    """Compression request"""
    chunks: List[Chunk] = Field(description="List of chunks to compress", min_length=1, max_length=20)
    question: Optional[str] = Field(default=None, description="User question to determine relevance")
    query: Optional[str] = Field(default=None, description="Alternative field for question")
    compression_ratio: Optional[float] = Field(default=0.5, description="Target compression ratio (0.5 = keep 50%, synced with main API)", ge=0.1, le=1.0)
    max_tokens_per_chunk: Optional[int] = Field(default=200, description="Max tokens per compressed chunk", ge=50, le=500)
    model: Optional[str] = Field(default=DEFAULT_MODEL, description="Model to use for compression")
    score_threshold: Optional[float] = Field(default=0.3, description="Minimum relevance score to keep chunk (0-1)", ge=0.0, le=1.0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "chunks": [
                    {
                        "id": 0,
                        "text": "Lord Hanuman is a Hindu deity. He has immense strength and can fly. The weather today is sunny. He is devoted to Lord Rama.",
                        "summary": "Description of Hanuman",
                        "keywords": "Hanuman, strength, devotion"
                    }
                ],
                "question": "What are Hanuman's powers?",
                "compression_ratio": 0.3,
                "max_tokens_per_chunk": 200,
                "model": "7B-fast"
            }
        }
    }

class CompressedChunk(BaseModel):
    """Single compressed chunk result"""
    id: str = Field(description="Chunk identifier (string)")
    original_text: str = Field(description="Original chunk text")
    compressed_text: str = Field(description="Compressed text with only relevant sentences")
    original_length: int = Field(description="Original text length in characters")
    compressed_length: int = Field(description="Compressed text length in characters")
    compression_ratio: float = Field(description="Actual compression ratio achieved")
    compression_time_ms: float = Field(description="Time taken to compress this chunk")

class CompressionResponse(BaseModel):
    """Compression response"""
    compressed_chunks: List[CompressedChunk] = Field(description="List of compressed chunks")
    total_input_tokens: int = Field(description="Estimated total input tokens")
    total_output_tokens: int = Field(description="Estimated total output tokens")
    total_compression_time_ms: float = Field(description="Total time for all compressions")
    avg_compression_ratio: float = Field(description="Average compression ratio across all chunks")
    model_used: str = Field(description="Model used for compression")
    api_version: str = Field(default=API_VERSION, description="API version")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    service: str
    llm_gateway_connected: bool
    uptime_seconds: float
    total_requests: int

class VersionResponse(BaseModel):
    """Version information response"""
    version: str
    service: str
    description: str
    default_model: str
    max_chunks: int
    max_tokens_per_chunk: int
    endpoints: List[str]
