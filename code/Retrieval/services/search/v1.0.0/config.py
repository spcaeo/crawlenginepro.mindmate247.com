#!/usr/bin/env python3
"""
Configuration for Search Service v1.0.0
Dense vector search + metadata boosting (ALL 7 fields)
"""

import os
import sys
from pathlib import Path

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
SERVICE_NAME = "Search Service"
SERVICE_DESCRIPTION = "Dense vector search + metadata boosting (ALL 7 fields)"

# Server config
DEFAULT_HOST = os.getenv("HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("SEARCH_SERVICE_PORT", "8071"))

# Dependent service URLs - using service_registry (environment-aware)
registry = get_registry()
EMBEDDINGS_URL = registry.get_service_url('embeddings')  # Already includes /v1/embeddings
STORAGE_URL = registry.get_service_url('storage')  # Already includes /v1

# Milvus connection (for direct queries if needed)
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))

# Search parameters
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "10"))  # Reduced from 20 for speed
MAX_TOP_K = int(os.getenv("MAX_TOP_K", "100"))
DEFAULT_SEARCH_METRIC = "COSINE"  # For dense vectors

# Metadata boost weights (ALL 7 FIELDS) - Enhanced with semantic metadata
BOOST_WEIGHTS = {
    # Standard metadata (4 fields) - slightly reduced to make room for enhanced fields
    "keywords": float(os.getenv("BOOST_KEYWORDS", "0.10")),      # Exact keyword matches
    "topics": float(os.getenv("BOOST_TOPICS", "0.06")),          # Category relevance
    "questions": float(os.getenv("BOOST_QUESTIONS", "0.08")),    # Question similarity
    "summary": float(os.getenv("BOOST_SUMMARY", "0.06")),        # Coverage check
    # Enhanced metadata (3 NEW fields)
    "semantic_keywords": float(os.getenv("BOOST_SEMANTIC_KEYWORDS", "0.15")),  # LLM-extracted conceptual keywords (highest weight)
    "entity_relationships": float(os.getenv("BOOST_ENTITY_RELATIONSHIPS", "0.10")),  # Entity relationships (for "who did what" queries)
    "attributes": float(os.getenv("BOOST_ATTRIBUTES", "0.08"))   # Entity attributes (for attribute-based queries)
}
MAX_TOTAL_BOOST = float(os.getenv("MAX_TOTAL_BOOST", "0.60"))  # Cap at 60% boost (increased to accommodate 7 fields)

# Performance settings
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))  # seconds
ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour
