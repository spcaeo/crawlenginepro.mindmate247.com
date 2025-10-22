# PipeLineServices - Port Allocation

## Overview
All PipeLineServices use a structured port allocation scheme with three isolated environments: **Development**, **Staging**, and **Production**. Each environment uses a different port range to avoid conflicts.

**IMPORTANT:** All services are environment-aware and automatically select ports based on the `ENVIRONMENT` environment variable (`production`, `staging`, or `development`).

## Multi-Environment Port Allocation

### Production Environment (8060-8069, 8110-8119)
**Primary/default environment running on the server**

**Ingestion Pipeline (8060-8069):**
- **8060**: Ingestion API (Main orchestrator - Public)
- **8061**: Chunking Service v1.0.0 (Internal)
- **8062**: Metadata Service v1.0.0 (Internal)
- **8063**: Embeddings Service v1.0.0 (Internal)
- **8064**: Storage Service v1.0.0 (Internal)
- **8065**: LLM Gateway Service v1.0.0 (Internal) ← Shared by Metadata, Compression, Answer
- **8066-8069**: Reserved for future Ingestion services

**Retrieval Pipeline (8110-8119):**
- **8110**: Retrieval API (Main orchestrator - Public)
- **8111**: Search Service v1.0.0 (Internal)
- **8112**: Reranking Service v1.0.0 (Internal)
- **8113**: Compression Service v1.0.0 (Internal)
- **8114**: Answer Generation Service v1.0.0 (Internal)
- **8115**: Intent & Prompt Adaptation Service v1.0.0 (Internal)
- **8116-8119**: Reserved for future Retrieval services

### Staging Environment (8080-8089, 8100-8109)
**Pre-production testing environment on the server**

**Ingestion Pipeline (8080-8089):**
- **8080**: Ingestion API
- **8081**: Chunking Service
- **8082**: Metadata Service
- **8083**: Embeddings Service
- **8084**: Storage Service
- **8085**: LLM Gateway Service
- **8086-8089**: Reserved

**Retrieval Pipeline (8100-8109):**
- **8100**: Retrieval API
- **8101**: Search Service
- **8102**: Reranking Service
- **8103**: Compression Service
- **8104**: Answer Generation Service
- **8105**: Intent & Prompt Adaptation Service
- **8106-8109**: Reserved

### Development Environment (8070-8079, 8090-8099)
**Local development on developer machines via SSH tunnel**

**Ingestion Pipeline (8070-8079):**
- **8070**: Ingestion API
- **8071**: Chunking Service
- **8072**: Metadata Service
- **8073**: Embeddings Service
- **8074**: Storage Service
- **8075**: LLM Gateway Service
- **8076-8079**: Reserved

**Retrieval Pipeline (8090-8099):**
- **8090**: Retrieval API
- **8091**: Search Service
- **8092**: Reranking Service
- **8093**: Compression Service
- **8094**: Answer Generation Service
- **8095**: Intent & Prompt Adaptation Service
- **8096-8099**: Reserved

### External Dependencies (All Environments)
- **19530**: Milvus Vector Database (via SSH tunnel in development)
- **3000**: Attu UI (Milvus admin interface, via SSH tunnel in development)

## Service Dependencies

```
Ingestion API
  ├─→ Chunking Service
  ├─→ Metadata Service
  │    └─→ LLM Gateway ← Nebius AI Studio proxy
  ├─→ Embeddings Service
  └─→ Storage Service
       └─→ Milvus (19530)

Retrieval API
  ├─→ Search Service
  │    ├─→ Embeddings Service ← Shared from Ingestion
  │    └─→ Storage Service ← Shared from Ingestion
  ├─→ Reranking Service ← BGE or Jina AI
  ├─→ Compression Service
  │    └─→ LLM Gateway ← Shared from Ingestion
  ├─→ Answer Generation Service
  │    └─→ LLM Gateway ← Shared from Ingestion
  └─→ Intent & Prompt Adaptation Service
       └─→ LLM Gateway ← Shared from Ingestion
```

## Configuration Files

Each environment has its own configuration file in `shared/`:

- **shared/.env.prod** - Production configuration (ports 8060-8069, 8110-8119)
- **shared/.env.staging** - Staging configuration (ports 8080-8089, 8100-8109)
- **shared/.env.dev** - Development configuration (ports 8070-8079, 8090-8099)

All services read PORT from environment variables using `os.getenv("PORT", "default")` pattern.

The symlink `/code/.env` → `/code/shared/.env.dev` ensures services load the correct environment config.

## Service Startup Order

For optimal startup, services should be started in dependency order:

1. **Milvus** (external) - Port 19530
2. **LLM Gateway** - First internal service
3. **Storage Service** - Depends on Milvus
4. **Embeddings Service** - Independent
5. **Metadata Service** - Depends on LLM Gateway
6. **Chunking Service** - Independent
7. **Ingestion API** - Depends on all above

## Quick Start

### Development (Local Machine)

```bash
# 1. Start SSH tunnel to server (Terminal 1)
ssh -i ~/reku631_nebius -L 19530:localhost:19530 -L 3000:localhost:3000 reku631@89.169.103.3

# 2. Start services using startup script (Terminal 2)
cd /path/to/crawlenginepro.mindmate247.com/local_dev
./start_all_services.sh

# 3. Verify all services are healthy
curl http://localhost:8070/health
```

### Staging (Server)

```bash
# On server
cd /var/www/CrawlEnginePro/code
./deploy/manage.sh staging start

# Check status
./deploy/manage.sh staging status
```

### Production (Server)

```bash
# On server
cd /var/www/CrawlEnginePro/code
./deploy/manage.sh production start

# Check status
./deploy/manage.sh production status
```

## Health Check Endpoints

All services expose a `/health` endpoint:

### Production
**Ingestion Pipeline:**
- http://localhost:8060/health (Ingestion API - aggregated health)
- http://localhost:8061/health (Chunking)
- http://localhost:8062/health (Metadata)
- http://localhost:8063/health (Embeddings)
- http://localhost:8064/health (Storage)
- http://localhost:8065/health (LLM Gateway)

**Retrieval Pipeline:**
- http://localhost:8110/health (Retrieval API - aggregated health)
- http://localhost:8111/health (Search)
- http://localhost:8112/health (Reranking)
- http://localhost:8113/health (Compression)
- http://localhost:8114/health (Answer Generation)
- http://localhost:8115/health (Intent & Prompt Adaptation)

### Development
**Ingestion Pipeline:**
- http://localhost:8070/health (Ingestion API)
- http://localhost:8071/health (Chunking)
- http://localhost:8072/health (Metadata)
- http://localhost:8073/health (Embeddings)
- http://localhost:8074/health (Storage)
- http://localhost:8075/health (LLM Gateway)

**Retrieval Pipeline:**
- http://localhost:8090/health (Retrieval API)
- http://localhost:8091/health (Search)
- http://localhost:8092/health (Reranking)
- http://localhost:8093/health (Compression)
- http://localhost:8094/health (Answer Generation)
- http://localhost:8095/health (Intent & Prompt Adaptation)

## Architecture Notes

### Environment Isolation

Each environment is completely isolated with its own:
- Port range (no conflicts)
- Python virtual environment (on server)
- Configuration file (shared/.env.{env})
- Log files (per environment)
- PID files for process management

### Development Workflow

1. **Local Development**: Work on features locally using development ports (8070-8095)
2. **Staging Deployment**: Test on server staging environment (8080-8109)
3. **Production Deployment**: Deploy to production (8060-8069, 8110-8119)

### SSH Tunnel for Development

Development requires SSH tunnel to access server infrastructure:

```bash
ssh -i ~/reku631_nebius \
  -L 19530:localhost:19530 \  # Milvus
  -L 3000:localhost:3000 \    # Attu UI
  reku631@89.169.103.3
```

This provides local access to:
- Milvus vector database (localhost:19530)
- Attu UI for collection management (localhost:3000)

### Shared Services

Some services are shared across pipelines:
- **LLM Gateway**: Used by Metadata, Compression, Answer Generation, Intent services
- **Embeddings Service**: Used by Ingestion API and Search Service
- **Storage Service**: Used by Ingestion API and Search Service

## Jina AI Reranker (Optional)

The Reranking Service supports two backends:

**BGE Reranker (Default)**:
- Model: `BAAI/bge-reranker-v2-m3`
- Runs locally on CPU/GPU
- No external API required
- Performance: ~2,700ms for 20 chunks

**Jina AI Reranker (Optional)**:
- Model: `jina-reranker-v2-base-multilingual`
- Cloud API: `https://api.jina.ai/v1/rerank`
- Requires `JINA_AI_KEY` in `.env`
- Performance: ~780ms for 20 chunks (3.5x faster!)

To enable Jina AI, add to environment config:
```bash
RERANKER_BACKEND=jina
JINA_AI_KEY=your_jina_api_key_here
```

To use BGE (default):
```bash
RERANKER_BACKEND=bge
# or simply omit RERANKER_BACKEND
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i:8070

# Kill process
kill -9 <PID>
```

