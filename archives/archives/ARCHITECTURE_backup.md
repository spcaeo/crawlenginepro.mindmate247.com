# Pipeline Services Architecture Plan

**Created:** October 9, 2025
**Last Updated:** October 9, 2025
**Status:** Phase 1 Complete - Ingestion Pipeline Implemented ✅

---

## Implementation Status

### ✅ Completed (Ingestion Pipeline)
- [x] Directory structure created
- [x] Ingestion API implemented (port 8060)
- [x] 4 internal services integrated (ports 8061-8064)
  - Chunking (8061)
  - Metadata (8062)
  - Embeddings (8063)
  - Storage (8064)
- [x] Environment-aware configuration (development/production)
- [x] Management script (`Tools/pipeline-manager`)
- [x] Complete documentation
- [x] Backup automation scripts
- [x] Docker infrastructure documented

### 🚧 In Progress
- [ ] Testing Ingestion pipeline (Phase 10-11)

### 📋 Planned (Retrieval Pipeline)
- [ ] Retrieval API (port 8070)
- [ ] 6 internal services (ports 8071-8076)

---

## Current Folder Structure (As Built)

```
PipeLineServices/
├── .env                                # Environment configuration
├── .env.example                        # Configuration template
│
├── Docs/                               # ALL documentation
│   ├── SYSTEM_OVERVIEW_AND_USAGE.md    # System overview
│   ├── COMPLETE_DEPLOYMENT_GUIDE.md    # Complete deployment guide
│   └── ARCHITECTURE_PLAN.md            # This document
│
├── Tools/                              # Utility tools
│   ├── pipeline-manager                # Main control script
│   └── backup/                         # Backup automation
│       ├── backup_milvus.sh
│       ├── backup_postgres.sh
│       ├── backup_redis.sh
│       ├── backup_all.sh
│       └── README.md
│
├── Ingestion/                          # ✅ IMPLEMENTED
│   ├── v1.0.0/                         # Main orchestrator API
│   │   ├── ingestion_api.py            # FastAPI application (port 8060)
│   │   ├── requirements.txt
│   │   └── README.md
│   └── services/                       # Internal microservices
│       ├── chunking/v1.0.0/            # Port 8061
│       ├── metadata/v1.0.0/            # Port 8062
│       ├── embeddings/v1.0.0/          # Port 8063
│       └── storage/v1.0.0/             # Port 8064
│
└── Retrieval/                          # 📋 PLANNED
    └── (To be implemented)
```

---

## Executive Summary

This document outlines the plan to restructure the RAG system into two clean, standalone pipeline services:

1. **Ingestion Pipeline** - Document → Vector Database (write operations)
2. **Retrieval Pipeline** - Query → Answer (read operations)

**Goals:**
- ✅ Clear separation of concerns
- ✅ Single entry point per pipeline
- ✅ Internal microservices hidden from external access
- ✅ No APISIX dependency for internal communication
- ✅ Easier to understand, test, and maintain

---

## Current State Problems

### Issues with Current `/services/` Architecture
1. **Scattered services** - Hard to track which services belong to which pipeline
2. **Built incrementally** - Organic growth over time without clear structure
3. **Mixed purposes** - Ingestion and retrieval services mixed together
4. **Complex testing** - Need to call 4-5 services individually
5. **Difficult maintenance** - Changes require updating multiple services
6. **Unclear ownership** - Hard to know which service does what

---

## New Architecture Overview

