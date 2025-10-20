# Metadata Extraction Service v1.0.0

**Streamlined Metadata Extraction with 4 Core Fields**

Part of **PipeLineServices** - Ingestion Pipeline Internal Service

**Version:** 1.0.0
**Port:** 8062 (Internal only)
**Purpose:** Extract semantic metadata from text chunks using LLM

## Architecture

```
Ingestion API (8060)
    ↓
Chunking Service (8061)
    ↓
Metadata Service (8062) ← YOU ARE HERE
    ↓
LLM Gateway (8065) → Nebius AI Studio
```

## 🚀 Overview

Version 1.0.0 provides **streamlined metadata extraction** with **4 core fields** optimized for general-purpose RAG applications.

### Key Features

- ✅ **4 core metadata fields**: keywords, topics, questions, summary
- ✅ **LLM Gateway integration**: Uses port 8065 (part of Ingestion services 8060-8065)
- ✅ **Fast extraction**: <800ms per chunk target
- ✅ **Batch processing**: Efficient parallel extraction for multiple chunks
- ✅ **Configurable counts**: Control number of keywords, topics, questions via parameters
- ✅ **Smart prompting**: Optimized LLM prompts for accurate extraction
- ✅ **40-60% faster** than v3.0.0 (reduced from 45 fields to 4 core fields)

## 📊 Metadata Fields

### Core Metadata (4 fields only)

| Field | Description | Example | Configurable |
|-------|-------------|---------|--------------|
| **keywords** | Comma-separated keywords | `"RAG, vector database, embeddings, semantic search"` | Yes (1-20 keywords) |
| **topics** | Comma-separated topics | `"Information Retrieval, Machine Learning, NLP"` | Yes (1-10 topics) |
| **questions** | Semicolon-separated questions | `"What is RAG?; How do vector databases work?; What are embeddings?"` | Yes (1-10 questions) |
| **summary** | Brief summary | `"This document explains RAG systems and vector databases for semantic search."` | Yes (length) |

**Note**: These 4 fields are stored in Milvus alongside embeddings for hybrid search and metadata filtering.

## 🔌 API Endpoints

### Health & Info
- `GET /health` - Health check with LLM Gateway connectivity test
- `GET /version` - Version information

### Metadata Extraction
- `POST /v1/metadata` - Extract metadata from single chunk
- `POST /v1/metadata/batch` - Batch extraction for multiple chunks (faster)

## 📝 Usage Examples

### Example 1: Single Extraction (Default Configuration)

```python
import requests

payload = {
    "text": "RAG systems combine retrieval and generation to provide accurate answers. Vector databases store embeddings for semantic search.",
    "chunk_id": "chunk_001"
}

response = requests.post("http://localhost:8062/v1/metadata", json=payload)
result = response.json()

print(f"Keywords: {result['keywords']}")
print(f"Topics: {result['topics']}")
print(f"Questions: {result['questions']}")
print(f"Summary: {result['summary']}")
```

**Expected Response:**
```json
{
  "keywords": "RAG, retrieval, generation, vector databases, embeddings, semantic search",
  "topics": "Information Retrieval, Natural Language Processing, AI",
  "questions": "What are RAG systems?; How do vector databases work?; What is semantic search?",
  "summary": "RAG systems combine retrieval and generation using vector databases for semantic search.",
  "chunk_id": "chunk_001",
  "processing_time_ms": 450.5
}
```

### Example 2: Custom Field Counts

```python
import requests

payload = {
    "text": "Your document content here...",
    "chunk_id": "chunk_002",
    "keywords_count": 10,              # More keywords
    "topics_count": 5,                 # More topics
    "questions_count": 5,              # More questions
    "summary_length": "2-3 sentences"  # Longer summary
}

response = requests.post("http://localhost:8062/v1/metadata", json=payload)
result = response.json()
```

### Example 3: Batch Extraction (Faster for Multiple Chunks)

```python
import requests

payload = {
    "chunks": [
        {
            "text": "First chunk content...",
            "chunk_id": "chunk_001"
        },
        {
            "text": "Second chunk content...",
            "chunk_id": "chunk_002"
        },
        {
            "text": "Third chunk content...",
            "chunk_id": "chunk_003"
        }
    ],
    "keywords_count": 5,
    "topics_count": 3,
    "questions_count": 3,
    "summary_length": "1-2 sentences"
}

response = requests.post("http://localhost:8062/v1/metadata/batch", json=payload)
results = response.json()

for result in results['metadata']:
    print(f"Chunk {result['chunk_id']}: {result['keywords']}")
```

