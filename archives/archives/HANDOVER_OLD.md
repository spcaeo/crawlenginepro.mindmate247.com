# CrawlEnginePro - Complete Handover Document

## Project Overview

**Project Name**: CrawlEnginePro
**Purpose**: Multi-embedding RAG (Retrieval-Augmented Generation) pipeline with FastAPI microservices
**Current Location**: `~/Desktop/crawlenginepro.mindmate247.com/`
**Server**: 89.169.108.8 (Nebius Cloud)
**Server User**: reku631
**SSH Key**: `~/reku631_nebius`

## What Was Accomplished

### 1. Clean Reset
- Stopped all old services
- Removed all old installations:
  - ~/PipeLineServies
  - ~/venvs (multiple scattered venvs)
  - ~/services-env
- Started fresh with proper structure

### 2. Multi-Environment Setup
Created 3 separate environments:
- **Development** (dev): Ports 8070-8074
- **Staging** (staging): Ports 8080-8084
- **Production** (prod): Ports 8060-8064

Each environment has:
- Separate virtual environment
- Separate logs directory
- Separate configuration file
- Can run independently

### 3. Server Structure

```
Server: reku631@89.169.108.8
~/crawlenginepro/
├── code/                           # Source code
│   ├── shared/                     # Shared configs
│   │   ├── model_registry.py       # Multi-embedding model registry
│   │   ├── .env.dev                # Development config
│   │   ├── .env.staging            # Staging config
│   │   ├── .env.prod               # Production config
│   │   └── .env.example            # Template
│   ├── services/                   # All microservices
│   │   ├── storage/v1.0.0/         # Milvus operations
│   │   ├── embeddings/v1.0.0/      # Multi-provider embeddings
│   │   ├── metadata/v1.0.0/        # Metadata extraction
│   │   ├── chunking/v1.0.0/        # Text chunking
│   │   └── ingestion_api/          # Main API orchestrator
│   ├── deploy/                     # Management scripts
│   │   ├── deploy.sh               # Deploy from local to server
│   │   ├── server_setup.sh         # Initial server setup
│   │   └── manage.sh               # Multi-env service management
│   ├── requirements.txt            # All Python dependencies
│   └── README.md                   # Documentation
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

## Environment Configurations

### Development (.env.dev)
```bash
# Development Environment
ENVIRONMENT=development

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# LLM Gateway
LLM_GATEWAY_BASE_URL=http://localhost:8000/v1

# API Keys (UPDATE THESE!)
JINA_API_KEY=your_jina_api_key_here
SAMBANOVA_API_KEY=your_sambanova_api_key_here

# Service Ports (Development: 8070-8074)
STORAGE_SERVICE_PORT=8074
EMBEDDINGS_SERVICE_PORT=8073
METADATA_SERVICE_PORT=8072
CHUNKING_SERVICE_PORT=8071
INGESTION_API_PORT=8070

# Default Model
DEFAULT_EMBEDDING_MODEL=jina-embeddings-v3

# Logging
LOG_LEVEL=DEBUG
```

### Staging (.env.staging)
```bash
# Staging Environment
ENVIRONMENT=staging

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# LLM Gateway
LLM_GATEWAY_BASE_URL=http://localhost:8000/v1

# API Keys (UPDATE THESE!)
JINA_API_KEY=your_jina_api_key_here
SAMBANOVA_API_KEY=your_sambanova_api_key_here

# Service Ports (Staging: 8080-8084)
STORAGE_SERVICE_PORT=8084
EMBEDDINGS_SERVICE_PORT=8083
METADATA_SERVICE_PORT=8082
CHUNKING_SERVICE_PORT=8081
INGESTION_API_PORT=8080

# Default Model
DEFAULT_EMBEDDING_MODEL=jina-embeddings-v3

# Logging
LOG_LEVEL=INFO
```

### Production (.env.prod)
```bash
# Production Environment
ENVIRONMENT=production

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# LLM Gateway
LLM_GATEWAY_BASE_URL=http://localhost:8000/v1

# API Keys (UPDATE THESE!)
JINA_API_KEY=your_jina_api_key_here
SAMBANOVA_API_KEY=your_sambanova_api_key_here

# Service Ports (Production: 8060-8064)
STORAGE_SERVICE_PORT=8064
EMBEDDINGS_SERVICE_PORT=8063
METADATA_SERVICE_PORT=8062
CHUNKING_SERVICE_PORT=8061
INGESTION_API_PORT=8060

# Default Model
DEFAULT_EMBEDDING_MODEL=jina-embeddings-v3

# Logging
LOG_LEVEL=WARNING
```

## CRITICAL: First Time Setup

### Step 1: Update API Keys on Server

```bash
# SSH to server
ssh -i ~/reku631_nebius reku631@89.169.108.8

# Edit development config
nano ~/crawlenginepro/code/shared/.env.dev

# Update these lines:
JINA_API_KEY=<your_actual_jina_key>
SAMBANOVA_API_KEY=<your_actual_sambanova_key>

# Repeat for staging
nano ~/crawlenginepro/code/shared/.env.staging

# Repeat for production
nano ~/crawlenginepro/code/shared/.env.prod
```

### Step 2: Start an Environment

```bash
# On server
cd ~/crawlenginepro/code

# Start development
./deploy/manage.sh dev start

# Check status
./deploy/manage.sh dev status

# View logs
./deploy/manage.sh dev logs
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

# Restart the environment you're working with
cd ~/crawlenginepro/code
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
```

## Service Architecture

### Services and Ports

#### Development (8070-8074)
- **Ingestion API** (8070): Main entry point for document ingestion
- **Chunking** (8071): Text chunking service
- **Metadata** (8072): Metadata extraction
- **Embeddings** (8073): Multi-provider embedding generation
- **Storage** (8074): Milvus vector database operations

#### Staging (8080-8084)
- **Ingestion API** (8080)
- **Chunking** (8081)
- **Metadata** (8082)
- **Embeddings** (8083)
- **Storage** (8084)

#### Production (8060-8064)
- **Ingestion API** (8060)
- **Chunking** (8061)
- **Metadata** (8062)
- **Embeddings** (8063)
- **Storage** (8064)

### Service Flow
```
Ingestion API (entry point)
    ↓
    ├─→ Metadata Service → Extract metadata
    ├─→ Chunking Service → Chunk document
    ├─→ Embeddings Service → Generate embeddings (Jina/SambaNova/Nebius)
    └─→ Storage Service → Store in Milvus
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

### Collection Naming Convention
Collections are automatically named: `{filename}_{provider}_{dimensions}`

Examples:
- `JaiShreeRam_jina_1024`
- `JaiShreeRam_sambanova_4096`
- `document_nebius_e5_4096`

### API Usage Example

```bash
# Development environment
curl -X POST "http://localhost:8070/api/v1.0.0/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/document.md",
    "embedding_model": "jina-embeddings-v3",
    "chunking_strategy": "semantic",
    "max_chunk_size": 1000,
    "chunk_overlap": 100
  }'

# Staging environment
curl -X POST "http://localhost:8080/api/v1.0.0/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/document.md",
    "embedding_model": "E5-Mistral-7B-Instruct",
    "chunking_strategy": "semantic",
    "max_chunk_size": 1000,
    "chunk_overlap": 100
  }'

# Production environment
curl -X POST "http://localhost:8060/api/v1.0.0/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/document.md",
    "embedding_model": "jina-embeddings-v3",
    "chunking_strategy": "semantic",
    "max_chunk_size": 1000,
    "chunk_overlap": 100
  }'
```

## Accessing Web Interfaces

### With SSH Tunnel Active

1. **Milvus Attu UI**
   - URL: http://localhost:3000
   - Milvus Host: localhost:19530

2. **API Documentation**
   - Dev: http://localhost:8070/docs
   - Staging: http://localhost:8080/docs
   - Prod: http://localhost:8060/docs

3. **LLM Gateway**
   - URL: http://localhost:8000

## Troubleshooting

### Services Won't Start

```bash
# Check logs
ssh -i ~/reku631_nebius reku631@89.169.108.8
cd ~/crawlenginepro/code
./deploy/manage.sh dev logs storage

# Check if API keys are set
cat ~/crawlenginepro/code/shared/.env.dev | grep API_KEY

# Check if ports are in use
lsof -i :8070-8074
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

# For development
source ~/crawlenginepro/development/venv/bin/activate
pip install -r ~/crawlenginepro/code/requirements.txt
deactivate
```

### SSH Tunnel Lost Connection

```bash
# Restart tunnel
ssh -i ~/reku631_nebius -L 19530:localhost:19530 -L 3000:localhost:3000 -L 8000:localhost:8000 reku631@89.169.108.8
```

## Key Improvements from Old System

### Before (Problems)
- Multiple scattered venvs (milvus_storage, embeddings_v3, metadata_v3, chunking_v5)
- Confusion between local vs server deployment
- Pipeline-manager opening many terminal windows
- No clear dev/staging/prod separation
- Conflicting port configurations
- Multiple README files creating confusion
- Services sometimes running locally, sometimes on server

### After (Solutions)
- **3 unified venvs**: One per environment (dev/staging/prod)
- **Clear deployment**: All services run on server, managed remotely
- **No terminal spam**: Services run in background with nohup
- **Proper environments**: Separate configs, ports, and logs for each stage
- **Consistent ports**: Well-defined port ranges per environment
- **Single documentation**: One README.md + this handover doc
- **All services on server**: Accessed via SSH tunnel

## Files and Locations

### Local Machine
```
~/Desktop/crawlenginepro.mindmate247.com/
├── code/                    # Main codebase
├── local_dev/               # For local testing (optional)
├── HANDOVER.md              # This document
└── GETTING_STARTED.md       # Quick start guide
```

### Server
```
~/crawlenginepro/
├── code/                    # Deployed code
├── development/             # Dev environment
├── staging/                 # Staging environment
└── production/              # Prod environment
```

### SSH Key Location
```
~/reku631_nebius             # Private key for server access
```

## API Keys Required

You need to obtain and configure these API keys:

1. **Jina AI API Key**
   - Get from: https://jina.ai
   - Used for: jina-embeddings-v3 (1024 dims)
   - Update in all 3 .env files

2. **SambaNova API Key**
   - Get from: https://sambanova.ai
   - Used for: E5-Mistral-7B-Instruct (4096 dims)
   - Update in all 3 .env files

## Important Commands Reference

### Local Machine
```bash
# Deploy code to server
cd ~/Desktop/crawlenginepro.mindmate247.com/code
./deploy/deploy.sh

# SSH with tunnel
ssh -i ~/reku631_nebius -L 19530:localhost:19530 -L 3000:localhost:3000 -L 8000:localhost:8000 reku631@89.169.108.8

# SSH without tunnel
ssh -i ~/reku631_nebius reku631@89.169.108.8
```

### On Server
```bash
# Navigate to code directory
cd ~/crawlenginepro/code

# Start environments
./deploy/manage.sh dev start
./deploy/manage.sh staging start
./deploy/manage.sh prod start

# Stop environments
./deploy/manage.sh dev stop
./deploy/manage.sh staging stop
./deploy/manage.sh prod stop

# Check status
./deploy/manage.sh dev status
./deploy/manage.sh staging status
./deploy/manage.sh prod status

# View logs
./deploy/manage.sh dev logs
./deploy/manage.sh dev logs storage      # Specific service
```

## Next Steps for New Session

1. **Open Terminal in New Project Directory**
   ```bash
   cd ~/Desktop/crawlenginepro.mindmate247.com/code
   ```

2. **Read This Handover Document**
   - You'll have full context of the setup
   - All SSH commands and credentials
   - Complete environment configurations

3. **Update API Keys** (if not done yet)
   ```bash
   ssh -i ~/reku631_nebius reku631@89.169.108.8
   nano ~/crawlenginepro/code/shared/.env.dev
   # Update JINA_API_KEY and SAMBANOVA_API_KEY
   ```

4. **Start Services**
   ```bash
   cd ~/crawlenginepro/code
   ./deploy/manage.sh dev start
   ```

5. **Test Ingestion**
   - With SSH tunnel active
   - Use the API examples above

## Critical Information Summary

- **Project Path**: `~/Desktop/crawlenginepro.mindmate247.com/`
- **Server**: `reku631@89.169.108.8`
- **SSH Key**: `~/reku631_nebius`
- **SSH Tunnel**: `ssh -i ~/reku631_nebius -L 19530:localhost:19530 -L 3000:localhost:3000 -L 8000:localhost:8000 reku631@89.169.108.8`
- **Port Ranges**: Dev (8070-8074), Staging (8080-8084), Prod (8060-8064)
- **Config Files**: `.env.dev`, `.env.staging`, `.env.prod` in `code/shared/`
- **Management Script**: `./deploy/manage.sh {env} {command}`

## Deployment Checklist