### Service Won't Start
1. Check logs in `local_dev/*.log`
2. Verify environment variables are loaded
3. Ensure dependencies (Milvus) are accessible
4. Check PORT environment variable is set correctly

### Health Check Fails
- Ensure all dependent services are running
- Check service logs for errors
- Verify network connectivity
- Test individual service health endpoints

---

## Production Server Configuration (89.169.103.3)

### Server Details
- **VM Name:** lavender-chameleon-instance-2
- **Instance ID:** computeinstance-e00akjpdm3mceg5ps0
- **Public IP:** 89.169.103.3
- **Private IP:** 10.0.0.65
- **Platform:** cpu-e2 (16 vCPUs, 64 GiB), 1280 GiB SSD
- **OS:** Ubuntu 24.04 LTS
- **Region:** eu-north1

### DNS Records (Hostinger)
- `milvus.mindmate247.com` → 89.169.103.3
- `crawlenginepro.mindmate247.com` → 89.169.103.3
- `mindmate247.com` (@) → 89.169.103.3

### SSH Access
- **Username:** reku631
- **SSH Key:** ~/reku631_nebius
- **Ports:** 22 (standard), 443 (firewall bypass)

```bash
# Standard SSH
ssh -i ~/reku631_nebius reku631@89.169.103.3

# Alternative (works on restrictive networks)
ssh -i ~/reku631_nebius -p 443 reku631@89.169.103.3
```

### Service Management

**Start all production services:**
```bash
cd ~/crawlenginepro/code
./start_production.sh
```

**Check service health:**
```bash
# Individual service
curl http://localhost:8110/health | jq

# All services
for port in 8060 8061 8062 8063 8064 8065 8110 8111 8112 8113 8114 8115; do
  echo "Port $port: $(curl -s http://localhost:$port/health | jq -r '.status')"
done
```

**View logs:**
```bash
cd ~/crawlenginepro/code/logs
tail -f retrieval_api.log
```

### Environment Variables

Production services automatically detect `ENVIRONMENT=production` and use correct ports (8060-8069, 8110-8119).

**Critical environment variables in shared/.env.prod:**
- `ENVIRONMENT=production`
- `LLM_GATEWAY_URL_PRODUCTION=http://localhost:8065`
- `LLM_GATEWAY_URL_DEVELOPMENT=http://localhost:8000`
- `MILVUS_HOST_PRODUCTION=localhost`
- `MILVUS_PORT_PRODUCTION=19530`

### Service Status (as of Oct 22, 2025)

**Current Environment:** Development (Local Mac) + Production Milvus (Server)

✅ **Local Development Services (6/6 Healthy):**
- Ingestion API (8070)
- Chunking (8071)
- Metadata (8072)
- Embeddings (8073)
- Storage (8074)
- LLM Gateway (8075)

✅ **Production Server - Milvus Only:**
- Milvus Database (19530) - v2.6.4
- Attu UI (3000) - v2.5.7
- etcd (2379) - v3.5.5
- Minio (9000/9001)

⏳ **Production Services (Not Yet Deployed):**
- Retrieval services will be deployed in future phase
- Ingestion services may be deployed for production use

**Status:** Development environment fully operational with production Milvus backend. Ready for testing and development.

### Key Fixes Applied

1. **Storage Service Port:** Fixed to correctly use port 8064 (was starting on 8014)
2. **Environment-Aware Configs:** All services now check `ENVIRONMENT` variable for port selection
3. **LLM Gateway URLs:** Fixed to use base URLs without paths (services append endpoints)
4. **Dependency URLs:** Main APIs now use correct production ports for internal services

### Milvus Database

**Status:** Running in Docker (Upgraded Oct 22, 2025)
```bash
cd ~/crawlenginepro/milvus
sudo docker-compose ps
```

**Services:**
- `milvus-standalone` - Port 19530 (v2.6.4 - Latest)
- `milvus-attu` - Port 3000 (v2.5.7 - Latest open-source, Admin UI via SSH tunnel)
- `milvus-etcd` - Metadata store (v3.5.5)
- `milvus-minio` - Object storage (ports 9000, 9001)

**Recent Upgrade (Oct 22, 2025):**
- Milvus: v2.3.3 → v2.6.4
- Attu: v2.3.10 → v2.5.7
- Fresh installation (all old data cleared)
- All 7 metadata fields verified working

**Access Attu UI:**
```bash
# From local machine
ssh -i ~/reku631_nebius -L 3000:localhost:3000 reku631@89.169.103.3
# Then open: http://localhost:3000
```

---

**Last Updated:** October 22, 2025  
**Documentation:** Complete production setup with all services configured and tested
