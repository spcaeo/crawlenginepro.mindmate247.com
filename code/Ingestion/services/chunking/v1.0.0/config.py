#!/usr/bin/env python3
"""
Configuration for Chunking Orchestrator v5.0.0
Simplified orchestration - delegates to Metadata v3 and Milvus Storage v1
"""

import os
import sys
from pathlib import Path
from enum import Enum

# Add shared directory to path FIRST (before imports that need it)
SHARED_DIR = Path(__file__).resolve().parents[5] / "shared"
sys.path.insert(0, str(SHARED_DIR))

# Import and load environment using config_loader
from config_loader import load_shared_env, get_env

# Load environment configuration (dev/prod/staging)
load_shared_env()

# Import service_registry
from service_registry import get_registry

# Service metadata
API_VERSION = "1.0.0"
SERVICE_NAME = "Chunking Orchestrator"
SERVICE_DESCRIPTION = "Complete RAG Pipeline with Enriched Metadata and Hybrid Search Support"

# Server configuration
DEFAULT_HOST = os.getenv("HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("CHUNKING_SERVICE_PORT", os.getenv("PORT", "8071")))

# ============================================================================
# Inter-Service Communication (Internal mode only)
# ============================================================================
# All services communicate directly via localhost (no external gateway)
INTERNAL_MODE = True

# ============================================================================
# Service URLs - using service_registry (environment-aware)
# ============================================================================
registry = get_registry()
EMBEDDINGS_SERVICE_URL = registry.get_service_url('embeddings')  # Already includes /v1/embeddings
METADATA_SERVICE_URL = registry.get_service_url('metadata')  # Already includes /v1/metadata
MILVUS_STORAGE_SERVICE_URL = registry.get_service_url('storage')  # Already includes /v1

print(f"[CONFIG] Internal mode (localhost communication) - Environment: {registry.environment}")
print(f"[CONFIG]   Metadata v1: {METADATA_SERVICE_URL}")
print(f"[CONFIG]   Embeddings v1: {EMBEDDINGS_SERVICE_URL}")
print(f"[CONFIG]   Storage v1: {MILVUS_STORAGE_SERVICE_URL}")

# Processing configuration
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "5"))
SERVICE_TIMEOUT = int(os.getenv("SERVICE_TIMEOUT", "60"))

# ============================================================================
# Connection Pooling Configuration
# ============================================================================
CONNECTION_POOL_SIZE = int(os.getenv("CONNECTION_POOL_SIZE", "20"))
CONNECTION_POOL_MAX = int(os.getenv("CONNECTION_POOL_MAX", "100"))
CONNECTION_TIMEOUT = int(os.getenv("CONNECTION_TIMEOUT", "60"))

# Permission levels
class PermissionLevel(str, Enum):
    """Permission levels for chunking operations"""
    CHUNKING = "chunking"
    EMBEDDINGS = "embeddings"
    METADATA = "metadata"
    MILVUS = "milvus"
    LLM = "llm"

# Processing modes
class ProcessingMode(str, Enum):
    """Processing modes for metadata/embeddings generation"""
    REALTIME = "realtime"           # Real-time parallel processing (fast, full cost)
    BATCH = "batch"                 # Batch inference (slow, 50% cost savings)
    CHUNKED_BATCH = "chunked_batch" # Process in batches (balanced)
    AUTO = "auto"                   # Intelligent auto-selection

class UrgencyLevel(str, Enum):
    """Urgency level for auto mode routing"""
    HIGH = "high"      # Need results immediately
    MEDIUM = "medium"  # Can wait a few minutes
    LOW = "low"        # Can wait hours
