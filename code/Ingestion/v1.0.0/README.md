# Ingestion Pipeline API v1.0.0

Main orchestrator for document ingestion into vector database with **full parameter control**.

## Overview

The Ingestion Pipeline provides a single unified API for ingesting documents into the vector database. It orchestrates 4 internal microservices to process documents through the complete pipeline.

**Key Features:**
- ✅ **Fully Customizable**: Control chunking, metadata, embeddings, and storage parameters
- ✅ **Multi-Provider Embeddings**: Choose from Jina (1024/2048-dim), Nebius (4096-dim), or SambaNova (FREE 4096-dim)
- ✅ **Auto-Dimension Detection**: Collection dimensions automatically match your embedding model
- ✅ **Smart Defaults**: All parameters optional with sensible defaults
- ✅ **Full CRUD**: Create, Read, Update, Delete collections and documents
- ✅ **4 Core Metadata Fields**: Keywords, Topics, Questions, Summary (streamlined from 45 fields)

### Pipeline Flow

```
Document → Chunking → Metadata (4 fields) → Embeddings (Multi-Provider) → Storage → Vector DB
```

### Architecture

- **Public API**: Port 8060 (this service)
- **Internal Services** (ports 8061-8065, not publicly accessible):
  - 8061: Chunking Service
  - 8062: Metadata Service (extracts 4 core fields)
  - 8063: Embeddings Service (multi-provider: Jina/Nebius/SambaNova)
  - 8064: Storage Service (full CRUD for Milvus)
  - 8065: LLM Gateway Service (used by Metadata Service)

## API Endpoints

### 1. Health Check
```bash
GET /health
```

### 2. Ingest Document (Full Parameter Control)

Ingest a document with complete control over all pipeline parameters.

```bash
POST /v1/ingest
Content-Type: application/json

{
  // REQUIRED FIELDS
  "text": "Document content here...",
  "document_id": "doc123",
  "collection_name": "my_collection",

  // OPTIONAL: Tenant (default: "default")
  "tenant_id": "default",

  // OPTIONAL: Chunking Parameters (all optional with smart defaults)
  "chunking_method": "recursive",        // "recursive" | "markdown" | "token" (default: recursive)
  "max_chunk_size": 1000,                // 100-10000 tokens (default: 1000)
  "chunk_overlap": 300,                  // 0-1000 tokens (default: 300)
  "separators": ["\n\n", "\n", ". "],   // Custom separators (optional)
  "markdown_headers": ["#", "##"],       // For markdown method only (optional)
  "encoding": "cl100k_base",             // Tokenizer (default: cl100k_base)

  // OPTIONAL: Metadata Parameters (all optional)
  "generate_metadata": true,             // Generate keywords/topics/questions/summary (default: true)
  "keywords_count": 5,                   // 1-20 keywords (default: 5)
  "topics_count": 3,                     // 1-10 topics (default: 3)
  "questions_count": 3,                  // 1-10 questions (default: 3)
  "summary_length": "1-2 sentences",     // Summary length (default: "1-2 sentences")

  // OPTIONAL: Embedding Parameters
  "generate_embeddings": true,                            // Generate embeddings (default: true)
  "embedding_model": "jina-embeddings-v3",               // See "Supported Embedding Models" below

  // OPTIONAL: Storage Parameters
  "storage_mode": "new_collection",                      // "new_collection" | "existing" | "none"
  "create_collection_if_missing": true                   // Auto-create collection (default: true)
}
```

#### Supported Embedding Models

Choose from multiple providers with auto-dimension detection:

| Provider | Model | Dimensions | Cost | Use Case |
|----------|-------|------------|------|----------|
| **Jina AI** | `jina-embeddings-v3` | 1024 | Paid | Fast, multilingual (89 languages) |
| **Jina AI** | `jina-embeddings-v4` | 2048 | Paid | Multimodal (text + images) |
| **Nebius AI** | `intfloat/e5-mistral-7b-instruct` | 4096 | Paid | Best for RAG, high accuracy |
| **Nebius AI** | `BAAI/bge-en-icl` | 4096 | Paid | English-optimized |
| **Nebius AI** | `BAAI/bge-multilingual-gemma2` | 3584 | Paid | Multilingual |
| **Nebius AI** | `Qwen/Qwen3-Embedding-8B` | 4096 | Paid | Latest Qwen model |
| **SambaNova** | `E5-Mistral-7B-Instruct` | 4096 | **FREE** | Same as Nebius E5, no cost |

