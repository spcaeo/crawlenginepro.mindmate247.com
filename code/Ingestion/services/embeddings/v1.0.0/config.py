#!/usr/bin/env python3
"""
Configuration for Embeddings Service v3.0.2
Multi-provider embeddings: Nebius AI Studio + Jina AI (dense-only, fast)

UPDATED: Now supports both Nebius and Jina AI providers
Uses shared model registry from /shared/model_registry.py
"""

import os
import sys
from pathlib import Path
from enum import Enum

# Add shared directory to path FIRST (before imports that need it)
SHARED_DIR = Path(__file__).resolve().parents[5] / "shared"
sys.path.insert(0, str(SHARED_DIR))

# Import and load environment using config_loader
from config_loader import load_shared_env
load_shared_env()

from model_registry import (
    EmbeddingModels,
    get_embedding_model,
    get_model_info,
    DEFAULT_EMBEDDING_MODEL
)

# Service metadata
API_VERSION = "1.0.0"
SERVICE_NAME = "Embeddings Service (Multi-Provider)"
SERVICE_DESCRIPTION = "Fast dense embeddings via Nebius AI Studio + Jina AI APIs"

# Server configuration
DEFAULT_HOST = os.getenv("HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("PORT", "8063"))  # Ingestion pipeline internal service

# Nebius AI Studio Configuration
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")
NEBIUS_API_URL = os.getenv("NEBIUS_API_URL", "https://api.studio.nebius.ai/v1/embeddings")

# SambaNova AI Configuration
SAMBANOVA_API_KEY = os.getenv("SAMBANOVA_API_KEY")
SAMBANOVA_API_URL = os.getenv("SAMBANOVA_API_URL", "https://api.sambanova.ai/v1/embeddings")

# Jina AI Configuration
JINA_API_KEY = os.getenv("JINA_API_KEY")
JINA_API_URL = os.getenv("JINA_API_URL", "https://api.jina.ai/v1/embeddings")

# At least one provider must be configured
if not NEBIUS_API_KEY and not JINA_API_KEY and not SAMBANOVA_API_KEY:
    raise ValueError("At least one API key required: NEBIUS_API_KEY, JINA_API_KEY, or SAMBANOVA_API_KEY")

# Model configuration - using shared registry
class EmbeddingModel(str, Enum):
    """Supported embedding models from all providers - maps to shared registry"""
    # Nebius models
    E5_MISTRAL = EmbeddingModels.E5_MISTRAL.value
    BGE_EN_ICL = EmbeddingModels.BGE_EN_ICL.value
    BGE_MULTILINGUAL = EmbeddingModels.BGE_MULTILINGUAL.value
    QWEN3 = EmbeddingModels.QWEN3_EMBEDDING.value
    # SambaNova models
    SAMBANOVA_E5 = EmbeddingModels.SAMBANOVA_E5_MISTRAL.value
    # Jina AI models
    JINA_V3 = EmbeddingModels.JINA_EMBEDDINGS_V3.value
    JINA_V4 = EmbeddingModels.JINA_EMBEDDINGS_V4.value

# Default model (best for RAG) - using shared registry
DEFAULT_MODEL = DEFAULT_EMBEDDING_MODEL

# Model dimensions - using shared registry (no fallbacks, registry has accurate tested values)
MODEL_DIMENSIONS = {
    EmbeddingModel.E5_MISTRAL: get_model_info(EmbeddingModels.E5_MISTRAL.value)["dimension"],
    EmbeddingModel.BGE_EN_ICL: get_model_info(EmbeddingModels.BGE_EN_ICL.value)["dimension"],
    EmbeddingModel.BGE_MULTILINGUAL: get_model_info(EmbeddingModels.BGE_MULTILINGUAL.value)["dimension"],
    EmbeddingModel.QWEN3: get_model_info(EmbeddingModels.QWEN3_EMBEDDING.value)["dimension"],
    EmbeddingModel.SAMBANOVA_E5: get_model_info(EmbeddingModels.SAMBANOVA_E5_MISTRAL.value)["dimension"],
    EmbeddingModel.JINA_V3: get_model_info(EmbeddingModels.JINA_EMBEDDINGS_V3.value)["dimension"],
    EmbeddingModel.JINA_V4: get_model_info(EmbeddingModels.JINA_EMBEDDINGS_V4.value)["dimension"]
}

# Model to provider mapping
MODEL_PROVIDERS = {
    EmbeddingModel.E5_MISTRAL: "nebius",
    EmbeddingModel.BGE_EN_ICL: "nebius",
    EmbeddingModel.BGE_MULTILINGUAL: "nebius",
    EmbeddingModel.QWEN3: "nebius",
    EmbeddingModel.SAMBANOVA_E5: "sambanova",
    EmbeddingModel.JINA_V3: "jina",
    EmbeddingModel.JINA_V4: "jina"
}

# Batch configuration
DEFAULT_BATCH_SIZE = int(os.getenv("BATCH_SIZE", "32"))
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "128"))

# Concurrency configuration (parallel API calls)
MAX_CONCURRENT_REQUESTS = 50

# Timeout configuration
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "30"))

# Response Caching Configuration
ENABLE_CACHING = os.getenv("ENABLE_CACHING", "true").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "7200"))  # 2 hours default
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "10000"))  # 10000 entries

# Rate limit handling
ENABLE_RETRY = os.getenv("ENABLE_RETRY", "true").lower() == "true"
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))  # seconds
