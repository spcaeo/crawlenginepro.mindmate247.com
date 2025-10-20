# Retrieval Pipeline v1.0.0

Advanced RAG (Retrieval-Augmented Generation) pipeline with multi-stage refinement.

## Overview

The Retrieval Pipeline transforms user queries into accurate, cited answers through a 4-stage process:
1. **Search** - Dense vector search with metadata boosting
2. **Reranking** - Semantic relevance scoring using BGE-Reranker-v2-M3
3. **Compression** - LLM-powered contextual compression
4. **Answer Generation** - LLM-based answer with citations

## Architecture

```
User Query
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ Retrieval API (8070) - Main Orchestrator [PLANNED]              │
└─────────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: Search Service (8071)                                   │
│ - Dense vector search (4096-dim)                                 │
│ - Metadata boosting (keywords, topics, questions, summary)       │
│ - Returns: Top 20 chunks                                         │
├──────────────────────────────────────────────────────────────────┤
│ Dependencies: Embeddings (8063), Storage (8064)                  │
└─────────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: Reranking Service (8072)                                │
│ - BGE-Reranker-v2-M3 semantic scoring                            │
│ - Cross-encoder for query-chunk relevance                        │
│ - Returns: Top 10 chunks                                         │
└─────────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: Compression Service (8073)                              │
│ - LLM-powered contextual compression                             │
│ - Extract only query-relevant sentences                          │
│ - Returns: Top 5 compressed chunks                               │
├──────────────────────────────────────────────────────────────────┤
│ Dependencies: LLM Gateway (8065)                                 │
└─────────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: Answer Generation Service (8074)                        │
│ - LLM-based answer generation                                    │
│ - Source attribution with [Source X] citations                   │
│ - Model: Llama-3.3-70B-Instruct-fast                             │
├──────────────────────────────────────────────────────────────────┤
│ Dependencies: LLM Gateway (8065)                                 │
└─────────────────────────────────────────────────────────────────┘
    ↓
Final Answer with Citations
```

## Services

### 1. Search Service (Port 8071)
**Location:** `/Retrieval/services/search/v1.0.0`

Dense vector search with metadata boosting using all 4 metadata fields.

**Features:**
- 4096-dim vector search (e5-mistral-7b-instruct)
- Metadata boosting: keywords (+0.10), topics (+0.05), questions (+0.08), summary (+0.07)
- Configurable boost weights
- Collection-based multi-tenancy

**Shared Dependencies:**
- Embeddings Service (8063) - from Ingestion pipeline
- Storage Service (8064) - from Ingestion pipeline

**API:** `POST /v1/search`

---

### 2. Reranking Service (Port 8072)
**Location:** `/Retrieval/services/reranking/v1.0.0`

Semantic relevance scoring using BGE-Reranker-v2-M3.

**Features:**
- Cross-encoder architecture (BAAI/bge-reranker-v2-m3)
- Query-chunk relevance scoring
- Handles up to 100 documents
- Returns top-N by relevance

**API:** `POST /v1/rerank`

---

### 3. Compression Service (Port 8073)
**Location:** `/Retrieval/services/compression/v1.0.0`

LLM-powered contextual compression to extract only relevant sentences.

**Features:**
- Intelligent sentence extraction
- Preserves context and meaning
- Configurable compression ratio
- Score-based filtering

**Shared Dependencies:**
- LLM Gateway (8065) - from Ingestion pipeline

**API:** `POST /v1/compress`

---

### 4. Answer Generation Service (Port 8074)
**Location:** `/Retrieval/services/answer_generation/v1.0.0`

LLM-based answer generation with source attribution.

**Features:**
- Llama-3.3-70B-Instruct-fast model
- Citation-based responses [Source X]
- Context-grounded answers only
- Redis caching support

**Shared Dependencies:**
- LLM Gateway (8065) - from Ingestion pipeline

**API:** `POST /v1/generate`

---

## Directory Structure

```
Retrieval/
├── README.md                          # This file
├── v1.0.0/                             # [PLANNED] Retrieval orchestrator API
│   ├── retrieval_api.py               # Main orchestrator (port 8070)
│   ├── config.py                      # Configuration
│   ├── models.py                      # Pydantic models
│   ├── test_stages.py                 # Stage-by-stage tester
│   └── requirements.txt               # Dependencies
└── services/
    ├── search/v1.0.0/                 # Search Service (8071)
    │   ├── search_api.py              # Main API
    │   ├── config.py                  # Configuration
    │   ├── models.py                  # Pydantic models
    │   ├── metadata_boost.py          # Metadata boosting logic
    │   └── README.md                  # Service documentation
    ├── reranking/v1.0.0/              # Reranking Service (8072)
    │   ├── reranking_api.py           # Main API
    │   ├── config.py                  # Configuration
    │   ├── models.py                  # Pydantic models
    │   └── README.md                  # Service documentation
    ├── compression/v1.0.0/            # Compression Service (8073)
    │   ├── compression_api.py         # Main API
    │   ├── config.py                  # Configuration
    │   ├── models.py                  # Pydantic models
    │   └── README.md                  # Service documentation
    ├── answer_generation/v1.0.0/      # Answer Generation (8074)
    │   ├── answer_api.py              # Main API
    │   ├── config.py                  # Configuration
    │   ├── models.py                  # Pydantic models
    │   ├── cache.py                   # Redis caching
    │   └── README.md                  # Service documentation
    └── llm_gateway@                   # Symlink to Ingestion LLM Gateway
        → ../../Ingestion/services/llm_gateway
```

