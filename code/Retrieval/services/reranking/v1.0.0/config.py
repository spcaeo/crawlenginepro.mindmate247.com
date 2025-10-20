#!/usr/bin/env python3
"""
Configuration for Reranking Service v1.0.0

UPDATED: Now uses shared model registry from /shared/model_registry.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load common .env from PipeLineServices root
env_path = Path(__file__).resolve().parents[4] / ".env"
load_dotenv(env_path)

# Add shared directory to path
SHARED_DIR = env_path.parent / "shared"
sys.path.insert(0, str(SHARED_DIR))

from model_registry import (
    RerankingModels,
    get_reranking_model,
    get_model_info
)

# Service metadata
API_VERSION = "1.0.0"
SERVICE_NAME = "Reranking Service"
SERVICE_DESCRIPTION = "Rerank documents by relevance using BGE-Reranker-v2-M3"

# Server configuration
DEFAULT_HOST = os.getenv("HOST", "0.0.0")
DEFAULT_PORT = int(os.getenv("RERANK_SERVICE_PORT", "8072"))

# Reranker backend selection
RERANKER_BACKEND = os.getenv("RERANKER_BACKEND", "bge")  # "bge" or "jina"

# BGE Model configuration (default) - using shared registry
MODEL_NAME = RerankingModels.BGE_RERANKER_V2_M3.value
MAX_LENGTH = int(os.getenv("MAX_LENGTH", "512"))
DEVICE = os.getenv("DEVICE", "cpu")  # cuda or cpu

# Jina AI configuration (optional) - using shared registry
JINA_AI_KEY = os.getenv("JINA_AI_KEY", None)
JINA_API_URL = os.getenv("JINA_API_URL", "https://api.jina.ai/v1/rerank")
JINA_MODEL = RerankingModels.JINA_RERANKER_V2.value

# Processing configuration
MAX_DOCUMENTS = int(os.getenv("MAX_DOCUMENTS", "100"))
DEFAULT_TOP_N = int(os.getenv("DEFAULT_TOP_N", "3"))  # Reduced from 10 for speed
