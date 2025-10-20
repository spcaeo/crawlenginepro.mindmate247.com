# Milvus Storage Service v1.0.0 - Technical Documentation

**Last Updated:** October 9, 2025
**Service Version:** 1.0.0
**Documentation Purpose:** Complete disaster recovery and setup reference

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Key Features](#key-features)
4. [Performance Characteristics](#performance-characteristics)
5. [Related Documentation](#related-documentation)

---

## Overview

The Milvus Storage Service v1.0.0 is a high-performance vector storage API that provides CRUD operations for multi-tenant document chunk storage. It uses Milvus as the underlying vector database with optimized configurations for production workloads.

### Service Metadata

- **Service Name:** Milvus Storage Service
- **API Version:** 1.0.0
- **Default Port:** 8064
- **Framework:** FastAPI with Python 3.12
- **Vector Database:** Milvus 2.4+

### Key Capabilities

- **Multi-tenancy:** Partition-key based tenant isolation
- **CRUD Operations:** Full Create, Read, Update, Delete support
- **Vector Storage:** Dense (BGE-M3 1024-dim) + Sparse vectors
- **Auto-indexing:** FLAT index for exact search
- **Partition Management:** Automatic via partition_key hashing
- **High Performance:** Optimized for production workloads

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Ingestion API (Port 8060)                  │
│              (Orchestrates entire pipeline)                  │
└──────────────┬──────────────────────────────────────────────┘
               │
               ├──> Chunking Service (v1.0.0)
               ├──> Metadata Service (v1.0.0)
               ├──> Embeddings Service (v1.0.0, BGE-M3)
               │
               └──> Storage Service (v1.0.0) ← THIS SERVICE
                           │
                           ▼
                    ┌──────────────┐
                    │    Milvus    │
                    │  localhost   │
                    │  Port 19530  │
                    └──────────────┘
```

### Service Dependencies

1. **Milvus Server** (localhost:19530)
   - Vector database backend
   - Requires authentication (username/password)
   - Must be running before storage service starts

2. **Configuration File** (.env)
   - Located at PipeLineServices root
   - Contains Milvus connection settings
   - Environment-aware (development/production)

---

## Key Features

### 1. Multi-Tenancy via Partition Keys

**Implementation:** `tenant_id` field marked as partition_key in schema

```python
FieldSchema(
    name="tenant_id",
    dtype=DataType.VARCHAR,
    max_length=100,
    is_partition_key=True,  # Automatic partition management
    description="Tenant/client ID for multi-tenancy"
)
```

**Benefits:**
- Automatic partition assignment via hashing
- No manual partition management required
- Unlimited tenant_ids → Fixed physical partitions
- Excellent tenant isolation

### 2. Optimized Partition Count

**Configuration:** 256 partitions (configurable via `NUM_PARTITIONS`)

**Rationale:**
- 16x smaller search scope vs default 16 partitions
- 5-10x faster retrieval performance
- ~0.4 tenants per partition (100 tenant scenario)
- Minimal RAM overhead (~2.5 GB for metadata)
- Scales to 10,000+ tenants

**Capacity Planning:**
- 100 tenants × 20,000 chunks = 2M vectors
- 256 partitions = ~7,800 vectors per partition
- RAM usage: ~20-22 GB peak (fits in 32 GB server)

### 3. High-Performance Index Strategy

**Dense Vector Index:**
- Type: FLAT (not IVF_FLAT)
- Metric: Inner Product (IP)
- Benefits: Zero build time, 100% recall, faster for <1M vectors

**Sparse Vector Index:**
- Type: SPARSE_INVERTED_INDEX
- Metric: Inner Product (IP)
- Optimized for BM25-style sparse embeddings

### 4. Optimized Flush Strategy

**Key Optimization:** Removed blocking `flush()` calls after insert

**Rationale:**
- Milvus auto-flushes periodically (1s interval)
- Data queryable immediately without manual flush
- Saves 10+ seconds per insert operation
- Blocking flush adds unnecessary I/O overhead

**Implementation:**
```python
# Insert data
insert_result = collection.insert(data)

# NOTE: Removed collection.flush() for performance
# Milvus auto-flushes periodically (default: 1s interval)
# Data is queryable immediately after insert
```

---

## Performance Characteristics

### Storage Performance

**Genesis Document (199KB, 268 chunks):**
- First insert (creates collection): ~11-12s
- Subsequent inserts (partition only): ~1-2s expected
- Bottleneck: Collection creation overhead on first insert

**Parallel Ingestion (3 documents, shared collection):**
- Sequential time: 26.69s (if run one by one)
- Parallel time: 14.75s (3 threads simultaneously)
- Speedup: 1.81x (46.9% faster)
- Strategy: Same collection, different tenant_ids

### Retrieval Performance

**With 256 Partitions:**
- Search scope: ~7,800 vectors per partition
- Expected speedup: 5-10x faster than 16 partitions
- Mechanism: Partition key filtering during search

**Baseline (16 partitions):**
- Search scope: ~125,000 vectors per partition (2M total)
- Slower for multi-tenant queries

---

## Related Documentation

This is part 1 of 7 comprehensive documentation files:

1. **01_OVERVIEW.md** (this file) - System overview and architecture
2. **02_CONFIGURATION.md** - Complete configuration reference
3. **03_SCHEMA_AND_INDEXES.md** - Database schema and index details
4. **04_OPERATIONS.md** - CRUD operations implementation
5. **05_DEPLOYMENT.md** - Deployment and setup procedures
6. **06_PERFORMANCE_TUNING.md** - Performance optimization guide
7. **07_TROUBLESHOOTING.md** - Common issues and solutions

---

## Quick Start

For immediate disaster recovery, see:
- **05_DEPLOYMENT.md** - Complete setup from scratch
- **02_CONFIGURATION.md** - Configuration file reference
- **07_TROUBLESHOOTING.md** - Common startup issues

For optimization, see:
- **06_PERFORMANCE_TUNING.md** - Performance tuning guide
- **03_SCHEMA_AND_INDEXES.md** - Index configuration

---

**Document Status:** ✅ COMPLETE
**Disaster Recovery Ready:** YES
**Next Review Date:** Monthly or after major changes
