#!/usr/bin/env python3
"""
LLM Gateway Service v2.0.0 - Configuration
Proxy to Nebius AI Studio with tenant API key management and cost tracking
https://llm.mindmate247.com/

UPDATED: Now uses shared model registry from /shared/model_registry.py
"""

import os
import sys
from pathlib import Path
from enum import Enum

# Add shared directory to path
SHARED_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "shared"
sys.path.insert(0, str(SHARED_DIR))

# Load shared configuration (from /code/shared/.env.dev or .env.prod)
from config_loader import load_shared_env
load_shared_env()

from model_registry import (
    LLMModels,
    get_model_info,
    get_llm_for_task,
    get_model_provider,
    is_sambanova_model
)

# ============================================================================
# Version Management
# ============================================================================
API_VERSION = "1.0.0"
SERVICE_NAME = "LLM Gateway Service"
SERVICE_DESCRIPTION = "Nebius AI Studio proxy with tenant API keys, cost tracking, and model management"

# ============================================================================
# Server Configuration
# ============================================================================
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = int(os.getenv("LLM_GATEWAY_SERVICE_PORT", os.getenv("PORT", "8075")))
DEFAULT_WORKERS = 2

# ============================================================================
# Nebius AI Studio Configuration
# ============================================================================
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")
# LLM Gateway uses base URL (not embeddings endpoint)
# Use NEBIUS_LLM_URL if set, otherwise fall back to base v1 URL
NEBIUS_API_URL = os.getenv("NEBIUS_LLM_URL", "https://api.studio.nebius.ai/v1")

if not NEBIUS_API_KEY:
    raise ValueError("NEBIUS_API_KEY environment variable is required")

# ============================================================================
# SambaNova AI Configuration
# ============================================================================
SAMBANOVA_API_KEY = os.getenv("SAMBANOVA_API_KEY")
SAMBANOVA_API_URL = os.getenv("SAMBANOVA_API_URL", "https://api.sambanova.ai/v1/chat/completions")

# SambaNova is optional - only warn if models are requested but key is missing
if SAMBANOVA_API_KEY:
    print(f"[CONFIG] SambaNova AI enabled - {len([m for m in LLMModels if 'SAMBANOVA' in m.name])} models available")
else:
    print("[CONFIG] SambaNova AI disabled - set SAMBANOVA_API_KEY to enable")

# ============================================================================
# Model Definitions - Now using shared registry
# ============================================================================
class ModelType(str, Enum):
    """Available LLM models - maps to shared registry"""
    # Fast flavor models for RAG
    GEMMA_2B = "gemma-2b"
    GEMMA_9B_FAST = "gemma-9b-fast"
    ULTRA_FAST = "llama-8B-fast"
    DEVSTRAL_SMALL = "devstral-small"
    QWEN_32B_FAST = "qwen-32b-fast"
    QWQ_32B_FAST = "qwq-32b-fast"
    LLAMA_70B_FAST = "llama-70b-fast"
    # Legacy aliases
    FAST = "7B-fast"
    RECOMMENDED = "32B-fast"
    BALANCED = "72B"
    ADVANCED = "480B"
    REASONING = "reasoning"
    VISION = "vision"

# Model name mappings - using shared registry
MODEL_NAMES = {
    # Fast flavor models
    ModelType.GEMMA_2B: LLMModels.GEMMA_2B.value,
    ModelType.GEMMA_9B_FAST: LLMModels.GEMMA_9B_FAST.value,
    ModelType.ULTRA_FAST: LLMModels.LLAMA_8B_FAST.value,
    ModelType.DEVSTRAL_SMALL: LLMModels.DEVSTRAL_SMALL.value,
    ModelType.QWEN_32B_FAST: LLMModels.QWEN_32B_FAST.value,
    ModelType.QWQ_32B_FAST: LLMModels.QWQ_32B_FAST.value,
    ModelType.LLAMA_70B_FAST: LLMModels.LLAMA_70B_FAST.value,
    # Legacy mappings
    ModelType.FAST: LLMModels.QWEN_32B_FAST.value,
    ModelType.RECOMMENDED: LLMModels.QWEN_32B_FAST.value,
    ModelType.BALANCED: LLMModels.QWEN_72B.value,
    ModelType.ADVANCED: LLMModels.QWEN_CODER_480B.value,
    ModelType.REASONING: LLMModels.DEEPSEEK_R1.value,
    ModelType.VISION: LLMModels.QWEN_VL_72B.value
}

# Default models for different use cases
DEFAULT_MODELS = {
    "fast": MODEL_NAMES[ModelType.RECOMMENDED],
    "basic": MODEL_NAMES[ModelType.RECOMMENDED],
    "code": MODEL_NAMES[ModelType.ADVANCED],
    "reasoning": MODEL_NAMES[ModelType.REASONING],
    "vision": MODEL_NAMES[ModelType.VISION]
}

# Model pricing - using shared registry pricing info
MODEL_PRICING = {
    model.value: get_model_info(model.value).get("cost_per_1m_tokens", 0.20)
    for model in LLMModels
}

# ============================================================================
# Tenant API Keys
# ============================================================================
TENANT_API_KEYS = {
    "Developer": os.getenv("DEVELOPER_KEY", "dev_crawlenginepro_2025_secret_key_001"),
    "Enterprise": os.getenv("ENTERPRISE_KEY", "sk-enterprise-mindmate247-2025-v2"),
    "Internal": os.getenv("INTERNAL_SERVICE_KEY", "internal_service_2025_secret_key_metadata_embeddings"),
    # Add more tenant keys here as needed
}

# ============================================================================
# Performance & Timeouts
# ============================================================================
DEFAULT_TIMEOUT = 60  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

def get_version_info():
    """Get version information"""
    return {
        "version": API_VERSION,
        "service": SERVICE_NAME,
        "description": SERVICE_DESCRIPTION,
        "supported_models": [m.value for m in ModelType],
        "default_models": DEFAULT_MODELS
    }