**Default**: `jina-embeddings-v3` (1024-dim, fast, multilingual)

**Response:**
```json
{
  "success": true,
  "document_id": "doc123",
  "collection_name": "my_collection",
  "tenant_id": "default",
  "chunks_created": 15,
  "chunks_inserted": 15,
  "processing_time_ms": 2345.67,
  "stages": {
    "chunking": {
      "method": "recursive",
      "max_chunk_size": 1000,
      "chunk_overlap": 300,
      "chunks_created": 15,
      "time_ms": 123.45
    },
    "metadata": {
      "fields_extracted": ["keywords", "topics", "questions", "summary"],
      "chunks_processed": 15,
      "time_ms": 456.78
    },
    "embeddings": {
      "model": "jina-embeddings-v3",
      "dimension": 1024,
      "chunks_processed": 15,
      "time_ms": 234.56
    },
    "storage": {
      "collection_name": "my_collection",
      "chunks_inserted": 15,
      "time_ms": 123.45
    }
  }
}
```

### 3. Create Collection

Create a new collection with custom dimension (auto-detected from embedding model).

```bash
POST /v1/collections
Content-Type: application/json

{
  "collection_name": "my_new_collection",
  "dimension": 4096,                      // Match your embedding model dimension
  "description": "My collection description"
}
```

**Auto-Dimension Detection**: When you ingest documents, the collection dimension automatically matches your `embedding_model`:
- `jina-embeddings-v3` → 1024 dims
- `jina-embeddings-v4` → 2048 dims
- `intfloat/e5-mistral-7b-instruct` (Nebius) → 4096 dims
- `E5-Mistral-7B-Instruct` (SambaNova FREE) → 4096 dims

### 4. Delete Collection

Delete a collection and all its documents.

```bash
DELETE /v1/collections/{collection_name}
```

### 5. Update Document

Update an existing document (delete + re-insert).

```bash
PUT /v1/documents/{document_id}
Content-Type: application/json

{
  "text": "Updated document content...",
  "collection_name": "my_collection",
  "tenant_id": "default",

  // All chunking/metadata/embedding parameters supported (see /v1/ingest)
  "max_chunk_size": 800,
  "chunk_overlap": 200,
  "embedding_model": "E5-Mistral-7B-Instruct"  // Switch to FREE SambaNova
}
```

### 6. Delete Document

Delete a document and all its chunks.

```bash
DELETE /v1/documents/{document_id}?collection_name=my_collection
```

## Usage Examples

### Example 1: Simple Ingestion (All Defaults)

Minimal request using smart defaults (recursive chunking, 1000 tokens, 300 overlap, Jina embeddings, metadata enabled):

```bash
curl -X POST http://localhost:8060/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The quick brown fox jumps over the lazy dog. This is a sample document for testing the ingestion pipeline. It will be automatically chunked, enriched with metadata (keywords, topics, questions, summary), embedded using Jina AI, and stored in Milvus.",
    "document_id": "doc_001",
    "collection_name": "test_collection"
  }'
```

**What happens:**
- ✅ Chunked using recursive method (1000 tokens, 300 overlap)
- ✅ Metadata extracted: keywords, topics, questions, summary (4 fields)
- ✅ Embeddings: Jina v3 (1024-dim, multilingual)
- ✅ Stored in Milvus collection "test_collection" (auto-created if missing)

### Example 2: Custom Chunking (Smaller Chunks, More Overlap)

Fine-tune chunking for better precision:

```bash
curl -X POST http://localhost:8060/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your document content here...",
    "document_id": "doc_002",
    "collection_name": "test_collection",
    "max_chunk_size": 500,      // Smaller chunks for better precision
    "chunk_overlap": 150        // More overlap for context preservation
  }'
```

### Example 3: Markdown-Specific Chunking

Use markdown headers as natural split points:

```bash
curl -X POST http://localhost:8060/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "# Chapter 1\nContent...\n## Section 1.1\nMore content...",
    "document_id": "doc_003",
    "collection_name": "test_collection",
    "chunking_method": "markdown",
    "markdown_headers": ["#", "##", "###"]
  }'
```

### Example 4: FREE Embeddings (SambaNova)

Use SambaNova's FREE tier for 4096-dim embeddings:

```bash
curl -X POST http://localhost:8060/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your document content here...",
    "document_id": "doc_004",
    "collection_name": "high_dim_collection",
    "embedding_model": "E5-Mistral-7B-Instruct",  // FREE 4096-dim from SambaNova
    "max_chunk_size": 1500                         // Larger chunks for high-dim embeddings
  }'
```

