# Milvus Storage Service v1.0.0

**Complete CRUD API for vector storage with multi-tenancy support**

Part of **PipeLineServices** - Ingestion Pipeline Internal Service

## Overview

Dedicated service for all Milvus operations with:
- ✅ **Full CRUD operations** (Create, Read, Update, Delete)
- ✅ **Multi-tenancy** support via `tenant_id` field
- ✅ **Dense vector search** (semantic similarity)
- ✅ **Automatic dimension detection** - Collections auto-size for embedding dimensions
- ✅ **14-field schema** with base metadata (keywords, topics, questions, summary)
- ✅ **Independent service** - No direct Milvus access from other services
- ✅ **REST API** - Standard HTTP endpoints for all operations
- ✅ **Environment-aware** - Supports development & production modes

## Architecture

```
Ingestion API (8060)
    ↓
Chunking Service (8061)
    ↓
Storage Service (8064) ← YOU ARE HERE
    ↓
Milvus Database (19530)
```

## Port

- **8064** - Internal service (localhost only, blocked from external access)
- Configured via `.env`: `STORAGE_SERVICE_PORT=8064`

## Endpoints

### Health & Version
- `GET /health` - Health check with Milvus status
- `GET /version` - Service version and endpoints list

### CRUD Operations
- `POST /v1/insert` - Insert chunks with metadata
- `POST /v1/update` - Update specific fields
- `POST /v1/delete` - Delete chunks by filter
- `DELETE /v1/delete/{chunk_id}` - Delete single chunk
- `POST /v1/search` - Hybrid search with filtering

### Collection Management
- `POST /v1/collection/create` - Create new collection
- `GET /v1/collection/{name}` - Get collection info
- `DELETE /v1/collection/{name}` - Delete collection
- `GET /v1/collections` - List all collections

## Multi-Tenancy

All operations support tenant isolation via `tenant_id` field:

```json
{
    "collection_name": "shared_collection_v3",
    "filter": "brand == 'Apple'",
    "tenant_id": "client_acme"  // Only returns client_acme data
}
```

**Best Practices:**
1. **Collection per tenant**: `client_acme_products_v3`, `client_beta_docs_v3`
2. **Shared collection with tenant_id**: Single collection, filter by `tenant_id`

## Schema (14 Fields)

### Core Fields (9)
- `id` (PRIMARY KEY)
- `document_id`
- `chunk_index`
- `text` (max 65K chars)
- `tenant_id` (multi-tenancy)
- `created_at`, `updated_at`
- `char_count`, `token_count`

### Vectors (1)
- `dense_vector` [dynamic] - Semantic similarity (auto-detected from chunk data: 1024 or 4096)

### Base Metadata (4 fields)
- `keywords` - Extracted keywords
- `topics` - Document topics
- `questions` - Related questions
- `summary` - Chunk summary

## Usage Examples

### 1. Insert Chunks

```python
import httpx

chunks_data = {
    "collection_name": "client_acme_products_v3",
    "chunks": [
        {
            "id": "chunk_001",
            "document_id": "doc_123",
            "chunk_index": 0,
            "text": "Apple iPhone 15 Pro features titanium design and A17 Pro chip.",
            "tenant_id": "client_acme",
            "dense_vector": [0.1, 0.2, ...],  # 1024/2048/3584/4096 floats (auto-detected)
            "keywords": "iPhone, Apple, smartphone, titanium, A17 Pro",
            "topics": "Smartphones, Apple Products, Technology",
            "questions": "What are iPhone 15 Pro features?; What chip does iPhone 15 Pro have?",
            "summary": "Apple iPhone 15 Pro features titanium design and advanced A17 Pro chip."
        }
    ],
    "create_collection": true
}

response = httpx.post("http://localhost:8064/v1/insert", json=chunks_data)
print(response.json())
# {"success": true, "inserted_count": 1, "chunk_ids": ["chunk_001"], ...}
```

### 2. Update Price (Product Info Changed)

```python
update_data = {
    "collection_name": "client_acme_products_v3",
    "filter": "sku == 'IPHONE-15-PRO'",
    "updates": {
        "price": 899.0,
        "sale_price": 799.0
    },
    "tenant_id": "client_acme"
}

response = httpx.post("http://localhost:8064/v1/update", json=update_data)
print(response.json())
# {"success": true, "updated_count": 5, ...}
```

### 3. Vector Search

```python
search_data = {
    "collection_name": "client_acme_products_v3",
    "query_dense": [0.1, 0.2, ...],  # From embeddings service (4096 dims)
    "filter": "brand == 'Apple' and price < 1000",
    "tenant_id": "client_acme",
    "limit": 20
}

response = httpx.post("http://localhost:8064/v1/search", json=search_data)
results = response.json()
# {"success": true, "results": [...], "total_results": 15, ...}
```

