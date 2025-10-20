# PipeLineServices

Unified Ingestion and Retrieval pipelines for RAG system with vector database storage.

## Quick Start

### Using the Management Script (Recommended)

```bash
# Show all available commands
./Tools/pipeline-manager help

# Start everything (SSH tunnel + all services)
./Tools/pipeline-manager start

# Check status
./Tools/pipeline-manager status

# Check health
./Tools/pipeline-manager health

# Stop everything
./Tools/pipeline-manager stop
```

### Manual Setup

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed manual setup instructions.

---

## What is PipeLineServices?

PipeLineServices provides two main pipelines:

### 1. Ingestion Pipeline (Port 8060)

**Purpose**: Process documents and store them in vector database

**Flow**:
```
Document → Chunking → Metadata → Embeddings → Storage → Milvus
```

**API Endpoints**:
- `POST /v1/ingest` - Ingest a document
- `POST /v1/collections` - Create collection
- `DELETE /v1/collections/{name}` - Delete collection
- `PUT /v1/documents/{doc_id}` - Update document
- `DELETE /v1/documents/{doc_id}` - Delete document

### 2. Retrieval Pipeline (Port 8070) - Coming Soon

**Purpose**: Search vectors and generate answers

**Flow**:
```
Query → Embeddings → Search → Rerank → Compress → Answer → User
```

---

## Architecture

### Development Environment (Local Machine)

```
┌─────────────────────────────────────────────────────┐
│           Production Server (via SSH tunnel)        │
│  ┌──────────┐  ┌─────────┐  ┌─────────────┐       │
│  │  Milvus  │  │ Attu UI │  │ LLM Gateway │       │
│  │  :19530  │  │  :3000  │  │    :8000    │       │
│  └────┬─────┘  └────┬────┘  └──────┬──────┘       │
└───────┼─────────────┼───────────────┼──────────────┘
        │             │               │
        └─────────────┴───────────────┘
                      │
              SSH Tunnel (./Tools/pipeline-manager tunnel)
                      │
┌───────────────────────┼───────────────────────────┐
│                       │                            │
│            Local PipeLineServices                  │
│                                                    │
│    ┌──────────────────────────────────────┐      │
│    │   Ingestion API (port 8060)          │      │
│    │        Main Orchestrator             │      │
│    └──────────┬───────────────────────────┘      │
│               │                                    │
│    ┌──────────┴───────────────────────────┐      │
│    │        Internal Services             │      │
│    │  - Chunking     (8061)               │      │
│    │  - Metadata     (8062)               │      │
│    │  - Embeddings   (8063)               │      │
│    │  - Storage      (8064)               │      │
│    └──────────────────────────────────────┘      │
│                                                    │
└────────────────────────────────────────────────────┘
```

### Production Environment (Server)

All services run locally on the server, no SSH tunnel needed.

---

## Management Commands

### Starting Services

```bash
# Start everything (recommended)
./Tools/pipeline-manager start

# Start only SSH tunnel
./Tools/pipeline-manager tunnel

# Start individual services
./Tools/pipeline-manager storage      # Port 8064
./Tools/pipeline-manager embeddings   # Port 8063
./Tools/pipeline-manager metadata     # Port 8062
./Tools/pipeline-manager chunking     # Port 8061
./Tools/pipeline-manager ingestion    # Port 8060 (main API)
```

### Monitoring

```bash
# Check if services are running
./Tools/pipeline-manager status

# Check if services are healthy
./Tools/pipeline-manager health

# View API documentation
./Tools/pipeline-manager api-docs

# Open Attu UI (Milvus admin)
./Tools/pipeline-manager attu
```

### Stopping Services

```bash
# Stop all services and tunnel
./Tools/pipeline-manager stop

# Restart everything
./Tools/pipeline-manager restart
```

### Documentation

```bash
# Open main README (this file)
./Tools/pipeline-manager docs

# Open deployment guide (SSH tunnel, Docker, disaster recovery)
./Tools/pipeline-manager deployment

# Open architecture plan (technical specs)
./Tools/pipeline-manager arch
```

---

## Directory Structure

```
PipeLineServices/
├── README.md                   # This file (system overview)
├── DEPLOYMENT.md               # Complete deployment guide
├── ARCHITECTURE.md             # Architecture & technical specs
├── .env                        # Shared environment config
├── .env.example                # Example environment config
│
├── Tools/                      # Management tools
│   ├── pipeline-manager        # Service management script
│   └── backup/                 # Backup scripts
│       ├── backup_milvus.sh
│       ├── backup_postgres.sh
│       ├── backup_redis.sh
│       ├── backup_all.sh
│       └── README.md
│
├── Ingestion/                  # Ingestion Pipeline
│   ├── v1.0.0/                 # Main orchestrator (port 8060)
│   │   ├── ingestion_api.py
│   │   └── requirements.txt
│   └── services/               # Internal services
│       ├── storage/v1.0.0/     # Port 8064
│       ├── embeddings/v1.0.0/  # Port 8063
│       ├── metadata/v1.0.0/    # Port 8062
│       └── chunking/v1.0.0/    # Port 8061
│
└── Retrieval/                  # Retrieval Pipeline (Coming Soon)
    └── v1.0.0/                 # Main orchestrator (port 8070)
```

