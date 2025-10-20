# CrawlEnginePro - Complete Handover Document

## Project Overview

**Project Name**: CrawlEnginePro
**Purpose**: Multi-embedding RAG (Retrieval-Augmented Generation) pipeline with FastAPI microservices
**Current Location**: `~/Desktop/crawlenginepro.mindmate247.com/`
**Server**: 89.169.108.8 (Nebius Cloud)
**Server User**: reku631
**SSH Key**: `~/reku631_nebius`

## What Was Accomplished

### 1. Complete Code Reorganization ✅

Migrated to clean PipeLineServices architecture:
- **Ingestion/** - All document ingestion services
- **Retrieval/** - All RAG retrieval services
- **shared/** - Common utilities (model_registry.py, health_utils.py)
- **Tools/** - Management utilities
- **TestingDocuments/** - Test files (JaiShreeRam.md, ITVAMS.md, Bible, etc.)
- **deploy/** - Deployment and management scripts

### 2. Multi-Environment Setup ✅

Created 3 separate environments with proper port isolation:

**Development Environment**
- Ingestion API: 8070 (Services: 8071-8075)
- Retrieval API: 8090 (Services: 8091-8095)
- Config: `code/shared/.env.dev`
- Logs: `~/crawlenginepro/development/logs`
- Venv: `~/crawlenginepro/development/venv`

**Staging Environment**
- Ingestion API: 8080 (Services: 8081-8085)
- Retrieval API: 8100 (Services: 8101-8105)
- Config: `code/shared/.env.staging`
- Logs: `~/crawlenginepro/staging/logs`
- Venv: `~/crawlenginepro/staging/venv`

**Production Environment**
- Ingestion API: 8060 (Services: 8061-8065)
- Retrieval API: 8110 (Services: 8111-8115)
- Config: `code/shared/.env.prod`
- Logs: `~/crawlenginepro/production/logs`
- Venv: `~/crawlenginepro/production/venv`

### 3. Server Structure

```
Server: reku631@89.169.108.8
~/crawlenginepro/
├── code/                           # Source code (deployed from local)
│   ├── Ingestion/                  # Ingestion pipeline
│   │   ├── v1.0.0/                 # Main ingestion API
│   │   │   └── main_ingestion_api.py
│   │   └── services/               # Internal microservices
│   │       ├── storage/v1.0.0/     # storage_api.py
│   │       ├── embeddings/v1.0.0/  # embeddings_api.py
│   │       ├── metadata/v1.0.0/    # metadata_api.py
│   │       ├── chunking/v1.0.0/    # chunking_orchestrator.py
│   │       └── llm_gateway/v1.0.0/ # llm_gateway.py
│   │
│   ├── Retrieval/                  # Retrieval pipeline
│   │   ├── v1.0.0/                 # Main retrieval API
│   │   │   └── main_retrieval_api.py
│   │   └── services/               # Internal microservices
│   │       ├── search/v1.0.0/      # search_api.py
│   │       ├── reranking/v1.0.0/   # reranking_api.py
│   │       ├── compression/v1.0.0/ # compression_api.py
│   │       ├── answer_generation/v1.0.0/ # answer_api.py
│   │       ├── intent/v1.0.0/      # intent_api.py
│   │       └── llm_gateway@        # Symlink to Ingestion LLM Gateway
│   │
│   ├── shared/                     # Shared configs & utilities
│   │   ├── model_registry.py       # Multi-embedding model registry
│   │   ├── health_utils.py         # Health check utilities
│   │   ├── .env → .env.dev         # Active environment symlink
│   │   ├── .env.dev                # Development config
│   │   ├── .env.staging            # Staging config
│   │   └── .env.prod               # Production config
│   │
│   ├── deploy/                     # Deployment scripts
│   │   ├── deploy.sh               # Deploy from local to server
│   │   ├── server_setup.sh         # Server environment setup
│   │   └── manage.sh               # Multi-environment service management
│   │
│   ├── Tools/                      # Management utilities
│   │   ├── pipeline-manager        # Legacy local manager
│   │   ├── remote-pipeline         # Remote pipeline control
│   │   └── backup/                 # Backup scripts
│   │
│   ├── TestingDocuments/           # Test files
│   │   ├── JaiShreeRam.md
│   │   ├── ITVAMS.md
│   │   └── bible/                  # 66 books
│   │
│   ├── .env → shared/.env          # Root env symlink
│   └── README.md                   # Main documentation
│
├── development/                    # Dev environment
│   ├── venv/                       # Python virtual environment
│   └── logs/                       # Service logs
│
├── staging/                        # Staging environment
│   ├── venv/
│   └── logs/
│
└── production/                     # Production environment
    ├── venv/
    └── logs/
```

## SSH Access

### SSH Tunnel Command (CRITICAL - DO NOT DELETE)
```bash
ssh -i ~/reku631_nebius -L 19530:localhost:19530 -L 3000:localhost:3000 -L 8000:localhost:8000 reku631@89.169.108.8
```

This tunnel forwards:
- **Port 19530**: Milvus vector database
- **Port 3000**: Attu UI (Milvus web interface)
- **Port 8000**: LLM Gateway (Nebius AI Studio)

### Basic SSH
```bash
ssh -i ~/reku631_nebius reku631@89.169.108.8
```

## Complete Setup Workflow

### Step 1: Deploy Code to Server (from local machine)

```bash
cd ~/Desktop/crawlenginepro.mindmate247.com/code
./deploy/deploy.sh
```

This will:
- Test SSH connection
- Create remote directory structure
- Sync all code to server
- Set executable permissions

### Step 2: SSH to Server

```bash
ssh -i ~/reku631_nebius reku631@89.169.108.8
cd ~/crawlenginepro/code
```

### Step 3: Run Server Setup (First Time Only)

```bash
# For development environment
./deploy/server_setup.sh dev

# For staging environment
./deploy/server_setup.sh staging

# For production environment
./deploy/server_setup.sh prod
```

This will:
- Create environment directory structure
- Create Python virtual environment
- Install all dependencies
- Setup Python path for shared modules
- Create environment file symlinks

### Step 4: Verify API Keys

```bash
# Edit the environment file
nano ~/crawlenginepro/code/shared/.env.dev

# Ensure these are set:
# NEBIUS_API_KEY=eyJhbGci...
# JINA_API_KEY=jina_a2e5e...
# SAMBANOVA_API_KEY=9a2acb...
```

### Step 5: Start Services

```bash
cd ~/crawlenginepro/code

# Start all services in development
./deploy/manage.sh dev start

# Or start only ingestion pipeline
./deploy/manage.sh dev start ingestion

# Or start only retrieval pipeline
./deploy/manage.sh dev start retrieval
```

### Step 6: Check Status

```bash
./deploy/manage.sh dev status
```

Expected output:
```
=== Service Status: development environment ===

Ingestion Pipeline:
  ● storage: running (PID: 12345, Port: 8074)
  ● embeddings: running (PID: 12346, Port: 8073)
  ● metadata: running (PID: 12347, Port: 8072)
  ● chunking: running (PID: 12348, Port: 8071)
  ● llm_gateway: running (PID: 12349, Port: 8075)
  ● ingestion: running (PID: 12350, Port: 8070)

Retrieval Pipeline:
  ● search: running (PID: 12351, Port: 8091)
  ● reranking: running (PID: 12352, Port: 8092)
  ● compression: running (PID: 12353, Port: 8093)
  ● answer_generation: running (PID: 12354, Port: 8094)
  ● intent: running (PID: 12355, Port: 8095)
  ● retrieval: running (PID: 12356, Port: 8090)

Summary:
  Ingestion: 6/6 running
  Retrieval: 6/6 running
```

## Daily Workflow

### Deploying Code Changes (from local machine)

```bash
# From your local machine
cd ~/Desktop/crawlenginepro.mindmate247.com/code

# Deploy to server
./deploy/deploy.sh

# SSH to server
ssh -i ~/reku631_nebius reku631@89.169.108.8
cd ~/crawlenginepro/code

# Restart the environment you're working with
./deploy/manage.sh dev restart       # or staging, or prod
```

### Managing Services on Server

```bash
# Start an environment
./deploy/manage.sh dev start         # Development
./deploy/manage.sh staging start     # Staging
./deploy/manage.sh prod start        # Production

# Stop an environment
./deploy/manage.sh dev stop

# Restart an environment
./deploy/manage.sh dev restart

# Check status
./deploy/manage.sh dev status

# View logs (all services)
./deploy/manage.sh dev logs

# Follow specific service log
./deploy/manage.sh dev logs storage
./deploy/manage.sh dev logs embeddings
./deploy/manage.sh dev logs ingestion
```

## Service Architecture

### Port Allocation

#### Development (8070-8099)
**Ingestion Services:**
- Ingestion API: 8070 (Main entry point)
- Chunking: 8071
- Metadata: 8072
- Embeddings: 8073
- Storage: 8074
- LLM Gateway: 8075

**Retrieval Services:**
- Retrieval API: 8090 (Main entry point)
- Search: 8091
- Reranking: 8092
- Compression: 8093
- Answer Generation: 8094
- Intent: 8095

#### Staging (8080-8109)
**Ingestion:** 8080-8085
**Retrieval:** 8100-8105

#### Production (8060-8069, 8110-8119)
**Ingestion:** 8060-8065
**Retrieval:** 8110-8115

### Service Flow

```
Ingestion Pipeline:
Document → Metadata → Chunking → Embeddings → Storage → Milvus

Retrieval Pipeline:
Query → Intent Detection (parallel with Search)
      → Search → Reranking → Compression → Answer Generation → Response
```

## Multi-Embedding Support

### Supported Providers

1. **Jina AI** (jina-embeddings-v3)
   - Dimensions: 1024
   - Context: 8K tokens
   - Free tier available

2. **SambaNova** (E5-Mistral-7B-Instruct)
   - Dimensions: 4096
   - Context: 4K tokens
   - Pricing: $0.13 per million tokens

3. **Nebius** (E5-Mistral-7B-Instruct)
   - Dimensions: 4096
   - Context: 4K tokens
   - Via LLM Gateway on port 8000

### API Usage Examples

#### Development Environment (Port 8070)
```bash
curl -X POST "http://localhost:8070/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/document.md",
    "embedding_model": "jina-embeddings-v3",
    "chunking_strategy": "semantic",
    "max_chunk_size": 1000,
    "chunk_overlap": 100
  }'
```

#### Staging Environment (Port 8080)
```bash
curl -X POST "http://localhost:8080/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/document.md",
    "embedding_model": "E5-Mistral-7B-Instruct",
    "chunking_strategy": "semantic"
  }'
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs
ssh -i ~/reku631_nebius reku631@89.169.108.8
cd ~/crawlenginepro/code
./deploy/manage.sh dev logs storage

# Check if virtual environment exists
ls -la ~/crawlenginepro/development/venv

# Re-run setup if needed
./deploy/server_setup.sh dev
```

### Port Conflicts

```bash
# Find what's using the port
lsof -i :8070

# Kill process
kill -9 <PID>

# Restart environment
./deploy/manage.sh dev restart
```

### Dependencies Missing

```bash
# Reinstall dependencies for an environment
ssh -i ~/reku631_nebius reku631@89.169.108.8

# Re-run setup
cd ~/crawlenginepro/code
./deploy/server_setup.sh dev
```

## Key Improvements from Old System

### Before (Problems)
- Scattered services across multiple directories
- Inconsistent port configurations
- No clear environment separation
- Manual service management
- Import path issues

### After (Solutions)
- **Clean architecture**: Ingestion/, Retrieval/, shared/
- **3 separate environments**: dev, staging, prod with isolated ports
- **Automated management**: Single script for all operations
- **Proper Python paths**: sitecustomize.py handles imports
- **Symlinked .env files**: Easy environment switching

## Management Script Reference

```bash
# Format: ./deploy/manage.sh <environment> <command> [options]

# Start services
./deploy/manage.sh dev start              # All services
./deploy/manage.sh dev start ingestion    # Only ingestion
./deploy/manage.sh dev start retrieval    # Only retrieval

# Stop services
./deploy/manage.sh dev stop               # All services
./deploy/manage.sh dev stop ingestion     # Only ingestion

# Restart services
./deploy/manage.sh dev restart

# Check status
./deploy/manage.sh dev status

# View logs
./deploy/manage.sh dev logs               # All logs
./deploy/manage.sh dev logs storage       # Specific service (follow mode)
```

## API Keys Required

All three environment files need these API keys:

1. **Nebius API Key**
   - Already configured in .env files
   - eyJhbGci...

2. **Jina AI API Key**
   - Already configured
   - jina_a2e5ee...

3. **SambaNova API Key**
   - Already configured
   - 9a2acb34...

## Next Steps for New Session

1. **Navigate to Project**
   ```bash
   cd ~/Desktop/crawlenginepro.mindmate247.com/code
   ```

2. **Deploy to Server** (if code changed)
   ```bash
   ./deploy/deploy.sh
   ```

3. **SSH to Server**
   ```bash
   ssh -i ~/reku631_nebius reku631@89.169.108.8
   cd ~/crawlenginepro/code
   ```

4. **Start Services**
   ```bash
   ./deploy/manage.sh dev start
   ./deploy/manage.sh dev status
   ```

5. **Test Ingestion** (with SSH tunnel active)
   ```bash
   curl -X POST http://localhost:8070/v1/ingest -H "Content-Type: application/json" -d '{...}'
   ```

## Critical Information Summary

- **Local Path**: `~/Desktop/crawlenginepro.mindmate247.com/code`
- **Server**: `reku631@89.169.108.8`
- **SSH Key**: `~/reku631_nebius`
- **Server Code**: `~/crawlenginepro/code`
- **SSH Tunnel**: `ssh -i ~/reku631_nebius -L 19530:localhost:19530 -L 3000:localhost:3000 -L 8000:localhost:8000 reku631@89.169.108.8`
- **Deployment**: `./deploy/deploy.sh`
- **Server Setup**: `./deploy/server_setup.sh <env>`
- **Management**: `./deploy/manage.sh <env> <command>`

---

**Status**: Complete code reorganization. Ready for deployment and testing.

**Last Updated**: October 17, 2025
**Architecture**: PipeLineServices with Ingestion + Retrieval pipelines
**Environments**: 3 (development, staging, production)

---