## Port Allocation

All Retrieval services use ports **8070-8079**:

| Service | Port | Type | Description |
|---------|------|------|-------------|
| Retrieval API | 8070 | Public | Main orchestrator [PLANNED] |
| Search | 8071 | Internal | Dense vector + metadata boost |
| Reranking | 8072 | Internal | BGE-Reranker-v2-M3 |
| Compression | 8073 | Internal | LLM-powered compression |
| Answer Generation | 8074 | Internal | LLM with citations |
| *Reserved* | 8075-8079 | - | Future services |

## Shared Dependencies

The Retrieval pipeline **shares** these services from the Ingestion pipeline:

1. **LLM Gateway (8065)** - Nebius AI Studio proxy
   - Shared by: Compression, Answer Generation
   - Symlinked from Ingestion

2. **Embeddings Service (8063)** - e5-mistral-7b-instruct
   - Shared by: Search
   - Direct service from Ingestion

3. **Storage Service (8064)** - Milvus vector database
   - Shared by: Search
   - Direct service from Ingestion

## Installation

### Prerequisites

1. **Milvus Vector Database** running on port 19530
   - In development: SSH tunnel to production server
   - In production: Local Milvus instance

2. **Shared Ingestion Services** must be running:
   ```bash
   # Start these first from Ingestion pipeline
   - LLM Gateway (8065)
   - Embeddings Service (8063)
   - Storage Service (8064)
   ```

### Setup

```bash
cd /Users/rakesh/Desktop/CrawlEnginePro/nebius_hosting/ai_studio/hosting/PipeLineServies/Retrieval

# Each service has its own virtual environment
# Navigate to individual service directories to install
```

### Individual Service Setup

For each service (search, reranking, compression, answer_generation):

```bash
cd services/<service_name>/v1.0.0

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run service
python <service_name>_api.py
```

## Configuration

All configuration is managed via central `.env` file at:
`/PipeLineServies/.env`

**Retrieval Pipeline Configuration:**
```bash
# Retrieval Pipeline Service Ports (8070-8079)
RETRIEVAL_API_PORT=8070
SEARCH_SERVICE_PORT=8071
RERANK_SERVICE_PORT=8072
COMPRESS_SERVICE_PORT=8073
ANSWER_SERVICE_PORT=8074

# Retrieval Pipeline Service URLs
SEARCH_SERVICE_URL=http://localhost:8071/v1
RERANK_SERVICE_URL=http://localhost:8072/v1
COMPRESS_SERVICE_URL=http://localhost:8073/v1
ANSWER_SERVICE_URL=http://localhost:8074/v1

# Shared Service URLs (from Ingestion)
EMBEDDINGS_SERVICE_URL=http://localhost:8063/v3/embeddings
STORAGE_SERVICE_URL=http://localhost:8064/v1
LLM_GATEWAY_URL_DEVELOPMENT=http://localhost:8065/v1/chat/completions
```

## Running Services

### Service Startup Order

Services should be started in dependency order:

```bash
# 1. Start Ingestion shared services first
cd /PipeLineServies/Ingestion/services/llm_gateway/v1.0.0
python3 llm_gateway.py &

cd /PipeLineServies/Ingestion/services/embeddings/v1.0.0
python3 embeddings_api.py &

cd /PipeLineServies/Ingestion/services/storage/v1.0.0
python3 storage_api.py &

# 2. Start Retrieval services
cd /PipeLineServies/Retrieval/services/search/v1.0.0
python3 search_api.py &

cd /PipeLineServies/Retrieval/services/reranking/v1.0.0
python3 reranking_api.py &

cd /PipeLineServies/Retrieval/services/compression/v1.0.0
python3 compression_api.py &

cd /PipeLineServies/Retrieval/services/answer_generation/v1.0.0
python3 answer_api.py &

# 3. [PLANNED] Start Retrieval orchestrator
cd /PipeLineServies/Retrieval/v1.0.0
python3 retrieval_api.py
```

## Testing

### Stage-by-Stage Testing

Use `test_stages.py` to test individual stages or the full pipeline:

