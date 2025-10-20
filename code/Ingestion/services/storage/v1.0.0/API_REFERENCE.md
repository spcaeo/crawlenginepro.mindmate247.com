# Storage Service API Reference v1.0.0

Quick reference for common Storage Service operations.

## Health & Status

### Health Check
```bash
curl -s http://localhost:8074/health | jq '{status, milvus_connected, collections_count}'
```

Response:
```json
{
  "status": "healthy",
  "milvus_connected": true,
  "collections_count": 1
}
```

### Version Info
```bash
curl -s http://localhost:8074/version
```

## Collection Management

### List All Collections
```bash
curl -s http://localhost:8074/v1/collections | jq .
```

Response:
```json
{
  "success": true,
  "collections": ["test_collection"],
  "total_count": 1
}
```

### Get Collection Info
```bash
curl -s http://localhost:8074/v1/collection/{collection_name} | jq .
```

Response includes:
- `schema`: Field definitions with types and parameters
- `num_entities`: Total document count
- `indexes`: Index configurations

### Create Collection
```bash
curl -X POST http://localhost:8074/v1/collection/create \
  -H 'Content-Type: application/json' \
  -d '{
    "collection_name": "my_collection",
    "dimension": 1024,
    "description": "My collection"
  }'
```

### Delete Collection
```bash
curl -X DELETE http://localhost:8074/v1/collection/{collection_name}
```

## Data Operations

### Search (Hybrid)
```bash
curl -X POST http://localhost:8074/v1/search \
  -H 'Content-Type: application/json' \
  -d '{
    "collection_name": "test_collection",
    "query_dense": [0.1, 0.2, ...],
    "limit": 20,
    "output_fields": ["id", "text", "keywords", "topics"],
    "search_mode": "hybrid"
  }'
```

### Insert Chunks
```bash
curl -X POST http://localhost:8074/v1/insert \
  -H 'Content-Type: application/json' \
  -d '{
    "collection_name": "test_collection",
    "chunks": [
      {
        "id": "chunk_001",
        "document_id": "doc_123",
        "text": "Sample text",
        "dense_vector": [...],
        "tenant_id": "client_123"
      }
    ]
  }'
```

### Update Chunks
```bash
curl -X POST http://localhost:8074/v1/update \
  -H 'Content-Type: application/json' \
  -d '{
    "collection_name": "test_collection",
    "filter": "document_id == \"doc_123\"",
    "updates": {"price": 99.99}
  }'
```

### Delete Chunks
```bash
curl -X POST http://localhost:8074/v1/delete \
  -H 'Content-Type: application/json' \
  -d '{
    "collection_name": "test_collection",
    "filter": "document_id == \"doc_123\""
  }'
```

### Delete by ID
```bash
curl -X DELETE "http://localhost:8074/v1/delete/{chunk_id}?collection_name=test_collection"
```

## Common Filters

Multi-field filter:
```
brand == 'Apple' and price < 1000
```

Tenant isolation:
```
tenant_id == 'client_acme'
```

Document filter:
```
document_id == 'doc_123'
```

## Output Fields

Common fields to request in searches:
- Core: `id`, `document_id`, `chunk_index`, `text`
- Metadata: `keywords`, `topics`, `questions`, `summary`
- Stats: `char_count`, `token_count`
- Tenant: `tenant_id`
- Timestamps: `created_at`, `updated_at`

## Tips

1. **Always check health first**: `GET /health` returns `milvus_connected` status
2. **List collections before querying**: `GET /v1/collections`
3. **Get schema before insert**: `GET /v1/collection/{name}` shows required fields
4. **Use correct endpoint paths**:
   - Collections list: `/v1/collections` (plural)
   - Collection info: `/v1/collection/{name}` (singular)