---

## Environment Configuration

The `.env` file contains all shared configuration:

```bash
# Set environment (development or production)
ENVIRONMENT=development

# Nebius AI Studio API Key
NEBIUS_API_KEY=your_key_here

# LLM Gateway (environment-aware)
LLM_GATEWAY_URL_DEVELOPMENT=http://localhost:8000/v1/chat/completions
LLM_GATEWAY_URL_PRODUCTION=http://localhost:8000/v1/chat/completions

# Milvus (environment-aware)
MILVUS_HOST_DEVELOPMENT=localhost  # Via SSH tunnel
MILVUS_PORT_DEVELOPMENT=19530
MILVUS_HOST_PRODUCTION=localhost   # Direct connection
MILVUS_PORT_PRODUCTION=19530

# Service ports
INGESTION_API_PORT=8060
CHUNKING_SERVICE_PORT=8061
METADATA_SERVICE_PORT=8062
EMBEDDINGS_SERVICE_PORT=8063
STORAGE_SERVICE_PORT=8064
```

---

## Usage Examples

### Ingest a Document

```bash
curl -X POST http://localhost:8060/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your document content here...",
    "document_id": "doc_001",
    "collection_name": "my_collection",
    "tenant_id": "default",
    "chunking_mode": "comprehensive",
    "metadata_mode": "basic"
  }'
```

### Create a Collection

```bash
curl -X POST http://localhost:8060/v1/collections \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "my_new_collection",
    "dimension": 4096,
    "description": "My collection"
  }'
```

### Update a Document

```bash
curl -X PUT http://localhost:8060/v1/documents/doc_001 \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Updated document content...",
    "collection_name": "my_collection",
    "tenant_id": "default"
  }'
```

### Delete a Document

```bash
curl -X DELETE "http://localhost:8060/v1/documents/doc_001?collection_name=my_collection"
```

---

## Interactive API Documentation

Once services are running:

- **Swagger UI**: http://localhost:8060/docs
- **ReDoc**: http://localhost:8060/redoc
- **Attu UI** (Milvus): http://localhost:3000

---

## Troubleshooting

### Services won't start

```bash
# Check if ports are already in use
lsof -i :8060
lsof -i :19530

# Kill processes on ports
./Tools/pipeline-manager stop
```

### SSH tunnel fails

```bash
# Check SSH key exists
ls -la ~/reku631_nebius

# Test SSH connection
ssh -i ~/reku631_nebius reku631@89.169.108.8

# Start tunnel manually
ssh -i ~/reku631_nebius -L 19530:localhost:19530 -L 3000:localhost:3000 -L 8000:localhost:8000 reku631@89.169.108.8
```

### Service health checks fail

```bash
# Check service status
./Tools/pipeline-manager status

# Check health
./Tools/pipeline-manager health

# Check tunnel is running
lsof -i :19530
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for more troubleshooting steps.

---

## Backup & Disaster Recovery

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete disaster recovery procedures.

Quick backup:
```bash
cd Tools/backup
./backup_all.sh
```

---

## Development Workflow

1. **Start services**:
   ```bash
   ./Tools/pipeline-manager start
   ```

2. **Verify everything is running**:
   ```bash
   ./Tools/pipeline-manager health
   ```

3. **Develop and test**:
   - View API docs: http://localhost:8060/docs
   - View Milvus data: http://localhost:3000
   - Test endpoints via Swagger UI

4. **Stop when done**:
   ```bash
   ./Tools/pipeline-manager stop
   ```

---

## Next Steps

- [ ] Complete Retrieval Pipeline implementation
- [ ] Add systemd service files for production
- [ ] Implement centralized logging
- [ ] Add monitoring/alerting
- [ ] Set up CI/CD pipeline

---

## Documentation Index

- **[README.md](README.md)** - This file (system overview & usage)
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide (SSH tunnel, Docker, disaster recovery)
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture & specifications
- **[Tools/backup/README.md](Tools/backup/README.md)** - Backup procedures

---

## Support

For issues or questions:
1. Check the documentation in the links above
2. Run `./Tools/pipeline-manager help` for available commands
3. Check logs in service terminal windows

---

**Version**: 1.0.0
**Last Updated**: October 9, 2025
**Server**: reku631@89.169.108.8
**Milvus Version**: 2.4.1
