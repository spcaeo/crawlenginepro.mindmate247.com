# CrawlEnginePro - Multi-Embedding RAG Pipeline System

**Version 1.0.0** | FastAPI Microservices Architecture

Complete Ingestion and Retrieval pipelines for Retrieval-Augmented Generation (RAG) with support for multiple embedding providers.

---

## 🚀 Quick Start

### Development (Local Machine)

```bash
# 1. Start SSH tunnel to server infrastructure (Terminal 1)
ssh -i ~/reku631_nebius -L 19530:localhost:19530 -L 3000:localhost:3000 reku631@89.169.108.8

# 2. Start all services (Terminal 2)
cd /path/to/crawlenginepro.mindmate247.com/local_dev
./start_all_services.sh

# 3. Verify health
curl http://localhost:8070/health
```

### Server Deployment

```bash
# On server (89.169.108.8)
cd /var/www/CrawlEnginePro/code

# Staging environment
./deploy/manage.sh staging start

# Production environment
./deploy/manage.sh production start
```

---

## Table of Contents

1. [Overview](#overview)
2. [Multi-Environment Architecture](#multi-environment-architecture)
3. [Ingestion Pipeline](#ingestion-pipeline)
4. [Retrieval Pipeline](#retrieval-pipeline)
5. [Directory Structure](#directory-structure)
6. [Configuration](#configuration)
7. [Development Setup](#development-setup)
8. [Deployment](#deployment)
9. [API Documentation](#api-documentation)
10. [Troubleshooting](#troubleshooting)

---

## Overview

CrawlEnginePro provides two main pipelines:

### Ingestion Pipeline ✅
**Purpose**: Process documents and store them in vector database

**Flow**:
```
Document → Chunking → Metadata → Embeddings → Storage → Milvus
```

**Key Features**:
- Multiple embedding providers (Jina AI, Nebius AI)
- **Automatic dimension detection** - Collections auto-sized for embedding dimensions
- Flexible chunking strategies (simple, semantic, comprehensive)
- LLM-powered metadata extraction
- Multi-collection support with isolated tenant data

### Retrieval Pipeline ✅
**Purpose**: Search vectors and generate RAG-powered answers

**Flow**:
```
Query → [Intent Detection] → Search → Rerank → Compress → Answer → User
         (parallel)
```

**Key Features**:
- Intent-aware prompts with 15 specialized intent types
- Custom markdown formatting per query type
- Jina AI reranker support (3.5x faster than BGE)
- LLM-powered contextual compression
- Citation-enabled answer generation

---

## Multi-Environment Architecture

CrawlEnginePro supports three isolated environments with dedicated port ranges:

### Production (8060-8069, 8110-8119)
**Primary environment on server**

- Ingestion API: 8060
- Internal Services: 8061-8065
- Retrieval API: 8110
- Internal Services: 8111-8115

### Staging (8080-8089, 8100-8109)
**Pre-production testing on server**

- Ingestion API: 8080
- Internal Services: 8081-8085
- Retrieval API: 8100
- Internal Services: 8101-8105

### Development (8070-8079, 8090-8099)
**Local development via SSH tunnel**

- Ingestion API: 8070
- Internal Services: 8071-8075
- Retrieval API: 8090
- Internal Services: 8091-8095

### External Dependencies
- **Milvus**: Port 19530 (vector database)
- **Attu UI**: Port 3000 (Milvus admin interface)

> **Complete port allocation details**: See [PORT_ALLOCATION.md](PORT_ALLOCATION.md)

---

## Ingestion Pipeline

### Services (Development Ports)

| Service | Port | Description |
|---------|------|-------------|
| **Ingestion API** | 8070 | Main orchestrator - Public API |
| Chunking Service | 8071 | Document chunking strategies |
| Metadata Service | 8072 | LLM-powered metadata extraction |
| Embeddings Service | 8073 | Multi-provider embedding generation |
| Storage Service | 8074 | Milvus vector database operations |
| LLM Gateway | 8075 | Nebius AI Studio proxy |

### Key Endpoints

```bash
# Ingest document
POST /v1/ingest

# Create collection
POST /v1/collections

# Update document
PUT /v1/documents/{doc_id}

# Delete document
DELETE /v1/documents/{doc_id}

# Delete collection
DELETE /v1/collections/{collection_name}
```

### Supported Embedding Providers

| Provider | Model | Dimensions | Cost | Status |
|----------|-------|------------|------|--------|
| **Jina AI** | jina-embeddings-v3 | 1024 | $0.02/M tokens | ✅ Supported |
| **SambaNova** | Not Available | - | - | ❌ Not Supported |
| **Nebius** | intfloat/e5-mistral-7b-instruct | 4096 | Varies | ✅ Supported |

**Active LLM Provider**: SambaNova (see `shared/model_registry.py:198` - `ACTIVE_PRESET = ProviderPreset.SAMBANOVA_FAST`)

**Embedding Comparison Results** (JaiShreeRam.md - 242 lines, 17.1KB):
- **Jina V3** (1024 dims): 12.1s total, 4x storage efficiency
- **Nebius E5** (4096 dims): 12.3s total, higher accuracy for RAG
- Test script: `local_dev/test_embeddings_comparison.py`

### Example Ingestion Request

```json
{
  "text": "CrawlEnginePro is a powerful multi-embedding RAG pipeline system...",
  "document_id": "doc_001",
  "collection_name": "my_collection",
  "embedding_model": "jina-embeddings-v3",
  "chunking_strategy": "comprehensive",
  "max_chunk_size": 500,
  "chunk_overlap": 100,
  "metadata_mode": "basic"
}
```

---

## Retrieval Pipeline

### Services (Development Ports)

| Service | Port | Description |
|---------|------|-------------|
| **Retrieval API** | 8090 | Main orchestrator - Public API |
| Search Service | 8091 | Dense vector + metadata boosting |
| Reranking Service | 8092 | BGE or Jina AI reranking |
| Compression Service | 8093 | LLM-powered context compression |
| Answer Generation | 8094 | LLM with citations |
| Intent Service | 8095 | Intent detection & prompt adaptation |

### Intent-Aware System

**15-Intent Taxonomy**:

| Group | Intents |
|-------|---------|
| **Core Retrieval** | simple_lookup, list_enumeration, yes_no, definition_explanation, factual_retrieval |
| **Analytical** | comparison, aggregation, temporal, relationship_mapping, contextual_explanation |
| **Advanced Logic** | negative_logic, cross_reference, synthesis |
| **Meta/Structural** | document_navigation, exception_handling |

Each intent has custom markdown formatting for optimal answer presentation.

### Reranking Options

| Backend | Performance | Requirements |
|---------|-------------|--------------|
| **BGE** (default) | ~2,700ms/20 chunks | Local CPU/GPU |
| **Jina AI** | ~780ms/20 chunks | API key |

**Speed Improvement**: 3.5x faster with Jina AI!

### Example Retrieval Request

```json
{
  "query": "What are the key features of CrawlEnginePro?",
  "collection_name": "my_collection",
  "top_k": 10,
  "rerank_top_k": 5,
  "use_compression": true,
  "include_citations": true
}
```

---

## Directory Structure

```
code/
├── README.md                      # This file
├── PORT_ALLOCATION.md             # Complete port allocation guide
├── .env                           # Symlink to shared/.env.dev
├── .env.example                   # Configuration template
│
├── shared/                        # Shared configuration
│   ├── .env.dev                   # Development config (8070-8095)
│   ├── .env.staging               # Staging config (8080-8109)
│   ├── .env.prod                  # Production config (8060-8069, 8110-8119)
│   └── model_registry.py          # Central model registry
│
├── Ingestion/                     # Ingestion Pipeline
│   ├── v1.0.0/
│   │   ├── main_ingestion_api.py  # Main orchestrator
│   │   └── requirements.txt
│   └── services/
│       ├── storage/v1.0.0/        # Milvus operations
│       ├── embeddings/v1.0.0/     # Embedding generation
│       ├── llm_gateway/v1.0.0/    # LLM proxy
│       ├── metadata/v1.0.0/       # Metadata extraction
│       └── chunking/v1.0.0/       # Document chunking
│
├── Retrieval/                     # Retrieval Pipeline
│   ├── v1.0.0/
│   │   ├── main_retrieval_api.py  # Main orchestrator
│   │   └── requirements.txt
│   └── services/
│       ├── search/v1.0.0/         # Vector search
│       ├── reranking/v1.0.0/      # Result reranking
│       ├── compression/v1.0.0/    # Context compression
│       ├── answer_generation/v1.0.0/  # Answer generation
│       └── intent/v1.0.0/         # Intent detection
│
├── deploy/                        # Deployment scripts
│   ├── manage.sh                  # Multi-environment service manager
│   ├── deploy.sh                  # Deploy to server
│   └── server_setup.sh            # Initial server setup
│
└── archives/                      # Archived documentation
    ├── COMPLETE_STATUS.md
    ├── HANDOVER_OLD.md
    ├── TESTING_GUIDE.md
    └── code_backup_20251017_094220/
```

---

## Configuration

### Environment Files

Each environment has its own configuration in `shared/`:

- **shared/.env.dev** - Development (ports 8070-8095)
- **shared/.env.staging** - Staging (ports 8080-8109)
- **shared/.env.prod** - Production (ports 8060-8069, 8110-8119)

### Key Configuration Variables

```bash
# Environment
ENVIRONMENT=development

# API Keys
NEBIUS_API_KEY=your_nebius_api_key
JINA_API_KEY=your_jina_api_key
SAMBANOVA_API_KEY=your_sambanova_api_key

# Service Ports (Development)
INGESTION_API_PORT=8070
CHUNKING_SERVICE_PORT=8071
METADATA_SERVICE_PORT=8072
EMBEDDINGS_SERVICE_PORT=8073
STORAGE_SERVICE_PORT=8074
LLM_GATEWAY_SERVICE_PORT=8075

# Milvus Configuration
MILVUS_HOST_DEVELOPMENT=localhost  # Via SSH tunnel
MILVUS_PORT_DEVELOPMENT=19530
MILVUS_HOST_PRODUCTION=localhost   # Direct connection
MILVUS_PORT_PRODUCTION=19530

# Performance Tuning
ENABLE_CACHE=false                 # LLM response caching
CACHE_TTL=7200                     # 2 hours
MAX_PARALLEL_LLM_CALLS=20          # Concurrency limit

# Reranking
RERANKER_BACKEND=jina              # "jina" or "bge"
```

### Port Environment Variable Pattern

All services read PORT from environment using:

```python
DEFAULT_PORT = int(os.getenv("PORT", "8062"))  # Example for metadata service
```

This allows flexible port assignment without code changes.

---

## Development Setup

### Prerequisites

1. **Python 3.11+**
2. **SSH access to server** (89.169.108.8)
3. **SSH key**: `~/reku631_nebius`
4. **API keys**: Nebius, Jina AI (optional), SambaNova (optional)

### Step 1: Clone Repository

```bash
cd /path/to/your/workspace
git clone <repository-url> crawlenginepro.mindmate247.com
cd crawlenginepro.mindmate247.com
```

### Step 2: Create Local Python Environment

```bash
# Create virtual environment
python3 -m venv local_dev/venv

# Activate environment
source local_dev/venv/bin/activate

# Install dependencies for all services
cd code
pip install -r Ingestion/v1.0.0/requirements.txt
pip install -r Ingestion/services/storage/v1.0.0/requirements.txt
pip install -r Ingestion/services/embeddings/v1.0.0/requirements.txt
pip install -r Ingestion/services/metadata/v1.0.0/requirements.txt
pip install -r Ingestion/services/chunking/v1.0.0/requirements.txt
pip install -r Ingestion/services/llm_gateway/v1.0.0/requirements.txt
```

### Step 3: Configure Environment

```bash
cd code
cp .env.example shared/.env.dev

# Edit configuration
vim shared/.env.dev

# Add your API keys:
# NEBIUS_API_KEY=your_key_here
# JINA_API_KEY=your_key_here
# SAMBANOVA_API_KEY=your_key_here
```

### Step 4: Start SSH Tunnel

**CRITICAL**: SSH tunnel must be running before starting services!

```bash
# Terminal 1 - Keep this running
ssh -i ~/reku631_nebius \
  -L 19530:localhost:19530 \
  -L 3000:localhost:3000 \
  reku631@89.169.108.8
```

This tunnels:
- **Port 19530**: Milvus vector database
- **Port 3000**: Attu UI (Milvus admin interface)

### Step 5: Start Services

```bash
# Terminal 2
cd /path/to/crawlenginepro.mindmate247.com/local_dev
./start_all_services.sh
```

This starts all 6 ingestion services in the correct dependency order.

### Step 6: Verify

```bash
# Check health
curl http://localhost:8070/health

# View API docs
open http://localhost:8070/docs

# View Attu UI
open http://localhost:3000
```

### Service Logs

Logs are written to `local_dev/*.log`:

```bash
tail -f local_dev/ingestion.log
tail -f local_dev/metadata.log
tail -f local_dev/llm_gateway.log
```

---

## Deployment

### Server Environments

The production server (89.169.108.8) runs three isolated environments:

1. **Production** - Live traffic (ports 8060-8069, 8110-8119)
2. **Staging** - Pre-production testing (ports 8080-8109)
3. **Development** - Server-side development (ports 8070-8095)

### Deployment Workflow

```bash
# 1. Test locally
cd local_dev
./start_all_services.sh
# Run tests...

# 2. Deploy to server
cd ../code
./deploy/deploy.sh

# 3. SSH to server
ssh -i ~/reku631_nebius reku631@89.169.108.8

# 4. Setup environment (first time only)
cd /var/www/CrawlEnginePro/code
./deploy/server_setup.sh staging

# 5. Start staging services
./deploy/manage.sh staging start

# 6. Test staging
./deploy/manage.sh staging status
./deploy/manage.sh staging health

# 7. Deploy to production
./deploy/manage.sh production start
```

### Management Commands

```bash
# Start environment
./deploy/manage.sh {dev|staging|production} start

# Stop environment
./deploy/manage.sh {dev|staging|production} stop

# Restart environment
./deploy/manage.sh {dev|staging|production} restart

# Check status
./deploy/manage.sh {dev|staging|production} status

# View logs
./deploy/manage.sh {dev|staging|production} logs {service}

# Start individual service
./deploy/manage.sh {dev|staging|production} start {service}
```

---

## API Documentation

### Ingestion API (Development: 8070, Production: 8060)

#### Ingest Document

```bash
curl -X POST http://localhost:8070/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "CrawlEnginePro is a powerful RAG pipeline system...",
    "document_id": "doc_001",
    "collection_name": "my_collection",
    "embedding_model": "jina-embeddings-v3",
    "chunking_strategy": "comprehensive",
    "max_chunk_size": 500,
    "chunk_overlap": 100,
    "metadata_mode": "basic"
  }'
```

#### Create Collection

```bash
curl -X POST http://localhost:8070/v1/collections \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "new_collection",
    "dimension": 1024,
    "description": "My new collection"
  }'
```

#### Update Document

```bash
curl -X PUT http://localhost:8070/v1/documents/doc_001 \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Updated document content...",
    "collection_name": "my_collection"
  }'
```

#### Delete Document

```bash
curl -X DELETE "http://localhost:8070/v1/documents/doc_001?collection_name=my_collection"
```

#### Delete Collection

```bash
curl -X DELETE http://localhost:8070/v1/collections/my_collection
```

### Retrieval API (Development: 8090, Production: 8110)

#### Retrieve and Generate Answer

```bash
curl -X POST http://localhost:8090/v1/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the key features of CrawlEnginePro?",
    "collection_name": "my_collection",
    "top_k": 10,
    "rerank_top_k": 5,
    "use_compression": true,
    "include_citations": true
  }'
```

### Interactive Documentation

Each API provides Swagger UI documentation:

- **Development**:
  - Ingestion: http://localhost:8070/docs
  - Retrieval: http://localhost:8090/docs

- **Production**:
  - Ingestion: http://localhost:8060/docs
  - Retrieval: http://localhost:8110/docs

---

## Troubleshooting

### SSH Tunnel Issues

**Problem**: Connection refused to Milvus

```bash
# Check tunnel is running
lsof -i :19530

# Restart tunnel
ssh -i ~/reku631_nebius -L 19530:localhost:19530 -L 3000:localhost:3000 reku631@89.169.108.8
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8070

# Kill process
kill -9 <PID>

# Or kill all services on development ports
lsof -ti:8070,8071,8072,8073,8074,8075 | xargs kill -9
```

### Service Won't Start

1. **Check environment variables**:
   ```bash
   python3 -c "from dotenv import dotenv_values; print(dotenv_values('shared/.env.dev'))"
   ```

2. **Check logs**:
   ```bash
   tail -f local_dev/{service}.log
   ```

3. **Verify dependencies**:
   - SSH tunnel running (development only)
   - Milvus accessible: `curl http://localhost:19530`
   - Python environment activated

### Health Check Fails

```bash
# Check individual service health
curl http://localhost:8070/health  # Ingestion API
curl http://localhost:8071/health  # Chunking
curl http://localhost:8072/health  # Metadata
curl http://localhost:8073/health  # Embeddings
curl http://localhost:8074/health  # Storage
curl http://localhost:8075/health  # LLM Gateway

# Check dependency services
curl http://localhost:19530  # Milvus
open http://localhost:3000   # Attu UI
```

### Ingestion Fails

1. **Verify Milvus connection**:
   ```bash
   curl http://localhost:19530
   open http://localhost:3000  # Check collections in Attu
   ```

2. **Check API keys**:
   ```bash
   grep NEBIUS_API_KEY shared/.env.dev
   grep JINA_API_KEY shared/.env.dev
   ```

3. **Test embedding service directly**:
   ```bash
   curl -X POST http://localhost:8073/v1/embeddings \
     -H "Content-Type: application/json" \
     -d '{"texts": ["test"], "model": "jina-embeddings-v3"}'
   ```

4. **Dimension mismatch errors** (Fixed in v1.0.0):
   - Error: "the dim (4096) of field data(dense_vector) is not equal to schema dim (1024)"
   - **Root Cause**: Storage service was not detecting vector dimensions from chunk data
   - **Fix**: Automatic dimension detection added to `operations.py:insert_chunks()`
   - Collections now auto-size based on actual embedding dimensions
   - See: `code/Ingestion/services/storage/v1.0.0/operations.py:240-246`

### Performance Issues

1. **Enable caching** (in shared/.env.dev):
   ```bash
   ENABLE_CACHE=true
   CACHE_TTL=7200
   ```

2. **Adjust concurrency**:
   ```bash
   MAX_PARALLEL_LLM_CALLS=20  # Reduce if hitting rate limits
   ```

3. **Use Jina AI reranker** (faster than BGE):
   ```bash
   RERANKER_BACKEND=jina
   JINA_AI_KEY=your_key_here
   ```

---

## Key Features

### ✅ Multi-Embedding Support
- Jina AI (1024 dims, $0.02/M tokens)
- Nebius AI (4096 dims, E5-Mistral-7B)
- **Automatic dimension detection** from chunk vectors

### ✅ Flexible Chunking
- Simple (fixed size)
- Semantic (meaning-based)
- Comprehensive (multi-strategy)

### ✅ LLM-Powered Metadata
- Keywords extraction
- Topic identification
- Question generation
- Summary creation

### ✅ Intent-Aware Retrieval
- 15-intent taxonomy
- Custom markdown formatting
- Parallel execution (zero latency)
- 94% classification accuracy

### ✅ Advanced Reranking
- BGE Reranker-v2-M3 (default)
- Jina AI Reranker (3.5x faster)
- Configurable top-k

### ✅ Multi-Environment Support
- Development (local)
- Staging (server)
- Production (server)
- Isolated port ranges

### ✅ Production-Ready
- FastAPI async architecture
- Connection pooling
- Rate limiting
- Comprehensive logging
- Health monitoring
- Error handling

---

## System Requirements

### Development Machine
- Python 3.11+
- 8GB RAM minimum
- SSH client
- Internet connection

### Production Server
- Ubuntu 20.04+
- Python 3.11+
- Docker & Docker Compose
- 16GB RAM minimum
- 50GB disk space

### External Services
- Milvus v2.4.1+ (vector database)
- Nebius AI Studio (LLM & embeddings)
- Jina AI (optional, for reranking)
- SambaNova AI (optional, for embeddings)

---

## Performance Benchmarks

### Ingestion Pipeline (Real Test Results - JaiShreeRam.md, 242 lines, 17.1KB)

**Jina V3 (1024 dims):**
- **Chunking**: ~5ms (22 chunks)
- **Metadata Extraction**: ~2,497ms (parallel, LLM-powered)
- **Embeddings**: ~2,497ms (parallel, Jina AI)
- **Storage**: ~9,418ms (Milvus insertion)
- **Total**: 12,087ms (12.1s)

**Nebius E5 (4096 dims):**
- **Chunking**: ~11ms (22 chunks)
- **Metadata Extraction**: ~2,513ms (parallel, LLM-powered)
- **Embeddings**: ~2,513ms (parallel, Nebius AI)
- **Storage**: ~9,671ms (Milvus insertion)
- **Total**: 12,252ms (12.3s)

**Key Findings:**
- Nearly identical performance (1.01x difference)
- Jina V3: 4x storage efficiency (1024 vs 4096 dims)
- Nebius E5: Higher dimensional for complex RAG tasks

### Retrieval Pipeline
- **Search**: ~200ms for top-10 results
- **Reranking**: ~780ms (Jina AI) / 2,700ms (BGE)
- **Compression**: ~1,500ms (LLM-powered)
- **Answer**: ~3,000ms (LLM generation)

**Total End-to-End**: ~6-8 seconds per query

---

## Security Considerations

1. **API Keys**: Store in `.env` files, never commit to git
2. **SSH Keys**: Use secure key-based authentication
3. **Network**: Services run on localhost, not exposed externally
4. **Tenant Isolation**: Multi-tenant data isolation in Milvus
5. **Rate Limiting**: Built-in per-service rate limits

---

## Contributing

When contributing to this project:

1. Follow existing code structure
2. Update documentation for any changes
3. Test in development environment first
4. Deploy to staging before production
5. Keep PORT_ALLOCATION.md updated
6. Update this README for new features

---

## License

Proprietary - All rights reserved

---

## Support

For issues or questions:

1. Check [PORT_ALLOCATION.md](PORT_ALLOCATION.md) for port configuration
2. Review service logs in `local_dev/*.log`
3. Check troubleshooting section above
4. Contact system administrator

---

**Last Updated**: October 17, 2025

**Status**: Production Ready ✅

**Environments**: 3 (Development, Staging, Production)

**Services**: 12 microservices across 2 pipelines
