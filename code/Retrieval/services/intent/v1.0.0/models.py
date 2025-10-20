#!/usr/bin/env python3
"""
Data models for Intent & Prompt Adaptation Service v1.0.0
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class IntentRequest(BaseModel):
    """Request model for intent analysis"""
    query: str = Field(..., description="User query to analyze")
    language: Optional[str] = Field(None, description="Pre-detected language (optional)")
    enable_citations: bool = Field(default=True, description="Whether to include citation instructions in system prompt")
    response_style: Optional[str] = Field(None, description="Explicit answer style: concise/balanced/comprehensive (None = auto-detect)")
    response_format: str = Field(default="markdown", description="Answer format: markdown or plain")


class IntentResponse(BaseModel):
    """Response model for intent analysis"""
    intent: str = Field(..., description="Detected intent type (comparison, aggregation, factual_retrieval, etc.)")
    language: str = Field(..., description="Detected language (ISO 639-1 code)")
    complexity: str = Field(..., description="Query complexity: simple|moderate|complex")
    requires_math: bool = Field(..., description="Whether query requires calculations")
    system_prompt: str = Field(..., description="Adapted system prompt for Answer Generation")
    confidence: float = Field(..., description="Confidence score (0-1)")
    analysis_time_ms: float = Field(..., description="Time taken for analysis in milliseconds")
    recommended_model: str = Field(..., description="Recommended LLM model for Answer Generation based on intent complexity")
    recommended_max_tokens: int = Field(..., description="Recommended max_tokens for Answer Generation based on intent type (512-3072)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata (pattern matching info, etc.)")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    llm_gateway_connected: bool = Field(default=False, description="Whether LLM Gateway is reachable")