- [x] Stopped all old services
- [x] Cleaned old installations
- [x] Created new project structure
- [x] Set up 3 environments (dev/staging/prod)
- [x] Deployed code to server
- [x] Created 3 separate venvs
- [x] Installed dependencies in all venvs
- [ ] **TODO: Update API keys in all .env files**
- [ ] **TODO: Start and test dev environment**
- [ ] **TODO: Test multi-embedding with JaiShreeRam.md**

---

**Status**: Ready for handover. System is deployed and configured. Only API keys need to be added to start services.

**Last Updated**: October 17, 2025
**Created By**: Claude Code Reset & Multi-Environment Setup

---

## Current Status & Known Issues

### What's Complete
- ✅ Server cleaned of all old installations
- ✅ New 3-environment structure created (dev/staging/prod)
- ✅ All code deployed to server
- ✅ 3 virtual environments set up with dependencies
- ✅ API keys added to all .env files (Jina, SambaNova, Nebius)
- ✅ Management scripts created

### Current Issue: Python Import Path

**Problem**: Services can't find `model_registry.py` because it's in `shared/` folder.

**Error**: `ModuleNotFoundError: No module named 'model_registry'`

**What Was Tried**:
1. Created symlink: `~/crawlenginepro/code/model_registry.py` → `shared/model_registry.py`
2. Attempted to add PYTHONPATH to manage.sh (syntax error occurred)

**Solution Needed**: 
The `start_service()` function in `/home/reku631/crawlenginepro/code/deploy/manage.sh` needs to be updated to properly set PYTHONPATH. Line 75 should be:

```bash
cd "$CODE_DIR" && PYTHONPATH="$CODE_DIR:$PYTHONPATH" PORT=$port nohup "$VENV" "$script" > "$log_file" 2>&1 &
```

**To Fix This Issue**:
```bash
ssh -i ~/reku631_nebius reku631@89.169.108.8

# Fix the manage.sh file
nano ~/crawlenginepro/code/deploy/manage.sh

# Find line 75 (in start_service function) and make it:
cd "$CODE_DIR" && PYTHONPATH="$CODE_DIR:$PYTHONPATH" PORT=$port nohup "$VENV" "$script" > "$log_file" 2>&1 &

# Save and exit (Ctrl+O, Enter, Ctrl+X)

# Try starting services
cd ~/crawlenginepro/code
./deploy/manage.sh dev start
```

### Alternative Fix (If Above Doesn't Work)

Copy model_registry.py directly into each service directory:
```bash
ssh -i ~/reku631_nebius reku631@89.169.108.8

cd ~/crawlenginepro/code

# Copy to each service that needs it
cp shared/model_registry.py services/storage/v1.0.0/
cp shared/model_registry.py services/embeddings/v1.0.0/
cp shared/model_registry.py services/metadata/v1.0.0/
cp shared/model_registry.py services/chunking/v1.0.0/
cp shared/model_registry.py services/ingestion_api/

# Restart services
./deploy/manage.sh dev restart
```

### Files Updated with API Keys

All three environment files have been configured:
- `/home/reku631/crawlenginepro/code/shared/.env.dev`
- `/home/reku631/crawlenginepro/code/shared/.env.staging`
- `/home/reku631/crawlenginepro/code/shared/.env.prod`

API Keys included:
- **NEBIUS_API_KEY**: eyJhbGciOiJIUzI1NiIsImtpZCI6IlV6SXJWd1h0dnprLVRvdzlLZWstc0M1akptWXBvX1VaVkxUZlpnMDRlOFUiLCJ0eXAiOiJKV1QifQ... (full key in files)
- **JINA_API_KEY**: jina_a2e5ee1eea2d444d93e4cc954cecedd9jBBf9EAC3x0Avhynva0mbltZd-Hz
- **SAMBANOVA_API_KEY**: 9a2acb34-97f8-4f3c-a37c-d11aa5b699dd

### Next Steps for Continuing

1. **Fix the Python import issue** (see solutions above)
2. **Start development environment**:
   ```bash
   cd ~/crawlenginepro/code
   ./deploy/manage.sh dev start
   ./deploy/manage.sh dev status
   ```
3. **Test with simple API call** (once services running)
4. **Test multi-embedding with JaiShreeRam.md**

### Project Location Summary

**Local**: `~/Desktop/crawlenginepro.mindmate247.com/`
**Server**: `~/crawlenginepro/` (on reku631@89.169.108.8)
**This Document**: `~/Desktop/crawlenginepro.mindmate247.com/HANDOVER.md`

---

**Last Updated**: October 17, 2025 - Services deployed, API keys added, Python import path issue needs resolution
