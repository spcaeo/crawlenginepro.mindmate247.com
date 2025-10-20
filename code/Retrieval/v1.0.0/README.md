# Retrieval Pipeline API v1.0.0

**Complete RAG retrieval orchestrator with intent-aware answer generation**

Part of **PipeLineServices** - Retrieval Pipeline Main API

## Overview

Multi-stage RAG retrieval pipeline that combines vector search, intelligent reranking, optional compression, and intent-aware answer generation for optimal retrieval quality and speed.

### Key Features

- ✅ **Intent Detection** - Automatic query classification and prompt adaptation
- ✅ **Dense Vector Search** - Semantic similarity with metadata boosting (4 metadata fields)
- ✅ **Cross-Encoder Reranking** - BGE-Reranker-v2-M3 or Jina AI reranker
- ✅ **LLM Compression** - Optional contextual compression (disabled by default for speed)
- ✅ **Answer Generation** - Multi-model support with citations
- ✅ **Speed-Optimized Defaults** - Configured for <2s retrieval (10 → 3 → 3 pipeline)
- ✅ **Full Parameter Control** - All parameters user-configurable via API
- ✅ **Multi-Tenancy** - Isolated data access per tenant

## Architecture

```
Query
  ↓
┌─────────────────────────────────────┐
│  Intent Detection (parallel)        │  (LLM-based classification)
│  - Detects query type               │
│  - Recommends model                 │
│  - Adapts system prompt             │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│  Stage 1: Search (8071)             │  (~50-100ms)
│  - Dense vector search              │
│  - Metadata boost (4 fields)        │
│  - Default: 10 results              │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│  Stage 2: Reranking (8072)          │  (~100-300ms)
│  - Cross-encoder scoring            │
│  - BGE-Reranker-v2-M3               │
│  - Default: Top 3 results           │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│  Stage 3: Compression (8073)        │  (~1-3s, DISABLED by default)
│  - LLM-powered extraction           │
│  - Relevance filtering              │
│  - Optional stage                   │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│  Stage 4: Answer Generation (8074)  │  (~500-2000ms)
│  - Intent-adapted prompts           │
│  - Multi-model support              │
│  - Citation extraction              │
│  - Default: 3 context chunks        │
└─────────────────────────────────────┘
  ↓
Answer + Citations
```

## Port

- **8070** - Main Retrieval API (this service)
- **Internal Services**: 8071-8075 (search, rerank, compress, answer, intent)

## Performance Characteristics

**Speed-Optimized Pipeline (Default: compression disabled)**

| Configuration | Search | Rerank | Answer | **Total** |
|--------------|--------|--------|--------|---------|
| **Default (10→3→3)** | 50-100ms | 100-300ms | 500-2000ms | **<2.5s** |
| With Compression (10→3→3) | 50-100ms | 100-300ms | 1-3s | 3-5s |
| High Quality (20→10→5) | 100-200ms | 300-500ms | 1-3s | 2-4s |

**Pipeline Stages:**
- Search retrieves: **10 chunks** (default)
- Reranking keeps: **3 chunks** (default)
- Answer uses: **3 chunks** (default)
- Compression: **DISABLED** by default (enable with `enable_compression: true`)

## API Parameters

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | User query/question (3-1000 chars) |
| `collection_name` | string | Milvus collection name |

### Optional Pipeline Parameters

#### Search Stage

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `search_top_k` | int | **10** | 1-100 | Chunks to retrieve in search stage |
| `use_metadata_boost` | bool | `true` | - | Enable metadata boosting |

#### Reranking Stage

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `enable_reranking` | bool | `true` | - | Enable reranking stage |
| `rerank_top_k` | int | **3** | 1-50 | Chunks to keep after reranking |

#### Compression Stage

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `enable_compression` | bool | **false** | - | Enable compression stage |
| `compression_ratio` | float | `0.5` | 0.0-1.0 | Compression ratio (0.5 = keep 50%) |
| `score_threshold` | float | `0.3` | 0.0-1.0 | Min relevance score for compression |

#### Answer Generation Stage

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `max_context_chunks` | int | **3** | 1-20 | Max chunks in answer context |
| `model` | string | `Llama-3.3-70B-Instruct-fast` | - | LLM model for answer generation |
| `temperature` | float | `0.3` | 0.0-1.0 | LLM temperature |
| `enable_citations` | bool | `true` | - | Include source citations |

#### Multi-Tenancy

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tenant_id` | string | `"default"` | Tenant ID for data isolation |

## Usage Examples

### Example 1: Simple Retrieval (All Defaults)

Speed-optimized with compression disabled:

```python
import httpx

query_data = {
    "query": "What damage did vajra cause to Hanuman?",
    "collection_name": "ramayana_knowledge_v1"
}

response = httpx.post("http://localhost:8070/v1/retrieve", json=query_data)
result = response.json()

print(f"Answer: {result['answer']}")
print(f"Total time: {result['total_time_ms']:.0f}ms")
print(f"Pipeline: {result['search_results_count']} → {result['reranked_count']} → {result['context_count']} chunks")
```

**Expected Output:**
```json
{
  "success": true,
  "answer": "The vajra struck Hanuman's jaw, causing him to fall unconscious. [Source 1]",
  "citations": [
    {
      "source_id": 1,
      "chunk_id": "doc1_chunk5",
      "document_id": "ramayana_v1",
      "text_snippet": "The vajra struck Hanuman's jaw..."
    }
  ],
  "total_time_ms": 1850,
  "search_results_count": 10,
  "reranked_count": 3,
  "context_count": 3,
  "stages": {
    "search": {"time_ms": 85, "success": true},
    "reranking": {"time_ms": 245, "success": true},
    "compression": {"time_ms": 0, "skipped": true},
    "answer_generation": {"time_ms": 1520, "success": true}
  }
}
```

### Example 2: High-Quality Retrieval (More Context)

Increase search and rerank for better quality:

```python
query_data = {
    "query": "Compare the features of iPhone 15 Pro and iPhone 15 Pro Max",
    "collection_name": "product_catalog_v1",
    "search_top_k": 20,  # More search results
    "rerank_top_k": 10,  # More reranked chunks
    "max_context_chunks": 5,  # More context for answer
    "tenant_id": "client_apple"
}

response = httpx.post("http://localhost:8070/v1/retrieve", json=query_data)
```

**Performance**: ~2-3s (vs 1.5-2s with defaults)

### Example 3: With Compression (Quality-Focused)

Enable compression for cleaner context:

```python
query_data = {
    "query": "Explain the technical specifications of the MacBook Pro M3",
    "collection_name": "tech_docs_v1",
    "enable_compression": True,  # Enable compression
    "compression_ratio": 0.4,    # Compress to 40% of original
    "score_threshold": 0.5       # Higher relevance threshold
}

response = httpx.post("http://localhost:8070/v1/retrieve", json=query_data)
```

**Performance**: ~3-5s (compression adds 1-3s)

### Example 4: Speed-Focused (Minimal Context)

Ultra-fast retrieval with minimal context:

```python
query_data = {
    "query": "What is RAG?",
    "collection_name": "qa_knowledge_v1",
    "search_top_k": 5,           # Fewer search results
    "rerank_top_k": 2,           # Minimal reranking
    "max_context_chunks": 1,     # Single chunk
    "enable_reranking": False    # Skip reranking for speed
}

response = httpx.post("http://localhost:8070/v1/retrieve", json=query_data)
```

**Performance**: <1s (fastest possible)

### Example 5: Custom LLM Model

Use different LLM model for answer generation:

```python
query_data = {
    "query": "Write a detailed comparison of vector databases",
    "collection_name": "technical_articles_v1",
    "model": "Qwen2.5-72B-Instruct",  # Different model
    "temperature": 0.7                 # More creative
}

response = httpx.post("http://localhost:8070/v1/retrieve", json=query_data)
```

### Example 6: Multi-Tenant Retrieval

Isolate data by tenant:

```python
# Client A retrieval
query_data_a = {
    "query": "Show me product inventory",
    "collection_name": "shared_products_v1",
    "tenant_id": "client_acme"  # Only ACME's data
}

# Client B retrieval (same collection, different data)
query_data_b = {
    "query": "Show me product inventory",
    "collection_name": "shared_products_v1",
    "tenant_id": "client_beta"  # Only Beta's data
}
```

### Example 7: No Citations (Faster Response)

Disable citations for slight speed gain:

```python
query_data = {
    "query": "Summarize the document",
    "collection_name": "documents_v1",
    "enable_citations": False  # No citation extraction
}

response = httpx.post("http://localhost:8070/v1/retrieve", json=query_data)
# Result will not include 'citations' field
```

## Response Format

```json
{
  "success": true,
  "query": "...",
  "collection_name": "...",
  "tenant_id": "default",
  "answer": "Generated answer text [Source 1] [Source 2]",
  "citations": [
    {
      "source_id": 1,
      "chunk_id": "chunk_001",
      "document_id": "doc_123",
      "text_preview": "Relevant text snippet..."
    }
  ],
  "context_chunks": [
    {
      "chunk_id": "chunk_001",
      "text": "Full chunk text...",
      "document_id": "doc_123",
      "topics": "Machine Learning, AI",
      "keywords": "RAG, embeddings, vector search",
      "summary": "Chunk summary..."
    }
  ],
  "stages": {
    "intent_detection": {
      "time_ms": 150,
      "success": true,
      "metadata": {
        "intent": "factual_retrieval",
        "language": "en",
        "confidence": 0.95
      }
    },
    "search": {
      "time_ms": 85,
      "success": true,
      "metadata": {
        "results_count": 10,
        "metadata_boost_enabled": true
      }
    },
    "reranking": {
      "time_ms": 245,
      "success": true,
      "metadata": {
        "input_count": 10,
        "output_count": 3
      }
    },
    "compression": {
      "time_ms": 0,
      "success": true,
      "metadata": {"skipped": true}
    },
    "answer_generation": {
      "time_ms": 1520,
      "success": true,
      "metadata": {
        "context_chunks": 3,
        "citations": 2,
        "model_used": "Llama-3.3-70B-Instruct-fast"
      }
    }
  },
  "total_time_ms": 2000,
  "search_results_count": 10,
  "reranked_count": 3,
  "compressed_count": 0,
  "context_count": 3,
  "api_version": "1.0.0",
  "timestamp": "2025-10-18T10:30:45.123456"
}
```

## Configuration Tuning

### When to Enable Compression

**Enable compression when:**
- Long documents with lots of irrelevant content
- Context quality > speed
- Budget allows extra 1-3s latency
- Dealing with technical/specification-heavy content

**Disable compression when:**
- Speed is critical (<2s target)
- Documents are already concise
- Using metadata boost (already filters relevance)
- High request volume (compression is LLM-intensive)

### Pipeline Configuration Presets

**Ultra-Fast (< 1s)**
```python
{
    "search_top_k": 5,
    "enable_reranking": False,
    "enable_compression": False,
    "max_context_chunks": 1
}
```

**Speed-Optimized (< 2s) - DEFAULT**
```python
{
    "search_top_k": 10,
    "rerank_top_k": 3,
    "enable_compression": False,
    "max_context_chunks": 3
}
```

**Balanced (2-3s)**
```python
{
    "search_top_k": 15,
    "rerank_top_k": 5,
    "enable_compression": False,
    "max_context_chunks": 4
}
```

**High-Quality (3-5s)**
```python
{
    "search_top_k": 20,
    "rerank_top_k": 10,
    "enable_compression": True,
    "compression_ratio": 0.4,
    "max_context_chunks": 5
}
```

## Endpoints

### Main Endpoints

- `POST /v1/retrieve` - Full RAG retrieval pipeline
- `GET /health` - Health check with dependency status
- `GET /` - Service info and available endpoints

### API Documentation

- Swagger UI: http://localhost:8070/docs
- ReDoc: http://localhost:8070/redoc

## Installation & Deployment

### Prerequisites

All internal services must be running:
1. **Search Service** (port 8071) - Dense vector search
2. **Reranking Service** (port 8072) - Cross-encoder reranking
3. **Compression Service** (port 8073) - LLM compression
4. **Answer Generation Service** (port 8074) - LLM answer generation
5. **Intent Service** (port 8075) - Intent detection

Use `pipeline-manager` to start all services:

```bash
cd /path/to/Tools
./pipeline-manager start-retrieval  # Start all Retrieval services
```

### Environment Variables

All settings in `config.py`:

```python
# Server
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8070

# Internal service URLs
INTENT_SERVICE_URL = "http://localhost:8075/v1"
SEARCH_SERVICE_URL = "http://localhost:8071/v1"
RERANK_SERVICE_URL = "http://localhost:8072/v1"
COMPRESS_SERVICE_URL = "http://localhost:8073/v1"
ANSWER_SERVICE_URL = "http://localhost:8074/v1"

# Speed-optimized defaults
DEFAULT_SEARCH_TOP_K = 10
DEFAULT_RERANK_TOP_K = 3
DEFAULT_MAX_CONTEXT_CHUNKS = 3
DEFAULT_COMPRESSION_RATIO = 0.5
DEFAULT_SCORE_THRESHOLD = 0.3

# Feature toggles
ENABLE_INTENT_DETECTION = true
ENABLE_SEARCH = true
ENABLE_RERANKING = true
ENABLE_COMPRESSION = false  # Disabled for speed
ENABLE_ANSWER_GENERATION = true

# LLM Configuration
DEFAULT_ANSWER_MODEL = "meta-llama/Llama-3.3-70B-Instruct-fast"

# Rate limiting
MAX_CONCURRENT_RETRIEVALS = 20
```

### Running the Service

```bash
# Manual start
cd /path/to/Retrieval/v1.0.0
python3 main_retrieval_api.py

# Using pipeline-manager (recommended)
cd /path/to/Tools
./pipeline-manager retrieval  # Start main Retrieval API only
./pipeline-manager start-retrieval  # Start all Retrieval services
```

### Health Check

```bash
curl http://localhost:8070/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "Retrieval Pipeline API",
  "version": "1.0.0",
  "timestamp": "2025-10-18T10:30:45.123456",
  "dependencies": {
    "intent": {"status": "healthy", "version": "1.0.0"},
    "search": {"status": "healthy", "version": "1.0.0"},
    "reranking": {"status": "healthy", "version": "2.0.0"},
    "compression": {"status": "healthy", "version": "2.0.0"},
    "answer_generation": {"status": "healthy", "version": "1.0.0"}
  },
  "health_summary": {
    "total_services": 5,
    "healthy": 5,
    "unhealthy": 0
  }
}
```

## Intent Detection

The Intent Service (port 8075) runs **in parallel** with Stage 1 (Search) to minimize latency impact.

**What it does:**
- Detects query type (factual, comparison, mathematical, etc.)
- Recommends appropriate LLM model
- Adapts system prompt for query intent
- Detects language and complexity

**Intent-based model recommendations:**
- `factual_retrieval` → Llama-3.3-70B-Instruct-fast (default)
- `comparison` → Qwen2.5-72B-Instruct (better reasoning)
- `mathematical` → DeepSeek-R1-Distill-Qwen-70B (math-focused)
- `code_generation` → Qwen2.5-Coder-32B-Instruct (code-focused)

**Performance**: ~100-300ms (runs parallel with search)

## Metadata Boosting

Search service uses **4 metadata fields** to boost relevance:

| Field | Description | Boost Weight |
|-------|-------------|--------------|
| `keywords` | Extracted keywords | 0.15 |
| `topics` | Document topics | 0.10 |
| `questions` | Related questions | 0.20 |
| `summary` | Chunk summary | 0.05 |

**Total boost**: Up to +0.50 on vector similarity score

**When to use:**
- Always enabled by default (`use_metadata_boost: true`)
- Improves relevance for topical/keyword-heavy queries
- Minimal performance impact (~5-10ms)

## Troubleshooting

### Slow Retrieval (>5s)

**Possible causes:**
1. Compression enabled (adds 1-3s) → Disable with `enable_compression: false`
2. Too many chunks → Reduce `search_top_k`, `rerank_top_k`, `max_context_chunks`
3. Slow LLM model → Use `Llama-3.3-70B-Instruct-fast` (default)
4. Large collection → Check Milvus index type and configuration

### No Results Returned

**Check:**
1. Collection exists and has data
2. Tenant ID matches data
3. Query embeddings successfully generated
4. Milvus search not timing out

### Citations Missing

**Verify:**
1. `enable_citations: true` in request
2. LLM is generating `[Source X]` tags in answer
3. Context chunks have valid `chunk_id` and `document_id`

### Service Unhealthy

```bash
# Check all dependencies
curl http://localhost:8070/health

# Check individual services
curl http://localhost:8071/health  # Search
curl http://localhost:8072/health  # Reranking
curl http://localhost:8073/health  # Compression
curl http://localhost:8074/health  # Answer Generation
curl http://localhost:8075/health  # Intent

# Restart all services
cd /path/to/Tools
./pipeline-manager restart-retrieval
```

## Version History

- **v1.0.0** (2025-10-18): Production release
  - Multi-stage RAG pipeline (Search → Rerank → Compress → Answer)
  - Intent-aware answer generation
  - Speed-optimized defaults (10→3→3 pipeline, compression disabled)
  - Full parameter control via API
  - Multi-tenancy support
  - Metadata boosting (4 fields: keywords, topics, questions, summary)
  - Rate limiting (20 concurrent retrievals)
  - Comprehensive health monitoring
  - **Parameter Fix**: Synced all defaults with config.py (search_top_k 20→10, rerank_top_k 10→3, max_context_chunks 5→3, compression enabled→disabled)

## License

Internal use only - CrawlEnginePro / MindMate247

## Support

For issues:
- Check service logs for detailed error messages
- Verify all dependencies are healthy (`/health` endpoint)
- Test with minimal configuration first
- Check `pipeline-manager status` for service status

---

**Version**: v1.0.0
**Date**: October 18, 2025
**Status**: Production-ready
**Performance**: <2s average retrieval time (speed-optimized defaults)