```bash
cd /PipeLineServies/Retrieval/v1.0.0

# Test individual stages
python3 test_stages.py --query "Who is the father of Hanuman?" --collection test_jaishreeram_v1 --stage 2  # Search only
python3 test_stages.py --query "Who is the father of Hanuman?" --collection test_jaishreeram_v1 --stage 3  # Search + Rerank
python3 test_stages.py --query "Who is the father of Hanuman?" --collection test_jaishreeram_v1 --stage 4  # + Compression
python3 test_stages.py --query "Who is the father of Hanuman?" --collection test_jaishreeram_v1 --stage 5  # + Answer

# Test full pipeline
python3 test_stages.py --query "Who is the father of Hanuman?" --collection test_jaishreeram_v1 --stage all

# With debug mode
python3 test_stages.py --query "Who is the father of Hanuman?" --collection test_jaishreeram_v1 --stage all --debug

# Adjust score threshold for compression filtering
python3 test_stages.py --query "Who is the father of Hanuman?" --collection test_jaishreeram_v1 --stage all --score-threshold 0.3
```

### Health Checks

```bash
# Check all Retrieval services
curl http://localhost:8071/health  # Search
curl http://localhost:8072/health  # Reranking
curl http://localhost:8073/health  # Compression
curl http://localhost:8074/health  # Answer Generation

# Check shared services
curl http://localhost:8063/health  # Embeddings
curl http://localhost:8064/health  # Storage
curl http://localhost:8065/health  # LLM Gateway
```

### Example Query Flow

```bash
# 1. Search
curl -X POST http://localhost:8071/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "Who is the father of Hanuman?",
    "collection": "test_jaishreeram_v1",
    "top_k": 20,
    "use_metadata_boost": true
  }'

# 2. Rerank
curl -X POST http://localhost:8072/v1/rerank \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Who is the father of Hanuman?",
    "chunks": [<search_results>],
    "top_k": 10
  }'

# 3. Compress
curl -X POST http://localhost:8073/v1/compress \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Who is the father of Hanuman?",
    "chunks": [<reranked_chunks>],
    "compression_ratio": 0.5,
    "score_threshold": 0.3
  }'

# 4. Generate Answer
curl -X POST http://localhost:8074/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Who is the father of Hanuman?",
    "context_chunks": [<compressed_chunks>],
    "enable_citations": true
  }'
```

## Performance Targets

| Stage | Target Latency | Typical Range |
|-------|----------------|---------------|
| Search | <100ms | 30-45ms |
| Reranking | <200ms | 50-150ms |
| Compression | <2000ms | 500-1500ms (LLM) |
| Answer Generation | <3000ms | 1000-2500ms (LLM) |
| **Full Pipeline** | **<5000ms** | **2000-4000ms** |

## Development vs Production

### Development
- All services run on `localhost` with assigned ports
- Milvus accessed via SSH tunnel:
  ```bash
  ssh -i ~/reku631_nebius -L 19530:localhost:19530 reku631@89.169.108.8
  ```
- LLM Gateway proxies to Nebius AI Studio

### Production
- All services run on `localhost` with same ports (server-side)
- Milvus runs locally (no tunnel needed)
- LLM Gateway proxies to Nebius AI Studio

**This ensures identical code in both environments.**

## Security

- All internal services bind to `0.0.0.0` but only accept local connections
- Only Retrieval API (8070) will be exposed publicly [PLANNED]
- LLM Gateway uses internal API key for service-to-service auth
- No external API keys in service code

## Next Steps

1. ✅ Setup individual services (search, reranking, compression, answer_generation)
2. ✅ Configure ports and shared dependencies
3. ✅ Create stage-by-stage test infrastructure
4. ⏳ Create Retrieval Orchestrator API (port 8070)
5. ⏳ Test full pipeline end-to-end
6. ⏳ Deploy to production server
7. ⏳ Setup monitoring and logging
8. ⏳ Integrate with frontend

## Troubleshooting

### Service won't start
```bash
# Check if port is already in use
lsof -i :8071

# Check dependencies are running
curl http://localhost:8063/health  # Embeddings
curl http://localhost:8064/health  # Storage
curl http://localhost:8065/health  # LLM Gateway
```

### LLM Gateway connection errors
```bash
# Verify LLM Gateway is running
curl http://localhost:8065/health

# Check Nebius API key is set in .env
grep NEBIUS_API_KEY /PipeLineServies/.env
```

### Milvus connection errors
```bash
# Development: Check SSH tunnel is active
ps aux | grep "ssh.*19530"

# Verify Milvus is accessible
nc -zv localhost 19530
```

## Documentation

- [PORT_ALLOCATION.md](../PORT_ALLOCATION.md) - Port allocation scheme
- [Search Service README](services/search/v1.0.0/README.md) - Search documentation
- [Reranking Service README](services/reranking/v1.0.0/README.md) - Reranking documentation
- [Compression Service README](services/compression/v1.0.0/README.md) - Compression documentation
- [Answer Generation README](services/answer_generation/v1.0.0/README.md) - Answer generation documentation

---

**Version:** 1.0.0
**Status:** Services Ready, Orchestrator Planned
**Author:** AI Studio Team
**Last Updated:** 2025-10-09