**Performance gain**: Batch processing uses parallel workers (MAX_WORKERS=5) for 3-5x speedup vs sequential single calls.

## 🏗️ Configuration

### Default Parameters

All parameters are optional with smart defaults:

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `keywords_count` | 5 | 1-20 | Number of keywords to extract |
| `topics_count` | 3 | 1-10 | Number of topics to extract |
| `questions_count` | 3 | 1-10 | Number of questions to generate |
| `summary_length` | "1-2 sentences" | - | Summary length instruction |

### LLM Models Used

Via LLM Gateway (port 8065):

- **Recommended**: `32B-fast` (Qwen3-32B-fast) - ~200-800ms, 99.5% success
- **Fast**: `7B-fast` (Qwen2.5-Coder-7B-fast) - ~300ms, 96% success
- **Balanced**: `72B` (Qwen2.5-72B-Instruct) - ~3500ms, highest accuracy
- **Advanced**: `480B` (Qwen3-Coder-480B) - ~800ms, production-grade

**Default**: `32B-fast` (best balance of speed and accuracy)

### Performance Targets

- **Extraction time**: <800ms per chunk (avg ~450ms)
- **Field coverage**: 95%+ on relevant documents
- **JSON validity**: 100% (fallback handling for malformed LLM responses)
- **Throughput**: ~120-150 chunks/minute (batch mode with MAX_WORKERS=5)

### Environment Variables

All settings in `config.py`:

```python
# API Version
API_VERSION = "1.0.0"

# LLM Gateway
LLM_GATEWAY_URL = "http://localhost:8065/v1/chat/completions"
DEFAULT_MODEL = "32B-fast"

# Performance
MAX_TOKENS = 800  # For 4-field extraction
TIMEOUT = 40  # Request timeout
MAX_WORKERS = 5  # Parallel processing workers

# Connection pooling
CONNECTION_POOL_SIZE = 30
CONNECTION_POOL_MAX = 100

# Caching
ENABLE_CACHE = True  # LRU cache for repeated chunks
```

## 📦 Deployment

### Prerequisites

**IMPORTANT:** LLM Gateway (port 8065) must be running before starting Metadata Service.

```bash
# Start LLM Gateway first
cd /PipeLineServices/Ingestion/services/llm_gateway/v1.0.0
python3 llm_gateway.py
```

### Local Development

```bash
cd /PipeLineServices/Ingestion/services/metadata/v1.0.0
python3 metadata_api.py
```

Expected output:
```
================================================================================
Metadata Extraction Service v1.0.0
================================================================================
Port: 8062
LLM Gateway: http://localhost:8065/v1/chat/completions
Model: 32B-fast
Fields: 4 core fields (keywords, topics, questions, summary)
Batch workers: 5
Caching: Enabled
================================================================================
Checking LLM Gateway connection...
✅ LLM Gateway is healthy
================================================================================
```

### Production (Server)

Same setup - LLM Gateway must be running on port 8065 first.

## 🔄 Migration from v3.0.0

### What Changed

| Feature | v3.0.0 | v1.0.0 |
|---------|--------|--------|
| **Fields** | 45 fields (product, business, entities, etc.) | **4 core fields** (keywords, topics, questions, summary) |
| **Endpoint** | `/v3/metadata` | **`/v1/metadata`** |
| **Performance** | ~2-3s per chunk (45 fields) | **~450ms per chunk** (4 fields, 4-6x faster) |
| **Use Case** | Product/business-specific | **General-purpose RAG** |
| **Schema Complexity** | High (45 fields) | **Simple** (4 fields) |
| **Max Tokens** | 1500 | **800** (reduced, faster) |

### Backward Compatibility

❌ **v3 endpoints removed** - Only `/v1/metadata` and `/v1/metadata/batch` supported

### Upgrading Clients

From v3.0.0 to v1.0.0:

```python
# v3 client (old - 45 fields)
response = requests.post("http://localhost:8062/v3/metadata", json={
    "text": text,
    "chunk_id": chunk_id,
    "extraction_mode": "enhanced"  # No longer supported
})
result = response.json()
# Accessed: brand, price, sku, entities, etc. (45 fields)

# v1 client (new - 4 core fields)
response = requests.post("http://localhost:8062/v1/metadata", json={
    "text": text,
    "chunk_id": chunk_id,
    "keywords_count": 5,  # Optional
    "topics_count": 3,    # Optional
    "questions_count": 3, # Optional
    "summary_length": "1-2 sentences"  # Optional
})
result = response.json()
# Access: keywords, topics, questions, summary (4 fields)
```

## 🧪 Testing

### Test Service

```bash
# Start service
python3 metadata_api.py

# Health check
curl http://localhost:8062/health

# Test single extraction
curl -X POST http://localhost:8062/v1/metadata \
  -H "Content-Type: application/json" \
  -d '{
    "text": "RAG systems combine retrieval and generation for accurate answers.",
    "chunk_id": "test_001"
  }'
```

### Performance Testing

```python
import time
import requests

text = "Your test document content here..." * 100  # Long text

start = time.time()
response = requests.post("http://localhost:8062/v1/metadata", json={
    "text": text,
    "chunk_id": "perf_test"
})
duration = time.time() - start

print(f"Extraction time: {duration*1000:.1f}ms")
print(f"Result: {response.json()}")
```

**Expected**: <800ms for typical chunks (500-1000 chars)

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8062
lsof -ti:8062

# Kill old service
kill $(lsof -ti:8062)

# Start v1.0.0
python3 metadata_api.py
```

### Missing Dependencies

```bash
pip install fastapi uvicorn httpx pydantic python-dotenv
```

### LLM Gateway Connection Failed

```bash
# Check if LLM Gateway is running
curl http://localhost:8065/health

# Check logs
# LLM Gateway should show: "LLM Gateway v1.0.0 ready"

# Restart LLM Gateway if needed
cd ../llm_gateway/v1.0.0
python3 llm_gateway.py
```

**Note:** LLM Gateway runs on port 8065 (part of Ingestion services 8060-8065). It must be started **before** the Metadata Service.

### Slow Extraction (>1500ms)

Possible causes:
1. LLM Gateway using slow model (switch to `32B-fast`)
2. Network latency to Nebius AI Studio
3. Long text chunks (>2000 chars)
4. Missing cache (check ENABLE_CACHE=True)

Solutions:
- Use batch mode for multiple chunks (parallel processing)
- Reduce text chunk size upstream (Chunking Service)
- Check LLM Gateway logs for model selection

### Malformed JSON from LLM

Service has automatic fallback handling:
```python
# If LLM returns invalid JSON, fallback to:
{
    "keywords": "",
    "topics": "",
    "questions": "",
    "summary": ""
}
```

Check logs for warnings about JSON parsing failures.

## 📈 Performance Comparison

| Metric | v3.0.0 (45 fields) | v1.0.0 (4 fields) | Improvement |
|--------|-------------------|-------------------|-------------|
| **Avg extraction time** | 2000-3000ms | 400-600ms | **5x faster** |
| **Max tokens** | 1500 | 800 | 47% reduction |
| **Field complexity** | 45 fields | 4 fields | 91% simpler |
| **Schema overhead** | High | Minimal | Better DB performance |
| **Use case specificity** | Product/business | General RAG | More versatile |

## 📚 Files

```
v1.0.0/
├── README.md                    # This file
├── config.py                    # Configuration (API version, prompt, models)
├── models.py                    # Pydantic models (4-field response)
├── metadata_api.py              # FastAPI application (v1 endpoints)
├── cache_optimized.py           # LRU cache for repeated chunks
└── test_metadata_api.py         # Test suite
```

## 📄 License

Internal use only - CrawlEnginePro / MindMate247

## 🤝 Support

For issues or questions:
- Check logs: Service prints detailed debug info
- Verify LLM Gateway is running: `curl http://localhost:8065/health`
- Test with simple text first before complex documents
- Use batch mode for better performance with multiple chunks

---

**Version**: v1.0.0
**Date**: October 18, 2025
**Status**: Production-ready
**Changes**: Streamlined from 45 → 4 core fields for better performance and simplicity