### Example 5: Custom Metadata Configuration

Control metadata extraction:

```bash
curl -X POST http://localhost:8060/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your document content here...",
    "document_id": "doc_005",
    "collection_name": "test_collection",
    "generate_metadata": true,
    "keywords_count": 10,             // More keywords
    "topics_count": 5,                // More topics
    "questions_count": 5,             // More questions
    "summary_length": "2-3 sentences" // Longer summary
  }'
```

### Example 6: Skip Metadata (Faster Ingestion)

Disable metadata extraction for speed:

```bash
curl -X POST http://localhost:8060/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your document content here...",
    "document_id": "doc_006",
    "collection_name": "test_collection",
    "generate_metadata": false  // Skip keywords/topics/questions/summary
  }'
```

**Performance gain**: ~40-60% faster (no LLM Gateway calls for metadata)

### Example 7: Multimodal Embeddings (Jina v4)

Use Jina v4 for text + image support (2048-dim):

```bash
curl -X POST http://localhost:8060/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your document content here...",
    "document_id": "doc_007",
    "collection_name": "multimodal_collection",
    "embedding_model": "jina-embeddings-v4"  // 2048-dim, multimodal
  }'
```

### Example 8: Update Document with Different Model

Update existing document and switch embedding model:

```bash
curl -X PUT http://localhost:8060/v1/documents/doc_001 \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Updated content for the document...",
    "collection_name": "test_collection",
    "embedding_model": "intfloat/e5-mistral-7b-instruct",  // Switch to Nebius 4096-dim
    "max_chunk_size": 1200,
    "chunk_overlap": 400
  }'
```

### Example 9: Create Collection (Manual Dimension)

Create collection before ingestion:

```bash
curl -X POST http://localhost:8060/v1/collections \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "new_collection",
    "dimension": 4096,  // For Nebius/SambaNova models
    "description": "Collection for 4096-dim embeddings"
  }'
```

### Example 10: Delete Document

```bash
curl -X DELETE "http://localhost:8060/v1/documents/doc_001?collection_name=test_collection"
```

### Example 11: Delete Collection

```bash
curl -X DELETE http://localhost:8060/v1/collections/test_collection
```

## Configuration

Configuration is loaded from `/PipeLineServices/.env`:

```bash
# Ingestion Pipeline Ports
INGESTION_API_PORT=8060
CHUNKING_SERVICE_PORT=8061
METADATA_SERVICE_PORT=8062
EMBEDDINGS_SERVICE_PORT=8063
STORAGE_SERVICE_PORT=8064
LLM_GATEWAY_SERVICE_PORT=8065

# Service URLs
CHUNKING_SERVICE_URL=http://localhost:8061/v1/orchestrate
METADATA_SERVICE_URL=http://localhost:8062/v1/metadata
EMBEDDINGS_SERVICE_URL=http://localhost:8063/v1/embeddings
STORAGE_SERVICE_URL=http://localhost:8064/v1

# Embedding Providers
# Jina AI (1024/2048-dim)
JINA_API_KEY=your_jina_key_here
JINA_API_URL=https://api.jina.ai/v1/embeddings

# Nebius AI Studio (4096-dim, best for RAG)
NEBIUS_API_KEY=your_nebius_key_here
NEBIUS_API_URL=https://api.studio.nebius.ai/v1/embeddings

# SambaNova AI (FREE 4096-dim embeddings)
SAMBANOVA_API_KEY=your_sambanova_key_here
SAMBANOVA_API_URL=https://api.sambanova.ai/v1/embeddings

# LLM Gateway (Port 8065 - used by Metadata Service)
LLM_GATEWAY_URL_DEVELOPMENT=http://localhost:8065/v1/chat/completions
LLM_GATEWAY_URL_PRODUCTION=http://localhost:8065/v1/chat/completions
LLM_GATEWAY_API_KEY=your_key_here

# Milvus Vector Database
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

## Installation

1. **Install dependencies**:
```bash
cd /path/to/PipeLineServices/Ingestion/v1.0.0
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
# Edit /PipeLineServices/.env with your configuration
vim ../../.env
```

3. **Start internal services first** (in separate terminals):
```bash
# Terminal 1: LLM Gateway (required by Metadata Service)
cd ../services/llm_gateway/v1.0.0
python llm_gateway.py

# Terminal 2: Storage Service
cd ../services/storage/v1.0.0
python storage_api.py

