#!/usr/bin/env python3
"""
LLM Gateway Service v2.0.0 - Data Models
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

from config import API_VERSION, ModelType

# ============================================================================
# Request Models
# ============================================================================

class ChatMessage(BaseModel):
    """Chat message"""
    role: str = Field(description="Message role: system, user, or assistant")
    content: str = Field(description="Message content")

    model_config = {"protected_namespaces": ()}

class ResponseFormat(BaseModel):
    """Response format specification"""
    type: str = Field(description="Format type: json_object, json_schema, or text")
    json_schema: Optional[Dict[str, Any]] = Field(default=None, description="JSON schema definition")

class ChatCompletionRequest(BaseModel):
    """Chat completion request"""
    model: Optional[str] = Field(
        default=None,
        description="Specific model name or use 'use_case' instead"
    )
    messages: List[ChatMessage] = Field(description="Conversation messages")
    temperature: Optional[float] = Field(default=0.7, description="Sampling temperature 0-2")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")
    stream: Optional[bool] = Field(default=False, description="Stream responses")
    use_case: Optional[str] = Field(
        default=None,
        description="Use case: fast, basic, code, reasoning, vision"
    )
    response_format: Optional[ResponseFormat] = Field(
        default=None,
        description="Response format (json_object or json_schema for structured output)"
    )

    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "model": "Qwen/Qwen2.5-Coder-7B-fast",
                "messages": [
                    {"role": "user", "content": "Explain Python decorators"}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
        }
    }

# ============================================================================
# Response Models
# ============================================================================

class UsageInfo(BaseModel):
    """Token usage information"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ResponseMessage(BaseModel):
    """Response message"""
    role: str
    content: str

    model_config = {"protected_namespaces": ()}

class Choice(BaseModel):
    """Response choice"""
    index: int
    message: ResponseMessage
    finish_reason: Optional[str] = None

    model_config = {"protected_namespaces": ()}

class MetadataInfo(BaseModel):
    """Request metadata"""
    response_time_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    model_used: str
    tenant: str
    cached: bool = False

    model_config = {"protected_namespaces": ()}

class ChatCompletionResponse(BaseModel):
    """Chat completion response"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: UsageInfo
    tenant: str = Field(description="Tenant name")
    metadata: MetadataInfo = Field(description="Additional metadata")

    model_config = {"protected_namespaces": ()}

# ============================================================================
# Health & Version Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    service: str
    nebius_connected: bool
    uptime_seconds: float
    total_requests: int
    cache_enabled: bool = Field(default=False, description="Whether caching is enabled")
    cache_entries: int = Field(default=0, description="Number of cached entries")
    cache_hit_rate: float = Field(default=0.0, description="Cache hit rate percentage")

class VersionResponse(BaseModel):
    """Version information"""
    version: str
    service: str
    description: str
    supported_models: List[str]
    default_models: Dict[str, str]
    endpoints: List[str]

class ModelInfo(BaseModel):
    """Model information"""
    model_id: str
    model_type: str
    description: str
    pricing_per_1m_tokens: float
    recommended_for: str

    model_config = {"protected_namespaces": ()}

class ModelsResponse(BaseModel):
    """Available models response"""
    models: List[ModelInfo]
    default_models: Dict[str, str]
    api_version: str = Field(default=API_VERSION)

    model_config = {"protected_namespaces": ()}

# ============================================================================
# Error Models
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: str
    api_version: str = Field(default=API_VERSION)