```
/home/reku631/PipeLineServices/
├── Docs/
│   ├── ARCHITECTURE_PLAN.md          # This document
│   ├── INGESTION_API.md               # Ingestion API documentation
│   ├── RETRIEVAL_API.md               # Retrieval API documentation
│   └── MIGRATION_GUIDE.md             # Migration from old services
│
├── Ingestion/                         # Document Ingestion Pipeline
│   ├── v1.0.0/                       # Main ingestion orchestrator
│   │   ├── ingestion_api.py          # Port 8060 (main API)
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   ├── README.md
│   │   └── ingestion.service         # systemd service file
│   │
│   └── services/                      # Internal microservices (not exposed)
│       ├── chunking/v1.0.0/          # Port 8061
│       ├── metadata/v1.0.0/          # Port 8062
│       ├── embeddings/v1.0.0/        # Port 8063
│       └── storage/v1.0.0/           # Port 8064
│
└── Retrieval/                         # Query Retrieval Pipeline
    ├── v1.0.0/                       # Main retrieval orchestrator
    │   ├── retrieval_api.py          # Port 8070 (main API)
    │   ├── config.py
    │   ├── models.py
    │   ├── requirements.txt
    │   ├── .env.example
    │   ├── README.md
    │   └── retrieval.service         # systemd service file
    │
    └── services/                      # Internal microservices (not exposed)
        ├── llm_gateway/v1.0.0/       # Port 8071
        ├── embeddings/v1.0.0/        # Port 8072
        ├── search/v1.0.0/            # Port 8073
        ├── rerank/v1.0.0/            # Port 8074
        ├── compress/v1.0.0/          # Port 8075
        └── answer/v1.0.0/            # Port 8076
```

---

## Port Allocation Strategy

### Ingestion Pipeline (8060-8069)
| Port | Service | Access | Purpose |
|------|---------|--------|---------|
| 8060 | **Ingestion API** | Public (via APISIX) | Main orchestrator - CRUD operations |
| 8061 | Chunking | Internal only | Document chunking service |
| 8062 | Metadata | Internal only | Metadata extraction service |
| 8063 | Embeddings | Internal only | Vector embeddings generation |
| 8064 | Storage | Internal only | Milvus vector database CRUD |

### Retrieval Pipeline (8070-8079)
| Port | Service | Access | Purpose |
|------|---------|--------|---------|
| 8070 | **Retrieval API** | Public (via APISIX) | Main orchestrator - Query processing |
| 8071 | LLM Gateway | Internal only | LLM proxy (Nebius AI Studio) |
| 8072 | Embeddings | Internal only | Query embeddings generation |
| 8073 | Search | Internal only | Vector search + metadata boosting |
| 8074 | Rerank | Internal only | Semantic reranking (BGE v2-m3) |
| 8075 | Compress | Internal only | Context compression |
| 8076 | Answer | Internal only | Answer generation with citations |

**Port Range Strategy:**
- 8060-8069: Ingestion pipeline (10 ports reserved)
- 8070-8079: Retrieval pipeline (10 ports reserved)
- Clean separation, easy to remember
- Room for future expansion

---

## Ingestion Pipeline Details

### Main Orchestrator API (Port 8060)

**Endpoints:**

#### 1. Ingest Documents
```http
POST /v1/ingest
Content-Type: application/json

{
  "documents": [
    {
      "document_id": "doc_001",
      "text": "Document content...",
      "metadata": {
        "source": "uploaded",
        "filename": "example.md"
      }
    }
  ],
  "collection_name": "my_collection",
  "tenant_id": "tenant_001",
  "chunking_mode": "comprehensive",
  "metadata_mode": "basic"
}

Response:
{
  "success": true,
  "job_id": "ingest_job_12345",
  "documents_processed": 1,
  "total_chunks": 45,
  "processing_time_ms": 3245.67,
  "stats": {
    "chunking": { "time_ms": 123.45, "chunks": 45 },
    "metadata": { "time_ms": 890.12, "successful": 45 },
    "embeddings": { "time_ms": 567.89, "vectors": 45 },
    "storage": { "time_ms": 1664.21, "inserted": 45 }
  }
}
```

#### 2. Create Collection
```http
POST /v1/collections/create
Content-Type: application/json

{
  "collection_name": "my_collection",
  "tenant_id": "tenant_001",
  "dimension": 4096,
  "description": "My document collection"
}

Response:
{
  "success": true,
  "collection_name": "my_collection",
  "dimension": 4096,
  "created_at": "2025-10-09T08:00:00Z"
}
```

#### 3. Delete Collection
```http
DELETE /v1/collections/{collection_name}?tenant_id=tenant_001

Response:
{
  "success": true,
  "collection_name": "my_collection",
  "deleted_count": 450,
  "deleted_at": "2025-10-09T08:00:00Z"
}
```