### 4. Delete Document

```python
delete_data = {
    "collection_name": "client_acme_products_v3",
    "filter": "document_id == 'doc_obsolete_123'",
    "tenant_id": "client_acme"
}

response = httpx.post("http://localhost:8064/v1/delete", json=delete_data)
print(response.json())
# {"success": true, "deleted_count": 10, ...}
```

## Installation

### 1. Install Dependencies

```bash
cd services/milvus_storage/v1.0.0
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Milvus connection details
```

### 3. Run Service

```bash
python storage_api.py
# Service starts on port 8064
```

### 4. Test Health

```bash
curl http://localhost:8064/health
```

## Systemd Service (Production)

```bash
sudo nano /etc/systemd/system/milvus-storage.service
```

```ini
[Unit]
Description=Milvus Storage Service v1.0.0
After=network.target docker.service

[Service]
Type=simple
User=reku631
WorkingDirectory=/home/reku631/services/milvus_storage/v1.0.0
Environment="PATH=/home/reku631/venvs/milvus_storage/bin"
ExecStart=/home/reku631/venvs/milvus_storage/bin/python storage_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable milvus-storage
sudo systemctl start milvus-storage
sudo systemctl status milvus-storage
```

## APISIX Route Configuration

```bash
# Add route for external access via https://storage.mindmate247.com
curl http://localhost:9080/apisix/admin/routes/milvus_storage -X PUT -d '
{
    "uri": "/v1/*",
    "name": "milvus_storage_route",
    "methods": ["GET", "POST", "PUT", "DELETE"],
    "upstream": {
        "type": "roundrobin",
        "nodes": {
            "127.0.0.1:8064": 1
        }
    },
    "plugins": {
        "key-auth": {},
        "limit-count": {
            "count": 1000,
            "time_window": 60,
            "rejected_code": 429
        }
    }
}' -H 'X-API-KEY: your-apisix-admin-key'
```

## Integration with Chunking v1.0.0

Chunking v1.0.0 calls Milvus Storage directly (no APISIX):

```python
# In chunking_orchestrator.py v1.0.0

import httpx

# After getting metadata + embeddings
chunks_data = prepare_chunks_for_storage(chunks, metadata, embeddings)

# Call Milvus Storage Service (direct localhost)
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8064/v1/insert",
        json={
            "collection_name": request.collection_name,
            "chunks": chunks_data
        },
        timeout=30.0
    )

result = response.json()
if not result["success"]:
    raise Exception(f"Storage failed: {result['error']}")
```

## Security

- ✅ **Security middleware** blocks external internet access
- ✅ **Only allows localhost** and internal network (172.*, 10.*, 192.168.*)
- ✅ **APISIX authentication** for external API access
- ✅ **Tenant isolation** via tenant_id filtering

## Performance

- **Insert**: ~45-100ms per chunk (including index updates)
- **Search**: <100ms for 100K records, <200ms for 1M records
- **Update**: Query + Delete + Insert (slower, use sparingly)
- **Delete**: ~20-50ms for filter-based deletion

## Monitoring

```bash
# Health check
curl http://localhost:8064/health

# Version
curl http://localhost:8064/version

# List collections
curl http://localhost:8064/v1/collections

# Collection info
curl http://localhost:8064/v1/collection/client_acme_products_v3
```

## API Documentation

Interactive API docs:
- Swagger UI: http://localhost:8064/docs
- ReDoc: http://localhost:8064/redoc

## Troubleshooting

### Connection Failed
```bash
# Check Milvus is running
docker ps | grep milvus

# Check Milvus port
netstat -tulpn | grep 19530

# Test Milvus connection
python -c "from pymilvus import connections; connections.connect('default', 'localhost', '19530'); print('Connected')"
```

### Collection Not Found
```bash
# List all collections
curl http://localhost:8064/v1/collections
```

### Slow Inserts
- Check if indexes are created: `GET /v1/collection/{name}`
- Batch inserts (100-1000 chunks per request)
- Consider disabling auto-flush for bulk inserts

## Version History

- **v1.0.0** (2025-10-18): Production release
  - Complete CRUD operations
  - Multi-tenancy support
  - **Automatic dimension detection** from chunk vectors (1024/2048/3584/4096 dims for multi-provider support)
  - Dense vector search with dynamic dimensions (Jina/Nebius/SambaNova)
  - 14-field schema with 4 core metadata fields (keywords, topics, questions, summary)
  - Independent service architecture (no direct Milvus access from other services)
  - Full parameter control from Ingestion API
  - **Bug Fix**: Collections now auto-size based on actual embedding dimensions (operations.py:240-246)
