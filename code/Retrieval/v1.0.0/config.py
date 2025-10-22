#!/usr/bin/env python3
"""
Configuration for Retrieval Pipeline API v1.0.0
Main orchestrator for RAG retrieval

UPDATED: Now uses shared model registry from /shared/model_registry.py
"""

import os
import sys
from pathlib import Path

# Add shared directory to path FIRST (before imports that need it)
SHARED_DIR = Path(__file__).resolve().parents[3] / "shared"
sys.path.insert(0, str(SHARED_DIR))

# Import and load environment using config_loader
from config_loader import load_shared_env, get_env

# Load environment configuration (dev/prod/staging)
load_shared_env()

# Import service_registry and model_registry
from service_registry import get_registry
from model_registry import (
    LLMModels,
    get_llm_for_task,
    get_model_info
)

# Service metadata
API_VERSION = "1.0.0"
SERVICE_NAME = "Retrieval Pipeline API"
SERVICE_DESCRIPTION = "RAG retrieval orchestrator: Search → Rerank → Compress → Answer"

# Server configuration
DEFAULT_HOST = os.getenv("HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("RETRIEVAL_API_PORT", "8090"))  # Development: 8090, Staging: 8100, Production: 8110

# Internal service URLs - using service_registry (environment-aware)
registry = get_registry()
INTENT_SERVICE_URL = registry.get_service_url('intent')  # Already includes /v1
SEARCH_SERVICE_URL = registry.get_service_url('search')  # Already includes /v1
RERANK_SERVICE_URL = registry.get_service_url('reranking')  # Already includes /v1
COMPRESS_SERVICE_URL = registry.get_service_url('compression')  # Already includes /v1
ANSWER_SERVICE_URL = registry.get_service_url('answer_generation')  # Already includes /v1

# Connection pooling for internal service calls
CONNECTION_POOL_SIZE = int(os.getenv("CONNECTION_POOL_SIZE", "20"))
CONNECTION_POOL_MAX = int(os.getenv("CONNECTION_POOL_MAX", "100"))
CONNECTION_TIMEOUT = int(os.getenv("CONNECTION_TIMEOUT", "60"))

# Pipeline configuration defaults (OPTIMIZED FOR SPEED)
DEFAULT_SEARCH_TOP_K = int(os.getenv("DEFAULT_SEARCH_TOP_K", "10"))  # Reduced from 20
DEFAULT_RERANK_TOP_K = int(os.getenv("DEFAULT_RERANK_TOP_K", "3"))  # Reduced from 10
DEFAULT_COMPRESSION_RATIO = float(os.getenv("DEFAULT_COMPRESSION_RATIO", "0.5"))
DEFAULT_SCORE_THRESHOLD = float(os.getenv("DEFAULT_SCORE_THRESHOLD", "0.3"))
DEFAULT_MAX_CONTEXT_CHUNKS = int(os.getenv("DEFAULT_MAX_CONTEXT_CHUNKS", "3"))  # Reduced from 5

# Input validation limits
MAX_QUERY_LENGTH = int(os.getenv("MAX_QUERY_LENGTH", "1000"))
MIN_QUERY_LENGTH = 3
MAX_COLLECTION_NAME_LENGTH = 255

# Rate limiting
MAX_CONCURRENT_RETRIEVALS = int(os.getenv("MAX_CONCURRENT_RETRIEVALS", "20"))

# Retry configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_BASE_DELAY = float(os.getenv("RETRY_BASE_DELAY", "1.0"))
RETRY_MAX_DELAY = float(os.getenv("RETRY_MAX_DELAY", "10.0"))

# Timeout configuration for each stage
INTENT_TIMEOUT = int(os.getenv("INTENT_TIMEOUT", "45"))  # seconds (LLM - SambaNova can take 30-40s)
SEARCH_TIMEOUT = int(os.getenv("SEARCH_TIMEOUT", "15"))  # seconds (increased for Milvus SSH latency)
RERANK_TIMEOUT = int(os.getenv("RERANK_TIMEOUT", "20"))  # seconds
COMPRESS_TIMEOUT = int(os.getenv("COMPRESS_TIMEOUT", "60"))  # seconds (LLM)
ANSWER_TIMEOUT = int(os.getenv("ANSWER_TIMEOUT", "90"))  # seconds (LLM - increased for long answers)

# Enable/disable pipeline stages (COMPRESSION DISABLED FOR SPEED)
ENABLE_INTENT_DETECTION = os.getenv("ENABLE_INTENT_DETECTION", "true").lower() == "true"
ENABLE_SEARCH = os.getenv("ENABLE_SEARCH", "true").lower() == "true"
ENABLE_RERANKING = os.getenv("ENABLE_RERANKING", "true").lower() == "true"
ENABLE_COMPRESSION = os.getenv("ENABLE_COMPRESSION", "false").lower() == "true"  # Disabled for speed
ENABLE_ANSWER_GENERATION = os.getenv("ENABLE_ANSWER_GENERATION", "true").lower() == "true"

# Model configuration - using shared registry
DEFAULT_ANSWER_MODEL = LLMModels.LLAMA_70B_FAST.value  # Fast 70B model for answers (was "meta-llama/Llama-3.3-70B-Instruct-fast")