#### 4. Update Document (Delete + Re-insert)
```http
PUT /v1/documents/{document_id}
Content-Type: application/json

{
  "collection_name": "my_collection",
  "tenant_id": "tenant_001",
  "text": "Updated document content...",
  "metadata": {
    "source": "updated",
    "version": 2
  }
}

Response:
{
  "success": true,
  "document_id": "doc_001",
  "operation": "replace",
  "old_chunks_deleted": 45,
  "new_chunks_inserted": 52,
  "processing_time_ms": 3456.78
}
```

#### 5. List Collections
```http
GET /v1/collections?tenant_id=tenant_001

Response:
{
  "success": true,
  "collections": [
    {
      "name": "my_collection",
      "document_count": 120,
      "chunk_count": 5432,
      "dimension": 4096,
      "created_at": "2025-10-09T08:00:00Z"
    }
  ]
}
```

#### 6. Get Collection Stats
```http
GET /v1/collections/{collection_name}/stats?tenant_id=tenant_001

Response:
{
  "success": true,
  "collection_name": "my_collection",
  "stats": {
    "total_documents": 120,
    "total_chunks": 5432,
    "total_vectors": 5432,
    "dimension": 4096,
    "avg_chunks_per_doc": 45.27,
    "storage_size_mb": 234.56,
    "last_updated": "2025-10-09T08:00:00Z"
  }
}
```

### Internal Service Flow

```
Ingestion API (8060)
    ↓
1. Chunking Service (8061)
   - Splits document into semantic chunks
   - Returns: chunks with metadata
    ↓
2. Metadata Service (8062)
   - Extracts keywords, topics, questions, summary
   - Batch processing for speed
   - Returns: metadata for each chunk
    ↓
3. Embeddings Service (8063)
   - Generates 4096-dim dense vectors
   - Uses e5-mistral-7b-instruct via Nebius API
   - Returns: vectors for each chunk
    ↓
4. Storage Service (8064)
   - Inserts chunks + vectors + metadata into Milvus
   - Returns: insertion confirmation
    ↓
Response to client with stats
```

---

## Retrieval Pipeline Details

### Main Orchestrator API (Port 8070)

**Endpoints:**

#### 1. Query (Full Pipeline)
```http
POST /v1/query
Content-Type: application/json

{
  "query": "Who is the father of Hanuman?",
  "collection_name": "my_collection",
  "tenant_id": "tenant_001",
  "options": {
    "top_k": 20,
    "rerank_top_k": 10,
    "enable_compression": true,
    "compression_ratio": 0.5,
    "enable_citations": true,
    "temperature": 0.3
  }
}

Response:
{
  "success": true,
  "query": "Who is the father of Hanuman?",
  "answer": "Hanuman's father is Kesari, the king of monkeys...",
  "citations": [
    {
      "source_id": 1,
      "chunk_id": "doc_001_chunk_12",
      "document_id": "doc_001",
      "text": "Kesari was the father of Hanuman..."
    }
  ],
  "processing_time_ms": 4567.89,
  "stats": {
    "search": { "time_ms": 234.56, "results": 20 },
    "rerank": { "time_ms": 567.89, "results": 10 },
    "compress": { "time_ms": 890.12, "results": 5 },
    "answer": { "time_ms": 2875.32, "tokens": 245 }
  }
}
```

#### 2. Search Only (No Answer Generation)
```http
POST /v1/search
Content-Type: application/json

{
  "query": "Who is the father of Hanuman?",
  "collection_name": "my_collection",
  "tenant_id": "tenant_001",
  "top_k": 20,
  "use_metadata_boost": true
}

Response:
{
  "success": true,
  "query": "Who is the father of Hanuman?",
  "results": [
    {
      "chunk_id": "doc_001_chunk_12",
      "document_id": "doc_001",
      "text": "Kesari was the father of Hanuman...",
      "score": 0.8756,
      "vector_score": 0.7823,
      "metadata_boost": 0.0933,
      "metadata": {
        "keywords": "Hanuman, Kesari, father",
        "topics": "Hindu mythology, Ramayana",
        "summary": "Description of Hanuman's parentage"
      }
    }
  ],
  "total_results": 20,
  "processing_time_ms": 234.56
}
```

### Internal Service Flow