# Terminal 3: Embeddings Service
cd ../services/embeddings/v1.0.0
python embeddings_api.py

# Terminal 4: Metadata Service (depends on LLM Gateway)
cd ../services/metadata/v1.0.0
python metadata_api.py

# Terminal 5: Chunking Service
cd ../services/chunking/v1.0.0
python chunking_orchestrator.py
```

4. **Start main orchestrator**:
```bash
python main_ingestion_api.py
```

## Interactive API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8060/docs
- ReDoc: http://localhost:8060/redoc

## Monitoring

Check service health:
```bash
curl http://localhost:8060/health
```

Check internal service health:
```bash
curl http://localhost:8061/health  # Chunking
curl http://localhost:8062/health  # Metadata
curl http://localhost:8063/health  # Embeddings
curl http://localhost:8064/health  # Storage
curl http://localhost:8065/health  # LLM Gateway
```

## Performance

Pipeline timings (typical document with 10-20 chunks):

| Stage | Time | Configurable? |
|-------|------|---------------|
| **Chunking** | 100-500ms | ✅ Yes (method, chunk_size, overlap) |
| **Metadata** | 200-400ms/chunk | ✅ Yes (generate_metadata, field counts) |
| **Embeddings** | 50-200ms/batch | ✅ Yes (embedding_model) |
| **Storage** | 100-300ms | ❌ No (Milvus insert speed) |

**Total pipeline**: 1-3 seconds for typical documents

**Performance tips:**
- Disable metadata (`generate_metadata: false`) for 40-60% speed boost
- Use Jina v3 (1024-dim) for faster embeddings vs 4096-dim models
- Increase `max_chunk_size` to reduce chunk count and total processing time
- Use SambaNova FREE tier to avoid rate limits

## Error Handling

The API returns appropriate HTTP status codes:
- `200 OK`: Success
- `400 Bad Request`: Invalid input (check parameter values)
- `500 Internal Server Error`: Pipeline processing error
- `503 Service Unavailable`: Internal service unavailable

## Architecture Notes

1. **No APISIX**: Internal services communicate directly (INTERNAL_MODE=true)
2. **Connection Pooling**: Persistent HTTP connections to internal services
3. **Async Operations**: FastAPI with async/await for high concurrency
4. **Error Recovery**: Graceful handling of internal service failures
5. **Batch Processing**: Metadata and embeddings processed in batches for efficiency
6. **Auto-Dimension Detection**: Collection dimensions automatically match embedding model
7. **Multi-Provider Embeddings**: Jina/Nebius/SambaNova with automatic failover
8. **4 Core Metadata Fields**: Streamlined from 45 fields to keywords/topics/questions/summary

## Parameter Reference

### Chunking Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `chunking_method` | string | `recursive` | `recursive`, `markdown`, `token` | Chunking strategy |
| `max_chunk_size` | int | `1000` | 100-10000 | Max tokens per chunk |
| `chunk_overlap` | int | `300` | 0-1000 | Overlap between chunks (tokens) |
| `separators` | list | `None` | - | Custom split separators |
| `markdown_headers` | list | `None` | - | Headers for markdown method |
| `encoding` | string | `cl100k_base` | - | Tokenizer encoding |

### Metadata Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `generate_metadata` | bool | `true` | - | Enable metadata extraction |
| `keywords_count` | int | `5` | 1-20 | Number of keywords to extract |
| `topics_count` | int | `3` | 1-10 | Number of topics to extract |
| `questions_count` | int | `3` | 1-10 | Number of questions to generate |
| `summary_length` | string | `"1-2 sentences"` | - | Summary length |

**4 Fields Stored**: keywords, topics, questions, summary

### Embedding Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `generate_embeddings` | bool | `true` | Enable embedding generation |
| `embedding_model` | string | `jina-embeddings-v3` | See "Supported Embedding Models" |

### Storage Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `storage_mode` | string | `new_collection` | `new_collection`, `existing`, `none` |
| `create_collection_if_missing` | bool | `true` | Auto-create collection |

## Version

v1.0.0 - Initial release (October 2025)

**Changes from v3.0.0/v5.0.0:**
- ✅ Comprehensive parameter control (all chunking/metadata/embedding/storage parameters)
- ✅ Multi-provider embeddings (Jina/Nebius/SambaNova)
- ✅ Auto-dimension detection
- ✅ Reduced metadata fields from 45 → 4 core fields
- ✅ Smart defaults for all parameters
- ✅ Full CRUD operations for collections
