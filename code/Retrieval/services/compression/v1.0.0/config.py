#!/usr/bin/env python3
"""
Configuration for Compression Service v1.0.0

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
    LLMModels,
    get_llm_for_task,
    get_model_info,
    requires_output_cleaning,
    get_cleaning_pattern
)

# Service metadata
API_VERSION = "1.0.0"
SERVICE_NAME = "Compression Service"
SERVICE_DESCRIPTION = "LLM-powered contextual compression - extract only relevant sentences"

# Server configuration
DEFAULT_HOST = os.getenv("HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("COMPRESS_SERVICE_PORT", "8073"))

# ============================================================================
# Inter-Service Communication Mode
# ============================================================================
# Set INTERNAL_MODE=true for direct service calls (lower latency)
# Set INTERNAL_MODE=false to route through APISIX (higher security, more logging)
INTERNAL_MODE = os.getenv("INTERNAL_MODE", "true").lower() == "true"

# ============================================================================
# LLM Gateway Configuration
# ============================================================================
if INTERNAL_MODE:
    # Direct internal calls (localhost) - Default mode
    LLM_GATEWAY_URL = os.getenv("LLM_GATEWAY_URL_DEVELOPMENT", "http://localhost:8065/v1/chat/completions")
else:
    # Via APISIX gateway (requires API key)
    APISIX_GATEWAY = os.getenv("APISIX_GATEWAY_URL", "http://localhost:9080")
    LLM_GATEWAY_URL = f"{APISIX_GATEWAY}/api/v2/llm/chat/completions"

# Service API key (only used if INTERNAL_MODE=false)
LLM_GATEWAY_API_KEY = os.getenv("LLM_GATEWAY_API_KEY", "")

# Compression configuration
DEFAULT_COMPRESSION_RATIO = float(os.getenv("DEFAULT_COMPRESSION_RATIO", "0.3"))
MAX_TOKENS_PER_CHUNK = int(os.getenv("MAX_TOKENS_PER_CHUNK", "200"))
MAX_CHUNKS_PER_REQUEST = int(os.getenv("MAX_CHUNKS_PER_REQUEST", "20"))
COMPRESSION_TIMEOUT = int(os.getenv("COMPRESSION_TIMEOUT", "30"))

# Model configuration - using shared registry
DEFAULT_MODEL = LLMModels.LLAMA_8B_FAST.value  # Fast model for compression (was "7B-fast")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
TOP_P = float(os.getenv("TOP_P", "0.9"))

# Retry configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "1"))

# Score-based filtering configuration
DEFAULT_SCORE_THRESHOLD = float(os.getenv("DEFAULT_SCORE_THRESHOLD", "0.3"))