```
Retrieval API (8070)
    ↓
1. Embeddings Service (8072)
   - Converts query to 4096-dim vector
   - Returns: query vector
    ↓
2. Search Service (8073)
   - Dense vector search in Milvus
   - Applies metadata boosting
   - Returns: top_k results with scores
    ↓
3. Rerank Service (8074)
   - Semantic reranking using BGE v2-m3
   - Returns: top_k reranked results
    ↓
4. Compress Service (8075)
   - LLM-powered context compression
   - Filters by score threshold
   - Returns: compressed context chunks
    ↓
5. Answer Service (8076)
   - Generates answer using Llama-3.3-70B
   - Includes citations
   - Returns: answer with sources
    ↓
Response to client with answer + citations
```

**Note:** LLM Gateway (8071) is used by both Compress and Answer services for LLM calls.

---

## Service Dependencies

### Ingestion Pipeline Dependencies
```
Ingestion API (8060)
    ├── Chunking (8061) - No dependencies
    ├── Metadata (8062) - Depends on: LLM Gateway (external call to 8000)
    ├── Embeddings (8063) - Depends on: Nebius AI Studio API
    └── Storage (8064) - Depends on: Milvus (localhost:19530)
```

### Retrieval Pipeline Dependencies
```
Retrieval API (8070)
    ├── LLM Gateway (8071) - Depends on: Nebius AI Studio API
    ├── Embeddings (8072) - Depends on: Nebius AI Studio API
    ├── Search (8073) - Depends on: Milvus (localhost:19530)
    ├── Rerank (8074) - Depends on: Jina AI Reranking API
    ├── Compress (8075) - Depends on: LLM Gateway (8071)
    └── Answer (8076) - Depends on: LLM Gateway (8071)
```

---

## Migration Strategy

### Phase 1: Planning & Design ✅
- [x] Create architecture plan
- [x] Define API endpoints
- [x] Allocate ports
- [ ] Review and approve plan

### Phase 2: Ingestion Pipeline ✅ COMPLETE
1. **Create directory structure** ✅ (Day 1)
   - [x] Create `/PipeLineServices/Ingestion/` folders
   - [x] Copy current services as v1.0.0
   - [x] Update port numbers (8061-8064)

2. **Build Ingestion API** ✅ (Day 2-3)
   - [x] Create `ingestion_api.py` main orchestrator
   - [x] Implement all CRUD endpoints (ingest, create, delete, update)
   - [x] Add error handling and logging

3. **Update internal services** ✅ (Day 3-4)
   - [x] Update chunking service (port 8061)
   - [x] Update metadata service (port 8062)
   - [x] Update embeddings service (port 8063)
   - [x] Update storage service (port 8064)
   - [x] Implement environment-aware configuration

4. **Testing** 🚧 (Day 4-5) - IN PROGRESS
   - [ ] Test internal services individually
   - [ ] Test full Ingestion API
   - [ ] Performance testing
   - [ ] Fix bugs

5. **Deployment** 📋 (Day 5)
   - [ ] Create systemd service file
   - [ ] Deploy to server
   - [ ] Configure UFW firewall
   - [ ] Add APISIX route (if needed)

### Phase 3: Retrieval Pipeline (Week 2)
1. **Create directory structure** (Day 1)
   - Create `/PipeLineServices/Retrieval/` folders
   - Copy current services as v1.0.0
   - Update port numbers

2. **Build Retrieval API** (Day 2-3)
   - Create `retrieval_api.py` main orchestrator
   - Implement query endpoints
   - Add error handling and logging

3. **Update internal services** (Day 3-4)
   - Update LLM gateway (port 8071)
   - Update embeddings service (port 8072)
   - Update search service (port 8073)
   - Update rerank service (port 8074)
   - Update compress service (port 8075)
   - Update answer service (port 8076)

4. **Testing** (Day 4-5)
   - Create retrieval tester script
   - Test all endpoints
   - Performance testing
   - Fix bugs

5. **Deployment** (Day 5)
   - Create systemd service file
   - Deploy to server
   - Configure UFW firewall
   - Add APISIX route

### Phase 4: Documentation & Cleanup (Week 3)
1. **Documentation**
   - Write INGESTION_API.md
   - Write RETRIEVAL_API.md
   - Write MIGRATION_GUIDE.md
   - Update VM_SETUP_GUIDE.md

