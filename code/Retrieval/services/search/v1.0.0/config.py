#!/usr/bin/env python3
"""
Configuration for Search Service v1.0.0
Dense vector search + metadata boosting (ALL 4 fields)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load common .env from PipeLineServices root
env_path = Path(__file__).resolve().parents[4] / ".env"
load_dotenv(env_path)

# Service metadata
API_VERSION = "1.0.0"
SERVICE_NAME = "Search Service"
SERVICE_DESCRIPTION = "Dense vector search + metadata boosting (ALL 4 fields)"

# Server config
DEFAULT_HOST = os.getenv("HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("SEARCH_SERVICE_PORT", "8071"))

# Dependent service URLs
EMBEDDINGS_URL = os.getenv("EMBEDDINGS_SERVICE_URL", "http://localhost:8063/v1/embeddings")  # Ingestion embeddings service
STORAGE_URL = os.getenv("STORAGE_SERVICE_URL", "http://localhost:8064/v1")  # Ingestion storage service

# Milvus connection (for direct queries if needed)
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))

# Search parameters
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "10"))  # Reduced from 20 for speed
MAX_TOP_K = int(os.getenv("MAX_TOP_K", "100"))
DEFAULT_SEARCH_METRIC = "COSINE"  # For dense vectors

# Metadata boost weights (ALL 4 FIELDS) - Hybrid Approach (Balanced)
BOOST_WEIGHTS = {
    "keywords": float(os.getenv("BOOST_KEYWORDS", "0.15")),      # Exact keyword matches (increased from 0.10)
    "topics": float(os.getenv("BOOST_TOPICS", "0.10")),        # Category relevance (increased from 0.05)
    "questions": float(os.getenv("BOOST_QUESTIONS", "0.15")),     # Question similarity (increased from 0.08 - Q&A focus)
    "summary": float(os.getenv("BOOST_SUMMARY", "0.10"))        # Coverage check (increased from 0.07)
}
MAX_TOTAL_BOOST = float(os.getenv("MAX_TOTAL_BOOST", "0.50"))  # Cap at 50% boost (increased from 30%)

# Performance settings
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))  # seconds
ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour
