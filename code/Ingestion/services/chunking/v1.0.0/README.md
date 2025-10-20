# Chunking Orchestrator v1.0.0

**Streamlined RAG Pipeline - Pure Orchestration with 4 Core Metadata Fields**

**Last Updated:** October 18, 2025

## Overview

Chunking Orchestrator v1.0.0 is focused on **pure orchestration**. It coordinates the complete ingestion pipeline by delegating to specialized services, providing users with **full parameter control** over chunking, metadata, embeddings, and storage.

**Key Features:**
- ✅ **7 Metadata Fields**: keywords, topics, questions, summary, semantic_keywords, entity_relationships, attributes
- ✅ **Multi-Provider Embeddings**: Jina (1024/2048-dim), Nebius (4096-dim), SambaNova (FREE 4096-dim)
- ✅ **Auto-Dimension Detection**: Collection dimensions automatically match embedding model
- ✅ **Full Parameter Control**: Customize chunking, metadata, embeddings, and storage
- ✅ **Smart Defaults**: All parameters optional with sensible defaults
- ✅ **Pure Orchestration**: No direct database dependencies, delegates all operations

## Architecture

### ✅ Architecture Simplification
- **NO direct pymilvus imports** - delegates to Milvus Storage v1.0.0 API
- **Calls Metadata v1.0.0** (extracts 7 fields: keywords, topics, questions, summary, semantic_keywords, entity_relationships, attributes)
- **Calls Embeddings v1.0.0** - Multi-provider support (Jina/Nebius/SambaNova)
- **Pure orchestration** - coordinates services, doesn't implement storage logic

### ✅ Service Dependencies
```
Chunking v1.0.0 (This service - port 8071)
  ├── Metadata v1.0.0 (port 8072) → LLM Gateway (port 8075)
  ├── Embeddings v1.0.0 (port 8073) - Multi-provider (Jina/Nebius/SambaNova)
  └── Storage v1.0.0 (port 8074) - CRUD API for Milvus
```

### ✅ Metadata Support
- **7 metadata fields** per chunk: keywords, topics, questions, summary, semantic_keywords, entity_relationships, attributes
- Extracted via Metadata v1.0.0 service (port 8072) using SambaNova Qwen3-32B model
- Metadata service uses LLM Gateway (port 8075) for AI-powered extraction
- **Optimized for RAG**: Includes semantic expansion, entity relationships, and structured attributes

## Configuration

### Port
- **8071** - Chunking Orchestrator v1.0.0

### Service URLs (INTERNAL_MODE=true, default)
- **Metadata v1.0.0**: http://localhost:8072/v1/metadata
- **Embeddings v1.0.0**: http://localhost:8073/v1/embeddings
- **Milvus Storage v1.0.0**: http://localhost:8074/v1

### Environment Variables
```bash
# Server
HOST=0.0.0.0
PORT=8071

# Mode
INTERNAL_MODE=true  # Direct localhost calls (default, lower latency)

# Service URLs (auto-configured based on INTERNAL_MODE)
# EMBEDDINGS_SERVICE_URL=http://localhost:8073/v1/embeddings
# METADATA_SERVICE_URL=http://localhost:8072/v1/metadata
# MILVUS_STORAGE_SERVICE_URL=http://localhost:8074/v1

# Processing
MAX_WORKERS=5  # Parallel metadata extraction workers
```

## Installation

### 1. Install Dependencies

```bash
cd /path/to/Ingestion/services/chunking/v1.0.0

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Create .env file
cp .env.example .env

# .env should have:
HOST=0.0.0.0
PORT=8071
INTERNAL_MODE=true  # Direct localhost calls (default)
```

### 3. Start Service Locally

```bash
python chunking_orchestrator.py
```

Expected output:
```
================================================================================
Chunking Orchestrator v1.0.0
================================================================================
FEATURES:
  ✅ Internal-mode service (localhost only)
  ✅ Intelligent text chunking (recursive/markdown/token)
  ✅ 7 metadata fields (keywords, topics, questions, summary, semantic_keywords, entity_relationships, attributes)
  ✅ Multi-provider embeddings (Jina/Nebius/SambaNova)
  ✅ Auto-dimension detection (1024/2048/3584/4096)
  ✅ Milvus Storage Service integration (v1.0.0 API)
  ✅ Parallel processing for speed
  ✅ NO direct Milvus dependencies
================================================================================
[CONFIG] INTERNAL_MODE=True
[CONFIG] Using INTERNAL mode:
[CONFIG]   Metadata v1: http://localhost:8072/v1/metadata
[CONFIG]   Embeddings v1: http://localhost:8073/v1/embeddings
[CONFIG]   Storage v1: http://localhost:8074/v1
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8071/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "Chunking Orchestrator",
  "services": {
    "embeddings": true,
    "metadata": true,
    "milvus_storage": true
  },
  "uptime_seconds": 123.45,
  "total_requests": 10
}
```

### Version Info
```bash
curl http://localhost:8071/version
```

### Complete Pipeline (Full Parameter Control)

```bash
curl -X POST http://localhost:8071/v1/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Apple iPhone 15 Pro in Natural Titanium with 128GB storage. Features A17 Pro chip and 48MP camera. Price: $999 USD.",

    // Chunking parameters
    "method": "recursive",
    "max_chunk_size": 1000,
    "chunk_overlap": 300,
    "separators": null,
    "markdown_headers": null,
    "encoding": "cl100k_base",

    // Metadata parameters
    "generate_metadata": true,
    "metadata_config": {
      "keywords_count": "5",
      "topics_count": "3",
      "questions_count": "3",
      "summary_length": "1-2 sentences"
    },

    // Embedding parameters
    "generate_embeddings": true,
    "embedding_model": "jina-embeddings-v3",  // Default 1024-dim

    // Storage parameters
    "storage_mode": "new_collection",
    "collection_name": "test_products",
    "tenant_id": "test_tenant",
    "document_id": "product_001"
  }'
```

Response includes:
- **Chunks** with 7 metadata fields (keywords, topics, questions, summary, semantic_keywords, entity_relationships, attributes)
- **Embeddings** from selected provider (dimension auto-detected)
- **Processing times** for each stage
- **Storage confirmation** from Milvus Storage v1.0.0

## Usage Examples

### Example 1: Chunking Only (No Storage)
```python
import httpx

response = httpx.post(
    "http://localhost:8071/v1/orchestrate",
    json={
        "text": "Your long document here...",
        "method": "recursive",
        "max_chunk_size": 1000,
        "chunk_overlap": 300,
        "generate_embeddings": False,
        "generate_metadata": False,
        "storage_mode": "none"
    }
)

result = response.json()
print(f"Created {result['total_chunks']} chunks")
```

### Example 2: Full Pipeline with Jina Embeddings (Default)
```python
import httpx

response = httpx.post(
    "http://localhost:8071/v1/orchestrate",
    json={
        "text": "Apple iPhone 15 Pro - Premium smartphone with titanium design...",
        "method": "recursive",
        "max_chunk_size": 1000,
        "chunk_overlap": 300,
        "generate_embeddings": True,  # Jina v3 (1024-dim) by default
        "generate_metadata": True,    # 4 core fields
        "storage_mode": "new_collection",
        "collection_name": "products",
        "tenant_id": "client_acme",
        "document_id": "product_iphone15pro"
    }
)

result = response.json()

# Access 7 metadata fields
for chunk in result['chunks']:
    print(f"Keywords: {chunk['keywords']}")
    print(f"Topics: {chunk['topics']}")
    print(f"Questions: {chunk['questions']}")
    print(f"Summary: {chunk['summary']}")
    print(f"Semantic Keywords: {chunk['semantic_keywords']}")
    print(f"Entity Relationships: {chunk['entity_relationships']}")
    print(f"Attributes: {chunk['attributes']}")
    print(f"Dense embedding: {len(chunk['dense_embedding'])} dims")  # 1024
```

### Example 3: FREE 4096-dim Embeddings (SambaNova)
```python
import httpx

response = httpx.post(
    "http://localhost:8071/v1/orchestrate",
    json={
        "text": "Your document content here...",
        "method": "recursive",
        "max_chunk_size": 1500,  # Larger chunks for high-dim embeddings
        "chunk_overlap": 400,
        "generate_embeddings": True,
        "embedding_model": "E5-Mistral-7B-Instruct",  # FREE 4096-dim from SambaNova
        "generate_metadata": True,
        "storage_mode": "new_collection",
        "collection_name": "high_dim_collection",
        "document_id": "doc_001"
    }
)

result = response.json()
print(f"Embeddings: {len(result['chunks'][0]['dense_embedding'])} dims")  # 4096
```

### Example 4: Custom Metadata Configuration
```python
import httpx

response = httpx.post(
    "http://localhost:8071/v1/orchestrate",
    json={
        "text": "Your document content here...",
        "method": "recursive",
        "max_chunk_size": 1000,
        "generate_metadata": True,
        "metadata_config": {
            "keywords_count": "10",           # More keywords
            "topics_count": "5",              # More topics
            "questions_count": "5",           # More questions
            "summary_length": "2-3 sentences" # Longer summary
        },
        "generate_embeddings": True,
        "storage_mode": "new_collection",
        "collection_name": "detailed_metadata",
        "document_id": "doc_002"
    }
)
```

### Example 5: Markdown-Specific Chunking
```python
import httpx

response = httpx.post(
    "http://localhost:8071/v1/orchestrate",
    json={
        "text": "# Chapter 1\nContent...\n## Section 1.1\nMore content...",
        "method": "markdown",
        "markdown_headers": ["#", "##", "###"],
        "max_chunk_size": 800,
        "generate_metadata": True,
        "generate_embeddings": True,
        "embedding_model": "jina-embeddings-v4",  # 2048-dim multimodal
        "storage_mode": "new_collection",
        "collection_name": "markdown_docs",
        "document_id": "doc_003"
    }
)
```

### Example 6: Skip Metadata (Faster Ingestion)
```python
import httpx

response = httpx.post(
    "http://localhost:8071/v1/orchestrate",
    json={
        "text": "Your document content here...",
        "method": "recursive",
        "max_chunk_size": 1000,
        "chunk_overlap": 300,
        "generate_metadata": False,  # Skip keywords/topics/questions/summary
        "generate_embeddings": True,
        "storage_mode": "new_collection",
        "collection_name": "fast_ingestion",
        "document_id": "doc_004"
    }
)

# Performance gain: ~40-60% faster (no LLM Gateway calls)
```

## Embedding Model Support

The service supports multiple embedding providers with auto-dimension detection:

| Provider | Model | Dimensions | Cost | Use Case |
|----------|-------|------------|------|----------|
| **Jina AI** | `jina-embeddings-v3` | 1024 | Paid | Fast, multilingual (89 languages) - **DEFAULT** |
| **Jina AI** | `jina-embeddings-v4` | 2048 | Paid | Multimodal (text + images) |
| **Nebius AI** | `intfloat/e5-mistral-7b-instruct` | 4096 | Paid | Best for RAG, high accuracy |
| **Nebius AI** | `BAAI/bge-en-icl` | 4096 | Paid | English-optimized |
| **Nebius AI** | `BAAI/bge-multilingual-gemma2` | 3584 | Paid | Multilingual |
| **Nebius AI** | `Qwen/Qwen3-Embedding-8B` | 4096 | Paid | Latest Qwen model |
| **SambaNova** | `E5-Mistral-7B-Instruct` | 4096 | **FREE** | Same as Nebius E5, no cost |

**Auto-Dimension Detection**: Collection dimensions automatically match the selected embedding model.

## Parameter Reference

### Chunking Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `method` | string | `recursive` | `recursive`, `markdown`, `token` | Chunking strategy |
| `max_chunk_size` | int | `1000` | 100-10000 | Max tokens per chunk |
| `chunk_overlap` | int | `300` | 0-1000 | Overlap between chunks (tokens) |
| `separators` | list | `None` | - | Custom split separators |
| `markdown_headers` | list | `None` | - | Headers for markdown method |
| `encoding` | string | `cl100k_base` | - | Tokenizer encoding |

### Metadata Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `generate_metadata` | bool | `true` | Enable metadata extraction |
| `metadata_config.keywords_count` | string | `"5"` | Number of keywords (1-20) |
| `metadata_config.topics_count` | string | `"3"` | Number of topics (1-10) |
| `metadata_config.questions_count` | string | `"3"` | Number of questions (1-10) |
| `metadata_config.summary_length` | string | `"1-2 sentences"` | Summary length |

**7 Fields Extracted**: keywords, topics, questions, summary, semantic_keywords, entity_relationships, attributes

### Embedding Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `generate_embeddings` | bool | `true` | Enable embedding generation |
| `embedding_model` | string | `jina-embeddings-v3` | See "Embedding Model Support" table |

### Storage Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `storage_mode` | string | `new_collection` | `new_collection`, `existing`, `none` |
| `collection_name` | string | - | Milvus collection name |
| `tenant_id` | string | `default` | Tenant ID for multi-tenancy |
| `document_id` | string | - | Document identifier |

## Service Dependencies

### Required Services (Must be running)
1. **Metadata v1.0.0** (port 8072) - Extracts 7 metadata fields using SambaNova Qwen3-32B
2. **Embeddings v1.0.0** (port 8073) - Multi-provider embedding generation
3. **Milvus Storage v1.0.0** (port 8074) - Vector storage API
4. **LLM Gateway** (port 8075) - Used by Metadata Service

### Check Service Health
```bash
# Check all dependencies
curl http://localhost:8071/health

# Should show:
# "embeddings": true
# "metadata": true
# "milvus_storage": true

# Check individual services
curl http://localhost:8072/health  # Metadata v1
curl http://localhost:8073/health  # Embeddings v1
curl http://localhost:8074/health  # Storage v1
curl http://localhost:8075/health  # LLM Gateway
```

## Performance Metrics

Pipeline timings (typical document with 10-20 chunks):

| Stage | Time | Notes |
|-------|------|-------|
| **Chunking** | 10-50ms | Fast, in-memory operation |
| **Metadata** | 200-400ms/chunk | LLM-powered extraction (7 fields using SambaNova Qwen3-32B) |
| **Embeddings** | 50-200ms/batch | Varies by provider and dimension |
| **Storage** | <100ms | Via Storage API |

**Total pipeline**: 1-3 seconds for typical documents

**Performance tips:**
- Disable metadata (`generate_metadata: false`) for 40-60% speed boost
- Use Jina v3 (1024-dim) for faster embeddings vs 4096-dim models
- Increase `max_chunk_size` to reduce chunk count and total processing time
- Use SambaNova FREE tier to avoid rate limits

## Differences from Previous Versions

| Feature | v3.0.0/v5.0.0 | v1.0.0 |
|---------|---------------|--------|
| **Metadata Fields** | 45 fields (product data, business data, entities) | **7 optimized fields** (keywords, topics, questions, summary, semantic_keywords, entity_relationships, attributes) |
| **Metadata Model** | Nebius models | **SambaNova Qwen3-32B** (via LLM Gateway) |
| **Embeddings** | Single provider (Nebius 4096-dim) | **Multi-provider** (Jina/Nebius/SambaNova) |
| **Default Dimension** | 4096 | **1024** (Jina v3, faster) |
| **Chunk Overlap** | 200 tokens | **300 tokens** (better context) |
| **Parameter Control** | Limited | **Full control** (all parameters customizable) |
| **Auto-Dimension** | Manual configuration | **Auto-detected** from embedding model |
| **FREE Option** | None | **SambaNova** (4096-dim FREE) |
| **Performance** | Slower (45 fields) | **Faster** (7 fields optimized for RAG) |
| **Schema Complexity** | High (45 fields) | **Optimized** (7 fields for RAG) |
| **Use Case** | Product/business-specific | **General-purpose RAG with semantic expansion** |

## API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8071/docs
- ReDoc: http://localhost:8071/redoc

## Troubleshooting

### Service Won't Start
```bash
# Check if port 8071 is in use
netstat -tulpn | grep 8071

# Check virtual environment
source venv/bin/activate
python -c "import fastapi; print('OK')"

# Check dependencies health
curl http://localhost:8072/health  # Metadata v1
curl http://localhost:8073/health  # Embeddings v1
curl http://localhost:8074/health  # Storage v1
curl http://localhost:8075/health  # LLM Gateway
```

### Metadata Extraction Slow
- Normal! LLM-powered extraction takes 200-400ms per chunk
- Use `generate_metadata: false` to skip metadata for faster ingestion
- Use parallel processing (automatic, controlled by MAX_WORKERS)

### Storage Fails
```bash
# Check Milvus Storage service
curl http://localhost:8074/health

# Check if collection exists
curl http://localhost:8074/v1/collections

# Check Milvus connection
curl http://localhost:8074/v1/health
```

### Wrong Embedding Dimension
- Check `embedding_model` parameter matches your collection dimension
- Use auto-dimension detection (don't manually create collections)
- Verify embedding model in Embeddings v1.0.0 service

## Version History

- **v1.0.0** (2025-10-18): Streamlined release
  - Optimized metadata from 45 → 7 RAG-focused fields (keywords, topics, questions, summary, semantic_keywords, entity_relationships, attributes)
  - Metadata extraction using SambaNova Qwen3-32B model via LLM Gateway (port 8075)
  - Added multi-provider embedding support (Jina/Nebius/SambaNova)
  - Auto-dimension detection (1024/2048/3584/4096)
  - Full parameter control (chunking, metadata, embeddings, storage)
  - Changed default chunk_overlap: 200 → 300 tokens
  - Changed default embedding: Nebius 4096-dim → Jina v3 1024-dim
  - Added FREE option: SambaNova E5-Mistral-7B-Instruct (4096-dim)
  - Optimized schema (7 fields optimized for RAG with semantic expansion)

## License

Internal service for mindmate247.com
