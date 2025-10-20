# Metadata Extraction Service v1.0.0

Extract semantic metadata from text using LLM for RAG applications.

## Features

- **7 Semantic Fields**: keywords, topics, questions, summary, semantic_keywords, entity_relationships, attributes
- **Optimized for RAG**: Fields designed for vector search and retrieval
- **Fast**: ~2-3s per chunk with Llama 70B
- **Semantic Expansion**: Automatic synonym and relationship extraction
- **Structured Attributes**: Key-value pairs for filtering
- **Batch Processing**: Process multiple chunks in parallel
- **Caching**: Optional response caching for repeated queries
- **Async**: Non-blocking FastAPI with connection pooling

## Quick Start

```bash
# Start service
PORT=8072 python3 metadata_api.py

# Test
curl -X POST http://localhost:8072/v1/metadata \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Apple iPhone 15 Pro Max by Apple Inc. Price: $1199",
    "chunk_id": "chunk_001"
  }'
```

## API Endpoints

### POST `/v1/metadata`
Extract metadata from single text chunk.

**Request:**
```json
{
  "text": "Your text here",
  "chunk_id": "optional_id",
  "keywords_count": "5",
  "topics_count": "3",
  "questions_count": "3",
  "summary_length": "1-2 sentences"
}
```

**Response (7 fields):**
```json
{
  "keywords": "Apple iPhone 15 Pro Max, Apple Inc., $1199",
  "topics": "Electronics, Smartphones, Technology",
  "questions": "What is the price?|What are the features?",
  "summary": "The Apple iPhone 15 Pro Max is a premium smartphone...",
  "semantic_keywords": "mobile device, iOS device, premium phone",
  "entity_relationships": "Apple Inc. → manufacturer-of → iPhone 15 Pro Max",
  "attributes": "brand: Apple, price: 1199, currency: USD",
  "chunk_id": "chunk_001",
  "model_used": "72B-base",
  "processing_time_ms": 2847.3,
  "api_version": "1.0.0"
}
```

### POST `/v1/metadata/batch`
Process multiple chunks in parallel.

**Request:**
```json
{
  "chunks": [
    {"text": "Text 1", "chunk_id": "chunk_001"},
    {"text": "Text 2", "chunk_id": "chunk_002"}
  ]
}
```

### GET `/health`
Health check with cache statistics.

### GET `/version`
Service version and available endpoints.

### GET `/models`
List available LLM models.

## Field Descriptions

| Field | Description | Use Case |
|-------|-------------|----------|
| **keywords** | Exact terms from text (names, SKUs, dates, payment info) | Exact match search |
| **topics** | High-level categories | Filtering, grouping |
| **questions** | Answerable questions from text | Q&A systems |
| **summary** | 1-2 sentence summary | Previews, snippets |
| **semantic_keywords** | Synonyms, industry terms, expansions | Semantic search |
| **entity_relationships** | Entity → relationship → Entity triplets | Knowledge graphs |
| **attributes** | key: value pairs | Faceted search, filters |

## Configuration

Environment variables (`.env` file):
```bash
# Service
PORT=8072
HOST=0.0.0.0

# LLM Gateway
LLM_GATEWAY_URL=http://localhost:8075/v1/chat/completions

# Caching
ENABLE_CACHING=false
CACHE_TTL=7200
CACHE_MAX_SIZE=10000

# Performance
MAX_PARALLEL_LLM_CALLS=20
```

## Model Selection

Available models (configured in shared/model_registry.py):
- **FAST**: 7B model, ~300ms per chunk
- **BALANCED**: 70B model, ~2-3s per chunk (default)
- **ADVANCED**: 480B model, ~800ms per chunk

Change via request:
```json
{
  "text": "...",
  "model": "fast"
}
```

## Performance

| Metric | Value |
|--------|-------|
| Throughput | ~20-30 chunks/sec (batch mode) |
| Latency | 2-3s per chunk (70B model) |
| Concurrency | 20 parallel LLM calls |
| Cache hit rate | 60-80% (when enabled) |

## Architecture

```
Client Request
    ↓
FastAPI (metadata_api.py)
    ↓
extract_metadata() → LLM Gateway → Llama 70B
    ↓
MetadataResponse (7 fields)
    ↓
Client
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn metadata_api:app --reload --port 8072

# Run tests
curl http://localhost:8072/health

# Clear cache
curl -X POST http://localhost:8072/cache/clear
```

## Integration

Used by:
- Chunking Orchestrator (port 8071) - calls `/v1/metadata`
- Storage Service (port 8074) - stores 7 fields in Milvus

Configuration in `/code/.env`:
```bash
METADATA_SERVICE_URL=http://localhost:8072/v1/metadata
```

## Troubleshooting

**Service won't start:**
- Check LLM Gateway is running on port 8075
- Verify .env file exists 4 levels up
- Check port 8072 is not in use

**Slow responses:**
- Use `"model": "fast"` for 7B model
- Enable caching with `ENABLE_CACHING=true`
- Reduce `MAX_PARALLEL_LLM_CALLS` if hitting rate limits

**Empty fields:**
- Text must be > 50 characters
- Check LLM Gateway logs for errors
- Verify JSON response is valid

## Version History

- **v1.0.0** (2025-10-20): Simplified to 7 fields optimized for RAG

## License

Part of CrawlEnginePro RAG Pipeline