2. **Cleanup**
   - Archive old `/services/` folder
   - Remove deprecated services
   - Update all documentation

3. **Monitoring**
   - Monitor for 1 week
   - Performance optimization
   - Bug fixes

---

## Benefits of New Architecture

### For Developers
✅ **Clear structure** - Know exactly where to find code
✅ **Single entry point** - One API per pipeline
✅ **Easy testing** - Test one endpoint instead of many
✅ **Better debugging** - Clear service boundaries
✅ **Version control** - Clean v1.0.0 baseline

### For Operations
✅ **Simplified deployment** - Deploy entire pipeline at once
✅ **Better monitoring** - Monitor 2 services instead of 10
✅ **Easier scaling** - Scale pipelines independently
✅ **Clear logs** - Pipeline-level logging
✅ **Reduced complexity** - Fewer moving parts

### For Users
✅ **Simpler API** - One endpoint for ingestion, one for retrieval
✅ **Better performance** - Optimized internal communication
✅ **More reliable** - Fewer failure points
✅ **Clearer errors** - Pipeline-level error messages

---

## Technical Specifications

### Technology Stack
- **Language:** Python 3.12
- **Framework:** FastAPI
- **HTTP Client:** httpx (async)
- **Vector DB:** Milvus 2.4.1
- **LLM Provider:** Nebius AI Studio
- **Embeddings:** e5-mistral-7b-instruct (4096-dim)
- **Reranker:** Jina AI (BGE v2-m3)

### Configuration Management
- **Environment:** .env files per service
- **Secrets:** Environment variables
- **Service URLs:** Configurable via .env
- **Ports:** Configurable via .env

### Error Handling
- **HTTP Errors:** Proper status codes (400, 404, 500)
- **Validation:** Pydantic models
- **Timeouts:** Configurable per service
- **Retries:** Exponential backoff for external APIs
- **Logging:** Structured JSON logs

### Security
- **Internal Services:** Localhost-only access
- **Main APIs:** APISIX authentication
- **API Keys:** Environment variables
- **Rate Limiting:** Via APISIX
- **Input Validation:** Pydantic models

---

## Success Criteria

### Functional Requirements
- [ ] Ingestion API accepts documents and stores in Milvus
- [ ] Retrieval API accepts queries and returns answers with citations
- [ ] All internal services communicate successfully
- [ ] CRUD operations work correctly
- [ ] Error handling works as expected

### Performance Requirements
- [ ] Ingestion: <5s per document (avg 1000 chars)
- [ ] Retrieval: <5s per query (full pipeline)
- [ ] Search only: <500ms per query
- [ ] 95th percentile latency <10s for full pipeline

### Quality Requirements
- [ ] 100% test coverage for main APIs
- [ ] Zero critical bugs in production
- [ ] All documentation complete
- [ ] Clean code (linting, typing)
- [ ] Proper logging and monitoring

---

## Risks & Mitigation

### Risk 1: Service Migration Breaks Production
**Mitigation:** Keep old `/services/` folder until new pipelines are stable

### Risk 2: Port Conflicts
**Mitigation:** Carefully allocated port ranges (8060-8069, 8070-8079)

### Risk 3: Performance Degradation
**Mitigation:** Benchmark before and after, optimize if needed

### Risk 4: Service Communication Failures
**Mitigation:** Proper error handling, retries, timeouts

### Risk 5: Data Loss During Migration
**Mitigation:** Backup Milvus data before migration

---

## Next Steps

1. **Review this plan** - Get approval from stakeholders
2. **Create detailed API specs** - Write INGESTION_API.md and RETRIEVAL_API.md
3. **Start Phase 2** - Build Ingestion pipeline
4. **Weekly check-ins** - Track progress, adjust as needed

---

## Questions & Decisions Needed

- [ ] Should Ingestion API be publicly accessible or internal-only?
- [ ] Should we keep old `/services/` folder as backup or delete after migration?
- [ ] Do we need APISIX for the new pipeline APIs?
- [ ] What authentication method for the new APIs?
- [ ] Should we version the main APIs (v1.0.0, v2.0.0)?

---

**End of Architecture Plan**
