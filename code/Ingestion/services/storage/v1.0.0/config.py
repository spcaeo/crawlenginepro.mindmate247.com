"""
Milvus Storage Service v1.0.0 - Configuration
Multi-tenant vector storage with full CRUD operations
"""

import os
import sys
from pathlib import Path

# Add shared directory to path FIRST (before imports that need it)
SHARED_DIR = Path(__file__).resolve().parents[5] / "shared"
sys.path.insert(0, str(SHARED_DIR))

# Import and load environment using config_loader
from config_loader import load_shared_env
load_shared_env()

from model_registry import get_embedding_dimension

# Service metadata
API_VERSION = "1.0.0"
SERVICE_NAME = "Milvus Storage Service"
SERVICE_DESCRIPTION = "Vector storage with CRUD operations and multi-tenancy support"

# Server configuration
DEFAULT_HOST = os.getenv("HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("PORT", "8064"))

# Environment-aware Milvus connection (using PIPELINE_ENV for consistency)
PIPELINE_ENV = os.getenv("PIPELINE_ENV", "dev")
if PIPELINE_ENV == "prod":
    MILVUS_HOST = os.getenv("MILVUS_HOST_PRODUCTION", "localhost")
    MILVUS_PORT = int(os.getenv("MILVUS_PORT_PRODUCTION", "19530"))
elif PIPELINE_ENV == "staging":
    MILVUS_HOST = os.getenv("MILVUS_HOST_STAGING", os.getenv("MILVUS_HOST_DEVELOPMENT", "localhost"))
    MILVUS_PORT = int(os.getenv("MILVUS_PORT_STAGING", os.getenv("MILVUS_PORT_DEVELOPMENT", "19530")))
else:  # dev
    MILVUS_HOST = os.getenv("MILVUS_HOST_DEVELOPMENT", "localhost")
    MILVUS_PORT = int(os.getenv("MILVUS_PORT_DEVELOPMENT", "19530"))

MILVUS_USER = os.getenv("MILVUS_USER", "")
MILVUS_PASSWORD = os.getenv("MILVUS_PASSWORD", "")

print(f"[CONFIG] Environment: {PIPELINE_ENV}")
print(f"[CONFIG] Milvus: {MILVUS_HOST}:{MILVUS_PORT}")

# Schema configuration - Get dimension from shared model registry
DEFAULT_DIMENSION = get_embedding_dimension()  # Dynamically set based on embedding model in shared/model_registry.py
MAX_VARCHAR_LENGTH = 65535  # Maximum text length

print(f"[CONFIG] Default embedding dimension: {DEFAULT_DIMENSION}")

# Index configuration
# PRODUCTION-READY: Using HNSW for scalability
# - HNSW = Hierarchical Navigable Small World (graph-based)
# - Scales to billions of vectors with fast search (O(log n))
# - 99%+ recall with proper params (vs FLAT's 100%)
# - Industry standard (Pinecone, Weaviate, Qdrant use HNSW)
# - Essential for SaaS with 1000s of customers
DENSE_INDEX_TYPE = "HNSW"
DENSE_METRIC_TYPE = "IP"  # Inner Product (cosine similarity after normalization)

# HNSW parameters (optimized for production)
HNSW_M = 16  # Connections per layer (8-64, 16 is balanced for RAG)
HNSW_EF_CONSTRUCTION = 200  # Build quality (100-500, higher = better accuracy but slower build)

# Legacy IVF params (kept for backward compatibility, not used with HNSW)
DENSE_NLIST = 128  # Number of clusters for IVF

SPARSE_INDEX_TYPE = "SPARSE_INVERTED_INDEX"
SPARSE_METRIC_TYPE = "IP"

# Search configuration
DEFAULT_SEARCH_LIMIT = 20
MAX_SEARCH_LIMIT = 100
DEFAULT_NPROBE = 10  # Number of clusters to search

# Multi-tenancy
DEFAULT_TENANT_ID = "default"

# Partition Key Configuration
# Using 256 partitions for optimal retrieval performance
# - Supports 100+ tenants with excellent isolation (~0.4 tenants per partition)
# - 16x smaller search scope vs default 16 partitions
# - Minimal RAM overhead (~2.5 GB for partition metadata)
# - Scales to 10,000+ tenants easily
NUM_PARTITIONS = 256

# Performance
CONNECTION_POOL_SIZE = 10
REQUEST_TIMEOUT = 30  # seconds

# Flush configuration
# Set to False to disable automatic flush after insert (better performance but data not immediately visible)
# Set to True to enable automatic flush (slower but data immediately visible in UI)
AUTO_FLUSH_AFTER_INSERT = os.getenv("AUTO_FLUSH_AFTER_INSERT", "false").lower() == "true"

print(f"[CONFIG] Auto-flush after insert: {AUTO_FLUSH_AFTER_INSERT}")
