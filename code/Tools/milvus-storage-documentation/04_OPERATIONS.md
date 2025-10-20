# CRUD Operations - Milvus Storage Service v1.0.0

**Last Updated:** October 9, 2025

---

## Table of Contents

1. [Operations Overview](#operations-overview)
2. [Connection Management](#connection-management)
3. [Collection Operations](#collection-operations)
4. [INSERT Operation](#insert-operation)
5. [UPDATE Operation](#update-operation)
6. [DELETE Operation](#delete-operation)
7. [Performance Optimizations](#performance-optimizations)

---

## Operations Overview

**File:** `/Users/rakesh/Desktop/CrawlEnginePro/nebius_hosting/ai_studio/hosting/PipeLineServies/Ingestion/services/storage/v1.0.0/operations.py`

**Purpose:** Complete CRUD operations for vector storage

**Supported Operations:**
- ✅ CREATE: Collection creation with automatic indexing
- ✅ READ: Query and search operations (via API)
- ✅ UPDATE: Modify existing chunks (delete + re-insert)
- ✅ DELETE: Remove chunks by filter

---

## Connection Management

### Connect to Milvus

```python
def connect_to_milvus():
    """Connect to Milvus server"""
    try:
        connections.connect(
            alias="default",
            host=config.MILVUS_HOST,
            port=config.MILVUS_PORT,
            user=config.MILVUS_USER,
            password=config.MILVUS_PASSWORD,
            timeout=config.REQUEST_TIMEOUT
        )
        print(f"✓ Connected to Milvus at {config.MILVUS_HOST}:{config.MILVUS_PORT}")
        return True
    except Exception as e:
        print(f"✗ Failed to connect to Milvus: {e}")
        return False
```

**Configuration:**
- Host/Port: From config.py (environment-aware)
- Authentication: Username/password from .env
- Timeout: 30 seconds (configurable)

**Connection Pooling:**
- Pool size: 10 connections (config.CONNECTION_POOL_SIZE)
- Reused across requests

### Disconnect

```python
def disconnect_from_milvus():
    """Disconnect from Milvus"""
    try:
        connections.disconnect(alias="default")
        print("✓ Disconnected from Milvus")
    except Exception as e:
        print(f"⚠ Warning during disconnect: {e}")
```

### Check Connection

```python
def check_connection() -> bool:
    """Check if Milvus connection is alive"""
    try:
        collections = utility.list_collections()
        return True
    except Exception as e:
        print(f"✗ Milvus connection check failed: {e}")
        return False
```

---

## Collection Operations

### Create Collection

**Function:** `create_collection(collection_name: str, dimension: int = 4096)`

**Process:**
1. Check if collection exists (return error if yes)
2. Create schema with v1.0.0 structure
3. Create collection with 256 partitions
4. Create indexes (FLAT, SPARSE_INVERTED_INDEX, STL_SORT)
5. Load collection
6. Return success status

**Example:**
```python
result = create_collection("my_collection", dimension=1024)

# Success response:
{
    "success": True,
    "collection_name": "my_collection",
    "fields_count": 14,
    "dimension": 1024
}
```

**Console Output:**
```
✓ Collection 'my_collection' created with 14 fields (256 partitions)
✓ Created dense vector index (FLAT, IP)
✓ Created scalar index on 'document_id'
✅ All indexes created successfully
✓ Collection 'my_collection' loaded
```

**Timing:** ~1-2 seconds (empty collection)

### Get Collection

**Function:** `get_collection(collection_name: str)`

```python
collection = get_collection("my_collection")

if collection:
    print(f"Collection found: {collection.name}")
else:
    print("Collection not found")
```

### Delete Collection

**Function:** `delete_collection(collection_name: str)`

**Warning:** Permanently deletes ALL data in collection

```python
result = delete_collection("my_collection")

# Success response:
{
    "success": True,
    "collection_name": "my_collection",
    "message": "Collection deleted successfully"
}
```

### Get Collection Info

**Function:** `get_collection_info(collection_name: str)`

**Returns:**
- Schema (all fields)
- Entity count
- Indexes

```python
info = get_collection_info("my_collection")

print(f"Entities: {info['num_entities']}")
print(f"Fields: {len(info['schema']['fields'])}")
```

---

## INSERT Operation

### Function Signature

```python
def insert_chunks(
    collection_name: str,
    chunks: List[ChunkData],
    create_if_not_exists: bool = True
) -> Dict[str, Any]
```

### Process Flow

1. **Check Collection Existence**
   ```python
   if not utility.has_collection(collection_name):
       if create_if_not_exists:
           create_collection(collection_name)
       else:
           return error
   ```

2. **Prepare Data (Column Format)**
   ```python
   data = prepare_insert_data(chunks)
   # Converts List[ChunkData] → List[List[values]] (column-oriented)
   ```

3. **Insert into Milvus**
   ```python
   insert_result = collection.insert(data)
   ```

4. **NO MANUAL FLUSH** ⚠️
   ```python
   # REMOVED: collection.flush()  # Saves 10+ seconds!
   # Milvus auto-flushes periodically (1s interval)
   ```

5. **Return Result**
   ```python
   return {
       "success": True,
       "inserted_count": len(chunks),
       "chunk_ids": [chunk.id for chunk in chunks],
       "collection_name": collection_name,
       "processing_time_ms": processing_time
   }
   ```

### Data Preparation

**Function:** `prepare_insert_data(chunks: List[ChunkData])`

**Converts:** Row format → Column format

```python
# Input (row format):
[
    ChunkData(id="1", text="Hello", ...),
    ChunkData(id="2", text="World", ...)
]

# Output (column format):
[
    ["1", "2"],           # id column
    ["Hello", "World"],   # text column
    [...],                # other columns
]
```

**Why column format?**
- Milvus requirement for batch insert
- Better compression and performance

### Default Values

**Function:** `get_default_value(field_name: str)`

**Defaults if field missing:**
```python
"dense_vector": [0.0] * 1024
"price", "amount", "tax_amount": 0.0
"year", "chunk_index", "char_count", "token_count": 0
All other fields: ""
```

### Performance

**Genesis (268 chunks):**
- First insert (creates collection): ~11-12s
- Subsequent inserts (partition only): ~1-2s
- NO flush overhead (removed blocking call)

**Parallel Inserts:**
- 3 documents, shared collection, different tenants
- Sequential: 26.69s
- Parallel: 14.75s
- Speedup: 1.81x (46.9% faster)

---

## UPDATE Operation

### Function Signature

```python
def update_chunks(
    collection_name: str,
    filter_expr: str,
    updates: Dict[str, Any],
    tenant_id: Optional[str] = None
) -> Dict[str, Any]
```

### Process Flow

**Milvus Limitation:** No native UPDATE command

**Workaround:**
1. Query entities matching filter
2. Modify fields in memory
3. Delete old entities
4. Insert updated entities

**Code:**
```python
# 1. Query
results = collection.query(
    expr=filter_expr,
    output_fields=["*"]
)

# 2. Modify
for entity in results:
    for field, value in updates.items():
        entity[field] = value
    entity["updated_at"] = datetime.utcnow().isoformat()

# 3. Delete
ids_to_delete = [entity["id"] for entity in results]
collection.delete(f"id in {ids_to_delete}")

# 4. Re-insert
chunks = [ChunkData(**entity) for entity in results]
insert_chunks(collection_name, chunks)
```

### Tenant Isolation

**Optional tenant filter:**
```python
if tenant_id:
    filter_expr = f"({filter_expr}) and tenant_id == '{tenant_id}'"
```

**Example:**
```python
# Update all chunks from document "doc123" for tenant "tenant_1"
result = update_chunks(
    collection_name="my_collection",
    filter_expr='document_id == "doc123"',
    updates={"text": "Updated text"},
    tenant_id="tenant_1"
)
```

### Response

```python
{
    "success": True,
    "updated_count": 50,
    "collection_name": "my_collection",
    "processing_time_ms": 1234.56
}
```

---

## DELETE Operation

### Function Signature

```python
def delete_chunks(
    collection_name: str,
    filter_expr: str,
    tenant_id: Optional[str] = None
) -> Dict[str, Any]
```

### Process Flow

1. **Query to count entities**
   ```python
   results = collection.query(
       expr=filter_expr,
       output_fields=["id"],
       limit=10000
   )
   count_before = len(results)
   ```

2. **Delete by expression**
   ```python
   collection.delete(filter_expr)
   ```

3. **Flush** (yes, we flush for deletes)
   ```python
   collection.flush()
   ```

**Why flush for delete but not insert?**
- Deletes must be guaranteed (data consistency)
- Inserts can be eventually consistent (performance)

### Tenant Isolation

```python
if tenant_id:
    filter_expr = f"({filter_expr}) and tenant_id == '{tenant_id}'"
```

### Examples

**Delete all chunks from document:**
```python
result = delete_chunks(
    collection_name="my_collection",
    filter_expr='document_id == "doc123"'
)
```

**Delete by tenant:**
```python
result = delete_chunks(
    collection_name="my_collection",
    filter_expr='tenant_id == "tenant_1"'
)
```

**Delete specific chunks:**
```python
result = delete_chunks(
    collection_name="my_collection",
    filter_expr='id in ["chunk1", "chunk2", "chunk3"]'
)
```

### Response

```python
{
    "success": True,
    "deleted_count": 100,
    "collection_name": "my_collection",
    "processing_time_ms": 234.56
}
```

---

## Performance Optimizations

### 1. Removed Blocking Flush (INSERT)

**Old Code (REMOVED):**
```python
insert_result = collection.insert(data)
collection.flush()  # ❌ Blocks for 10+ seconds
```

**New Code (OPTIMIZED):**
```python
insert_result = collection.insert(data)
# ✅ No flush! Milvus auto-flushes periodically (1s interval)
# Data is queryable immediately without manual flush
```

**Performance Gain:**
- Saves 10+ seconds per insert
- Non-blocking operation
- Data available within 1 second automatically

### 2. FLAT Index (Zero Build Time)

**Configuration:**
```python
DENSE_INDEX_TYPE = "FLAT"  # Not IVF_FLAT
```

**Benefits:**
- Zero index build time
- 100% recall (exact search)
- Faster for collections <1M vectors
- No quantization loss

**Trade-off:**
- Higher memory usage (acceptable for our scale)
- Brute-force search (fast enough for partitioned data)

### 3. Partition Key Optimization

**Feature:** tenant_id as partition_key

**Benefits:**
- Automatic partition assignment via hashing
- Search only relevant partition (not all 256)
- 5-10x faster retrieval

**Example:**
```
Without partition key: Search 2M vectors
With partition key:    Search ~7,800 vectors (one partition)
```

### 4. Connection Pooling

**Configuration:**
```python
CONNECTION_POOL_SIZE = 10
```

**Benefits:**
- Reuse connections across requests
- Reduced connection overhead
- Better throughput

---

## Error Handling

### Common Errors

**1. Collection Already Exists**
```python
{
    "success": False,
    "error": "Collection already exists",
    "collection_name": "my_collection"
}
```

**2. Collection Not Found**
```python
{
    "success": False,
    "error": "Collection not found"
}
```

**3. Insert Failure**
```python
{
    "success": False,
    "error": "Error details...",
    "collection_name": "my_collection",
    "processing_time_ms": 1234.56
}
```

### Error Logging

**All operations log errors:**
```python
try:
    # ... operation ...
except Exception as e:
    error_details = traceback.format_exc()
    print(f"✗ Operation failed: {e}")
    print(f"Error details:\n{error_details}")
    return {
        "success": False,
        "error": f"{str(e)} | Details: {error_details[:500]}"
    }
```

---

## Testing Operations

### Test Insert

```python
from models import ChunkData
from operations import insert_chunks

chunks = [
    ChunkData(
        id="test_chunk_1",
        document_id="test_doc",
        tenant_id="test_tenant",
        text="Test chunk text",
        chunk_index=0,
        char_count=15,
        token_count=3,
        dense_vector=[0.0] * 1024,
        sparse_vector={},
        price=0.0,
        amount=0.0,
        tax_amount=0.0,
        year=2025,
        created_at="2025-10-09T13:18:34"
    )
]

result = insert_chunks("test_collection", chunks)
print(result)
```

### Test Delete

```python
result = delete_chunks(
    collection_name="test_collection",
    filter_expr='document_id == "test_doc"'
)
print(f"Deleted {result['deleted_count']} chunks")
```

---

**Document Status:** ✅ COMPLETE
**Operations Tested:** YES
**Production Ready:** YES
