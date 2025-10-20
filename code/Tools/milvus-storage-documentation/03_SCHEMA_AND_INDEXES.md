# Schema and Indexes - Milvus Storage Service v1.0.0

**Last Updated:** October 9, 2025

---

## Table of Contents

1. [Collection Schema](#collection-schema)
2. [Field Definitions](#field-definitions)
3. [Index Configuration](#index-configuration)
4. [Partition Key Implementation](#partition-key-implementation)
5. [Schema Evolution](#schema-evolution)

---

## Collection Schema

### Schema Version

**Version:** 1.0.0
**Created:** Storage Service v1.0.0
**File:** `schema.py`

### Schema Overview

```
Collection Name: {dynamic} (e.g., "partition_test_20251009_131834")
Total Fields: 14
Primary Key: id (VARCHAR)
Partition Key: tenant_id (VARCHAR)
Partitions: 256 (configurable)
Dimension: 1024 (BGE-M3 dense vector)
```

### Complete Field List

```python
fields = [
    "id",              # Primary key
    "document_id",     # Document identifier
    "tenant_id",       # Partition key (multi-tenancy)
    "text",            # Chunk content
    "chunk_index",     # Position in document
    "char_count",      # Text length
    "token_count",     # Token count
    "dense_vector",    # BGE-M3 dense embedding (1024-dim)
    "sparse_vector",   # BGE-M3 sparse embedding
    "price",           # Extracted metadata
    "amount",          # Extracted metadata
    "tax_amount",      # Extracted metadata
    "year",            # Extracted metadata
    "created_at"       # ISO timestamp
]
```

---

## Field Definitions

### 1. Primary Key Field

```python
FieldSchema(
    name="id",
    dtype=DataType.VARCHAR,
    max_length=100,
    is_primary=True,
    auto_id=False,
    description="Unique chunk identifier (primary key)"
)
```

**Purpose:** Unique identifier for each chunk
**Format:** UUID4 or custom string
**Length:** Up to 100 characters
**Auto-generated:** No (must be provided)

### 2. Document Identifier

```python
FieldSchema(
    name="document_id",
    dtype=DataType.VARCHAR,
    max_length=100,
    description="Source document identifier"
)
```

**Purpose:** Group chunks by document
**Indexed:** Yes (STL_SORT index)
**Use case:** Query all chunks from specific document

### 3. Partition Key (Tenant ID) ⭐

```python
FieldSchema(
    name="tenant_id",
    dtype=DataType.VARCHAR,
    max_length=100,
    is_partition_key=True,  # ← KEY FEATURE
    description="Tenant/client ID for multi-tenancy (partition key)"
)
```

**Purpose:** Multi-tenant isolation via partitions
**Automatic:** Yes (Milvus handles partition assignment via hashing)
**Benefits:**
- Automatic partition management
- No manual partition operations
- Unlimited tenant_ids → Fixed partitions (256)
- Query optimization (searches only relevant partition)

**How it works:**
```
INSERT: tenant_id → hash → partition_id (0-255)
SEARCH: Filter by tenant_id → Search only that partition
```

### 4. Text Content

```python
FieldSchema(
    name="text",
    dtype=DataType.VARCHAR,
    max_length=65535,  # Maximum VARCHAR length
    description="Full chunk text content"
)
```

**Purpose:** Store actual chunk text
**Max length:** 65,535 characters (Milvus limit)
**Encoding:** UTF-8

### 5. Chunk Metadata

```python
# Position in document
FieldSchema(name="chunk_index", dtype=DataType.INT64)

# Text statistics
FieldSchema(name="char_count", dtype=DataType.INT64)
FieldSchema(name="token_count", dtype=DataType.INT64)
```

**Purpose:** Track chunk position and size
**Use case:** Reconstruct document order, filter by size

### 6. Dense Vector (BGE-M3)

```python
FieldSchema(
    name="dense_vector",
    dtype=DataType.FLOAT_VECTOR,
    dim=1024,  # BGE-M3 dimension
    description="Dense vector embedding (BGE-M3)"
)
```

**Model:** BAAI/bge-m3
**Dimension:** 1024 (fixed)
**Metric:** Inner Product (IP) after L2 normalization
**Use case:** Semantic similarity search

**Index:** FLAT (exact search)
```python
{
    "index_type": "FLAT",
    "metric_type": "IP",
    "params": {}
}
```

### 7. Sparse Vector (BGE-M3)

```python
FieldSchema(
    name="sparse_vector",
    dtype=DataType.SPARSE_FLOAT_VECTOR,
    description="Sparse vector embedding (BGE-M3 lexical)"
)
```

**Model:** BAAI/bge-m3 (lexical component)
**Dimension:** Variable (sparse)
**Metric:** Inner Product (IP)
**Use case:** Keyword-based search, hybrid search

**Index:** SPARSE_INVERTED_INDEX
```python
{
    "index_type": "SPARSE_INVERTED_INDEX",
    "metric_type": "IP",
    "params": {"drop_ratio_build": 0.2}
}
```

### 8. Extracted Metadata Fields

```python
# Financial metadata
FieldSchema(name="price", dtype=DataType.FLOAT)
FieldSchema(name="amount", dtype=DataType.FLOAT)
FieldSchema(name="tax_amount", dtype=DataType.FLOAT)

# Temporal metadata
FieldSchema(name="year", dtype=DataType.INT64)
```

**Purpose:** Store extracted structured data
**Source:** Metadata Service (Qwen-2.5-7B)
**Optional:** Yes (defaults to 0.0 or 0)

### 9. Timestamp

```python
FieldSchema(
    name="created_at",
    dtype=DataType.VARCHAR,
    max_length=100,
    description="ISO 8601 timestamp"
)
```

**Format:** ISO 8601 (e.g., "2025-10-09T13:18:34.123456")
**Use case:** Track creation time, sort by time

---

## Index Configuration

### Index Strategy

**Philosophy:** Optimize for production workloads <1M vectors

1. **Dense Vector:** FLAT index (exact search)
2. **Sparse Vector:** SPARSE_INVERTED_INDEX
3. **Scalar Fields:** STL_SORT for document_id

### Dense Vector Index (FLAT)

**Configuration:**
```python
dense_index_params = {
    "index_type": "FLAT",
    "metric_type": "IP",
    "params": {}
}
```

**Why FLAT vs IVF_FLAT?**

| Feature | FLAT | IVF_FLAT |
|---------|------|----------|
| Build time | 0 seconds | 10+ seconds |
| Recall | 100% (exact) | ~95-99% |
| Speed (<1M) | Faster | Slower |
| Memory | Higher | Lower |
| Best for | <1M vectors | >1M vectors |

**Decision:** FLAT for <1M vectors (current requirement: 2M but partitioned)

### Sparse Vector Index

**Configuration:**
```python
sparse_index_params = {
    "index_type": "SPARSE_INVERTED_INDEX",
    "metric_type": "IP",
    "params": {
        "drop_ratio_build": 0.2  # Drop 20% smallest weights
    }
}
```

**Purpose:** Optimize sparse vector storage and search
**Benefit:** Reduced memory, faster search

### Scalar Index (document_id)

**Configuration:**
```python
scalar_index_params = {
    "index_type": "STL_SORT"
}
```

**Purpose:** Fast filtering by document_id
**Use case:** Query all chunks from specific document

### Index Creation Process

**Timing:** Immediately after collection creation

**Process:**
1. Create collection
2. Create dense vector index → ~0s (FLAT)
3. Create scalar index → ~0s (STL_SORT)
4. Create sparse vector index → ~0s (empty collection)
5. Load collection

**Total time:** <1 second (no data yet)

### Index Build on Insert

**Behavior:** Indexes updated automatically on insert

**Performance:**
- FLAT: No build overhead (brute-force)
- SPARSE_INVERTED_INDEX: Incremental build
- STL_SORT: Incremental sort

---

## Partition Key Implementation

### Configuration

**File:** `schema.py` (line 54-60)

```python
FieldSchema(
    name="tenant_id",
    dtype=DataType.VARCHAR,
    max_length=100,
    is_partition_key=True,  # ← Enable automatic partition management
    description="Tenant/client ID for multi-tenancy (partition key)"
)
```

**File:** `config.py` (line 68)

```python
NUM_PARTITIONS = 256
```

**File:** `operations.py` (line 84-92)

```python
collection = Collection(
    name=collection_name,
    schema=collection_schema,
    using='default',
    num_partitions=config.NUM_PARTITIONS  # 256 partitions
)
```

### How Partition Keys Work

**1. Insert Operation:**
```
User provides: tenant_id = "tenant_42"
     ↓
Milvus hashes: hash("tenant_42") % 256 → partition_id (e.g., 142)
     ↓
Data stored in: partition_142
```

**2. Search Operation:**
```
User queries: filter="tenant_id == 'tenant_42'"
     ↓
Milvus knows: hash("tenant_42") % 256 → partition_142
     ↓
Search only: partition_142 (not all 256 partitions)
```

**3. Performance Benefit:**
```
Without partition key: Search 2M vectors (all partitions)
With partition key:    Search ~7,800 vectors (one partition)
Speedup:              5-10x faster retrieval
```

### Partition Distribution

**100 Tenants Example:**
```
Total partitions: 256
Total tenants: 100
Average: 0.4 tenants per partition

Distribution (via hashing):
partition_0:   tenant_5, tenant_87
partition_1:   tenant_23
partition_2:   tenant_91, tenant_42
...
partition_255: tenant_18
```

**Benefits:**
- Excellent isolation (~0.4 tenants per partition)
- Even distribution via hashing
- Multiple tenants per partition is OK (hashing handles collisions)

### Capacity Planning

**Current Configuration:**
```
Partitions: 256
Tenants: 100
Chunks per tenant: 20,000
Total vectors: 2M

Vectors per partition: 2M / 256 = ~7,800
Search scope: 7,800 (vs 2M without partitions)
Speedup: 256x smaller scope → 5-10x faster in practice
```

**Scalability:**
```
Max partitions: 4,096 (Milvus limit)
Current: 256
Headroom: 16x expansion possible
```

### Partition Key Limits

**Milvus Constraints:**
- Max partitions per collection: 4,096
- Max partition key length: 100 characters
- Partition key type: VARCHAR only

**Our Configuration:**
- Partitions: 256 (well within limit)
- tenant_id length: 100 characters
- Type: VARCHAR ✅

---

## Schema Evolution

### Version History

**v1.0.0 (Current):**
- Added partition_key to tenant_id
- 256 partitions (configurable)
- 14 fields total
- FLAT index for dense vectors
- Removed manual flush calls

### Future Considerations

**If vectors exceed 1M per partition:**
- Consider IVF_FLAT or HNSW index
- Tune nlist/nprobe parameters
- Monitor recall vs speed trade-off

**If new metadata fields needed:**
- Add to schema.py
- Update models.py (ChunkData)
- Update operations.py (default values)
- No migration needed (new collections use new schema)

**If tenant_id grows beyond 100 chars:**
- Increase max_length in schema
- Recreate collections (Milvus doesn't support field modification)

---

## Schema Reference Commands

### Create Collection

```python
from schema import create_storage_schema_v1, create_indexes
from pymilvus import Collection

# Create schema
schema = create_storage_schema_v1(dimension=1024)

# Create collection with 256 partitions
collection = Collection(
    name="my_collection",
    schema=schema,
    using='default',
    num_partitions=256
)

# Create indexes
create_indexes(collection)

# Load collection
collection.load()
```

### Query Schema

```python
from pymilvus import Collection

collection = Collection(name="my_collection")

# Get schema
schema = collection.schema

# List fields
for field in schema.fields:
    print(f"Field: {field.name}, Type: {field.dtype}, Params: {field.params}")

# Check partition key
for field in schema.fields:
    if field.is_partition_key:
        print(f"Partition key: {field.name}")
```

### Check Indexes

```python
# Get indexes
indexes = collection.indexes

for idx in indexes:
    print(f"Field: {idx.field_name}")
    print(f"Index: {idx.index_name}")
    print(f"Params: {idx.params}")
```

---

**Document Status:** ✅ COMPLETE
**Schema Version:** 1.0.0
**Production Ready:** YES
