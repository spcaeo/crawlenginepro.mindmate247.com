#!/usr/bin/env python3
"""
Pydantic models for Reranking Service v2.0.0
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from config import API_VERSION

class RerankRequest(BaseModel):
    """Reranking request"""
    query: str = Field(..., description="Search query", min_length=1, max_length=1000)
    documents: List[str] = Field(..., description="List of documents to rerank", min_length=1, max_length=100)
    top_n: Optional[int] = Field(default=None, description="Return top N results", ge=1, le=100)

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "What is machine learning?",
                "documents": [
                    "Machine learning is a subset of AI...",
                    "Python is a programming language...",
                    "Deep learning uses neural networks..."
                ],
                "top_n": 2
            }
        }
    }

class RerankResult(BaseModel):
    """Single reranking result"""
    index: int = Field(description="Original document index")
    relevance_score: float = Field(description="Relevance score (higher is more relevant)")
    document: str = Field(description="Document text")

class RerankResponse(BaseModel):
    """Reranking response"""
    results: List[RerankResult] = Field(description="Reranked results sorted by relevance")
    query: str = Field(description="Original query")
    total_documents: int = Field(description="Total documents processed")
    returned_count: int = Field(description="Number of results returned")
    model: str = Field(description="Model used for reranking")
    processing_time_ms: float = Field(description="Processing time in milliseconds")
    api_version: str = Field(default=API_VERSION, description="API version")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    service: str
    model: str
    device: str
    uptime_seconds: float
    total_requests: int
    api_connected: bool = Field(default=True, description="Whether external API is reachable (for Jina mode)")

class VersionResponse(BaseModel):
    """Version information response"""
    version: str
    service: str
    description: str
    model: str
    max_documents: int
    max_length: int
    endpoints: List[str]

# RAG Pipeline compatibility models
class ChunkInput(BaseModel):
    """Chunk with ID for RAG pipeline"""
    chunk_id: Optional[str] = Field(default=None, description="Chunk ID")
    id: Optional[str] = Field(default=None, description="Document ID (alternative)")
    text: str = Field(..., description="Chunk text")
    document_id: Optional[str] = Field(default=None, description="Parent document ID")

class RerankChunksRequest(BaseModel):
    """Reranking request for chunks with IDs"""
    query: str = Field(..., description="Search query")
    chunks: List[ChunkInput] = Field(..., description="Chunks to rerank")
    top_k: int = Field(default=3, description="Return top K results (speed-optimized, changed from 10)", ge=1, le=100)

class RerankChunk(BaseModel):
    """Reranked chunk with score"""
    chunk_id: str = Field(description="Chunk ID")
    text: str = Field(description="Chunk text")
    relevance_score: float = Field(description="Relevance score")
    document_id: Optional[str] = Field(default=None, description="Parent document ID")

class RerankChunksResponse(BaseModel):
    """Response for chunk reranking"""
    success: bool = Field(default=True)
    reranked_chunks: List[RerankChunk] = Field(description="Reranked chunks")
    num_input_chunks: int = Field(description="Number of input chunks")
    reranking_time_ms: float = Field(description="Processing time")
    api_version: str = Field(default=API_VERSION)
