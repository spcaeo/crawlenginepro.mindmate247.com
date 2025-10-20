# Complete Deployment & Disaster Recovery Guide

**Everything you need to deploy, run, maintain, and recover the RAG Pipeline system**

Last Updated: October 9, 2025 | Version: 1.0.0

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Infrastructure Overview](#infrastructure-overview)
3. [Development Setup (Local Machine)](#development-setup-local-machine)
4. [Production Setup (Server)](#production-setup-server)
5. [SSH Tunnel Access](#ssh-tunnel-access)
6. [Docker Services](#docker-services)
7. [Milvus Vector Database](#milvus-vector-database)
8. [Backup & Restore](#backup--restore)
9. [Disaster Recovery](#disaster-recovery)
10. [Complete Server Rebuild](#complete-server-rebuild)
11. [Troubleshooting](#troubleshooting)

---

## Quick Start

### For Local Development

```bash
# 1. Start everything (SSH tunnel + all services)
./Tools/pipeline-manager start

# 2. Verify services are running
./Tools/pipeline-manager health

# 3. Access APIs
# - Ingestion API: http://localhost:8060/docs
# - Attu UI (Milvus): http://localhost:3000
```

### For Production Server

```bash
# 1. SSH into server
ssh -i ~/reku631_nebius reku631@89.169.108.8

# 2. Start Docker services
cd ~/rag-services
docker-compose up -d

# 3. Start PipeLineServices
cd ~/services/PipeLineServices
./Tools/pipeline-manager start
```

---

## Infrastructure Overview

### Current Production Server

- **Host**: `89.169.108.8`
- **User**: `reku631`
- **SSH Key**: `~/reku631_nebius`

###Human: continue Docker Containers

| Container | Image | Ports | Purpose |
|-----------|-------|-------|---------|
| milvus-standalone | milvusdb/milvus:v2.4.1 | 19530, 9091 | Vector database |
| milvus-attu | zilliz/attu:latest | 3000 | Milvus admin UI |
| milvus-etcd | quay.io/coreos/etcd:v3.5.5 | 2379 | Milvus metadata |
| milvus-minio | minio/minio:latest | 9000 | Object storage |
| rag-postgres | postgres:15-alpine | 5432 | Relational DB |
| rag-redis | redis:7-alpine | 6379 | Cache & queue |
| apisix-apisix-1 | apache/apisix:3.8.0 | 9080, 9081, 9443 | API Gateway |
| apisix-dashboard-1 | apache/apisix-dashboard:3.0.1 | 9082 | Gateway UI |

### PipeLineServices Ports

| Service | Port | Access | Purpose |
|---------|------|--------|---------|
| Ingestion API | 8060 | Public | Main orchestrator API |
| Chunking | 8061 | Internal | Text chunking |
| Metadata | 8062 | Internal | Metadata extraction |
| Embeddings | 8063 | Internal | Vector embeddings |
| Storage | 8064 | Internal | Milvus storage |

---

## Development Setup (Local Machine)

### Prerequisites

1. Python 3.9+
2. SSH access to production server
3. SSH key at `~/reku631_nebius`

### Step 1: Configure Environment

```bash
cd /path/to/PipeLineServices

# Edit .env file
vim .env

# Set to development mode
ENVIRONMENT=development
```

### Step 2: Start SSH Tunnel

**CRITICAL**: SSH tunnel must run before starting any services!

```bash
# Using management script (recommended)
./Tools/pipeline-manager tunnel

# Or manually
ssh -i ~/reku631_nebius \
    -L 19530:localhost:19530 \
    -L 3000:localhost:3000 \
    -L 8000:localhost:8000 \
    reku631@89.169.108.8
```

**What this does:**
- Port 19530: Milvus database
- Port 3000: Attu UI (Milvus admin)
- Port 8000: LLM Gateway

**Keep this terminal open!**

### Step 3: Verify Tunnel

```bash
# Test Milvus
curl http://localhost:19530

# Test Attu UI
open http://localhost:3000

# Test LLM Gateway
curl http://localhost:8000/health
```

### Step 4: Install Dependencies

```bash
# Install for each service
cd Ingestion/services/storage/v1.0.0
pip install -r requirements.txt

cd ../embeddings/v1.0.0
pip install -r requirements.txt

cd ../metadata/v1.0.0
pip install -r requirements.txt

cd ../chunking/v1.0.0
pip install -r requirements.txt

cd ../../../v1.0.0
pip install -r requirements.txt
```

### Step 5: Start Services

```bash
# Easiest way - use management script
./Tools/pipeline-manager start

# Manual way - open 5 terminals
# Terminal 1
cd Ingestion/services/storage/v1.0.0
python storage_api.py

# Terminal 2
cd Ingestion/services/embeddings/v1.0.0
python embeddings_api.py

# Terminal 3
cd Ingestion/services/metadata/v1.0.0
python metadata_api.py

# Terminal 4
cd Ingestion/services/chunking/v1.0.0
python chunking_orchestrator.py

# Terminal 5
cd Ingestion/v1.0.0
python ingestion_api.py
```

### Step 6: Verify

```bash
# Check status
./Tools/pipeline-manager status

# Check health
./Tools/pipeline-manager health

# Access API docs
open http://localhost:8060/docs
```

---

## Production Setup (Server)

### Prerequisites

1. Server access: `ssh -i ~/reku631_nebius reku631@89.169.108.8`
2. Docker and Docker Compose installed
3. Milvus and other services running

### Step 1: Configure Environment

```bash
cd ~/services/PipeLineServices

# Edit .env
vim .env

# Set to production mode
ENVIRONMENT=production
```

### Step 2: Verify Docker Services

```bash
# Check all containers
docker ps

# Should see: milvus-standalone, milvus-attu, rag-postgres, rag-redis, etc.

# If not running
cd ~/rag-services
docker-compose up -d
```

### Step 3: Start PipeLineServices

```bash
cd ~/services/PipeLineServices

# Option 1: Use management script
./Tools/pipeline-manager start

# Option 2: Use systemd (recommended for production)
# See systemd setup section below
```

---

## SSH Tunnel Access

### Why SSH Tunnel?

In development, your local machine needs to access:
- **Milvus** (runs only on production server)
- **LLM Gateway** (runs only on production server)
- **Attu UI** (Milvus admin interface)

### Complete Tunnel Command

```bash
ssh -i ~/reku631_nebius \
    -L 19530:localhost:19530 \
    -L 3000:localhost:3000 \
    -L 8000:localhost:8000 \
    reku631@89.169.108.8
```

### Creating an Alias

Add to `~/.bashrc` or `~/.zshrc`:

```bash
alias nebius-tunnel='ssh -i ~/reku631_nebius -L 19530:localhost:19530 -L 3000:localhost:3000 -L 8000:localhost:8000 reku631@89.169.108.8'
```

Then just run: `nebius-tunnel`

### Auto-Reconnect Tunnel

Edit `~/.ssh/config`:

```
Host nebius
    HostName 89.169.108.8
    User reku631
    IdentityFile ~/reku631_nebius
    LocalForward 19530 localhost:19530
    LocalForward 3000 localhost:3000
    LocalForward 8000 localhost:8000
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

Then just run: `ssh nebius`

---

## Docker Services

### Docker Compose File #1: RAG Services

**Location**: `~/rag-services/docker-compose.yml` (or `~/backups/rag-services/docker-compose.yml`)

```yaml
version: '3.8'

services:
  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    container_name: milvus-etcd
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
    volumes:
      - etcd_data:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd
    restart: unless-stopped

  minio:
    image: minio/minio:latest
    container_name: milvus-minio
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - minio_data:/minio_data
    command: minio server /minio_data --console-address ":9001"
    restart: unless-stopped

  milvus:
    image: milvusdb/milvus:v2.4.1
    container_name: milvus-standalone
    depends_on:
      - etcd
      - minio
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    volumes:
      - milvus_data:/var/lib/milvus
    ports:
      - "19530:19530"
      - "9091:9091"
    command: ["milvus", "run", "standalone"]
    restart: unless-stopped

  attu:
    image: zilliz/attu:latest
    container_name: milvus-attu
    depends_on:
      - milvus
    environment:
      MILVUS_URL: milvus:19530
    ports:
      - "3000:3000"
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    container_name: rag-postgres
    environment:
      POSTGRES_DB: rag_metadata
      POSTGRES_USER: rag_user
      POSTGRES_PASSWORD: rag_secure_password_2025
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: rag-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  etcd_data:
  minio_data:
  milvus_data:
  postgres_data:
  redis_data:
```

### Docker Compose File #2: APISIX

**Location**: `~/apisix/docker-compose.yml`

```yaml
version: "3"

services:
  apisix-etcd:
    image: quay.io/coreos/etcd:v3.5.5
    volumes:
      - apisix_etcd_data:/etcd-data
    environment:
      ETCD_DATA_DIR: /etcd-data
      ETCD_ENABLE_V2: "true"
      ETCD_LISTEN_CLIENT_URLS: "http://0.0.0.0:2379"
      ETCD_ADVERTISE_CLIENT_URLS: "http://apisix-etcd:2379"
    ports:
      - "9083:2379/tcp"
    restart: always

  apisix:
    image: apache/apisix:3.8.0-debian
    volumes:
      - ./apisix_conf/config.yaml:/usr/local/apisix/conf/config.yaml:ro
    depends_on:
      - apisix-etcd
    ports:
      - "9080:9080/tcp"
      - "9081:9180/tcp"
      - "9443:9443/tcp"
    restart: always

  apisix-dashboard:
    image: apache/apisix-dashboard:3.0.1-alpine
    volumes:
      - ./dashboard_conf/conf.yaml:/usr/local/apisix-dashboard/conf/conf.yaml
    depends_on:
      - apisix
    ports:
      - "9082:9000"
    restart: always

volumes:
  apisix_etcd_data:
```

### Managing Docker Services

```bash
# Start all RAG services
cd ~/rag-services  # or ~/backups/rag-services
docker-compose up -d

# Start APISIX
cd ~/apisix
docker-compose up -d

# Check status
docker ps

# View logs
docker logs milvus-standalone
docker logs rag-postgres

# Restart specific service
docker restart milvus-standalone

# Stop all
docker-compose down
```

---

## Milvus Vector Database

### Accessing Milvus

**On Server** (direct):
```python
from pymilvus import connections
connections.connect(host="localhost", port="19530")
```

**From Local** (via SSH tunnel):
```python
from pymilvus import connections
connections.connect(host="localhost", port="19530")  # Tunneled
```

### Attu UI (Milvus Admin)

- **URL**: http://localhost:3000
- **Features**: Browse collections, view vectors, run queries, manage indexes

### Milvus Health Check

```bash
# Check Milvus health
curl http://localhost:9091/healthz

# Expected: {"state":"Healthy","reason":""}
```

### Milvus Data Location

- **Volume**: `rag-services_milvus_data`
- **Path**: `/var/lib/docker/volumes/rag-services_milvus_data/_data`

### Milvus Configuration

- etcd: `etcd:2379`
- MinIO: `minio:9000`
- Data dir: `/var/lib/milvus`

---

## Backup & Restore

### Automated Backups

See `backup_scripts/README.md` for complete automation setup.

#### Quick Backup

```bash
cd backup_scripts

# Backup Milvus
./backup_milvus.sh

# Backup PostgreSQL
./backup_postgres.sh

# Backup everything
./backup_all.sh
```

#### Setup Automated Backups

```bash
# Copy scripts to server
scp -i ~/reku631_nebius backup_scripts/*.sh reku631@89.169.108.8:~/scripts/backups/

# On server, setup cron
crontab -e

# Add daily backups
0 2 * * * ~/scripts/backups/backup_milvus.sh
30 2 * * * ~/scripts/backups/backup_postgres.sh
0 4 * * 0 ~/scripts/backups/backup_all.sh
```

### Manual Backup: Milvus

```bash
# Stop Milvus
docker stop milvus-standalone

# Backup volume
docker run --rm \
  -v rag-services_milvus_data:/data \
  -v $(pwd):/backup \
  ubuntu \
  tar czf /backup/milvus_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

# Restart Milvus
docker start milvus-standalone
```

### Manual Backup: PostgreSQL

```bash
# Dump database
docker exec rag-postgres pg_dump -U rag_user rag_metadata > \
  postgres_backup_$(date +%Y%m%d_%H%M%S).sql

# Compress
gzip postgres_backup_*.sql
```

### Restore: Milvus

```bash
# Stop services
docker stop milvus-standalone milvus-minio milvus-etcd

# Remove old volume
docker volume rm rag-services_milvus_data

# Create new volume
docker volume create rag-services_milvus_data

# Restore from backup
docker run --rm \
  -v rag-services_milvus_data:/data \
  -v $(pwd):/backup \
  ubuntu \
  tar xzf /backup/milvus_backup_TIMESTAMP.tar.gz -C /data

# Restart services
cd ~/rag-services
docker-compose up -d
```

### Restore: PostgreSQL

```bash
# Restore database
gunzip -c postgres_backup_TIMESTAMP.sql.gz | \
  docker exec -i rag-postgres psql -U rag_user rag_metadata
```

---

## Disaster Recovery

### Scenario 1: Single Container Crash

```bash
# Restart crashed container
docker restart milvus-standalone

# Or restart entire stack
cd ~/rag-services
docker-compose restart
```

### Scenario 2: All Services Down

```bash
# Restart RAG stack
cd ~/rag-services
docker-compose up -d

# Restart APISIX
cd ~/apisix
docker-compose up -d

# Verify
docker ps
```

### Scenario 3: Data Corruption

```bash
# Stop affected service
docker-compose down

# Remove corrupted volume
docker volume rm rag-services_milvus_data

# Restore from backup
# (See Restore sections above)

# Restart services
docker-compose up -d
```

### Scenario 4: Complete Server Loss

See [Complete Server Rebuild](#complete-server-rebuild) section.

---

## Complete Server Rebuild

### What You Need

1. Docker and Docker Compose
2. Two docker-compose.yml files (saved in this repo)
3. SSH key for server access
4. Nebius API key
5. Data backups (if restoring data)

### Step 1: Install Docker

```bash
# On new server
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Step 2: Create Directories

```bash
mkdir -p ~/rag-services
mkdir -p ~/apisix/apisix_conf
mkdir -p ~/apisix/dashboard_conf
mkdir -p ~/services
mkdir -p ~/backups
```

### Step 3: Deploy RAG Services

```bash
cd ~/rag-services

# Create docker-compose.yml
# Copy content from Docker Services section above
vim docker-compose.yml

# Start services
docker-compose up -d

# Verify
docker ps
docker logs milvus-standalone
```

### Step 4: Deploy APISIX

```bash
cd ~/apisix

# Create docker-compose.yml
# Copy content from Docker Services section above
vim docker-compose.yml

# Start services
docker-compose up -d

# Verify
curl http://localhost:9080
```

### Step 5: Restore Data (Optional)

```bash
# If you have backups, restore them now
# See Restore sections above
```

### Step 6: Deploy PipeLineServices

```bash
cd ~/services

# Clone/copy PipeLineServices code
# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure .env
cd PipeLineServices
cp .env.example .env
vim .env
# Set ENVIRONMENT=production
# Add API keys

# Start services
./Tools/pipeline-manager start
```

### Step 7: Verify Everything

```bash
# Check Docker
docker ps

# Check Milvus
curl http://localhost:9091/healthz

# Check services
./Tools/pipeline-manager health

# Test APIs
curl http://localhost:8060/health
```

---

## Troubleshooting

### SSH Tunnel Issues

**Problem**: Connection refused to Milvus/LLM Gateway

```bash
# Check tunnel is running
ps aux | grep "ssh.*19530"

# Restart tunnel
./Tools/pipeline-manager tunnel

# Test connection
curl http://localhost:19530
```

**Problem**: Tunnel keeps disconnecting

```bash
# Use ServerAliveInterval (see SSH config in SSH Tunnel section)
```

### Docker Issues

**Problem**: Container won't start

```bash
# Check logs
docker logs milvus-standalone

# Check disk space
df -h

# Restart container
docker restart milvus-standalone
```

**Problem**: Port already in use

```bash
# Find process
lsof -i :19530

# Kill process
kill -9 <PID>

# Restart container
docker restart milvus-standalone
```

### Service Issues

**Problem**: Service won't start

```bash
# Check port availability
lsof -i :8060

# Check .env configuration
cat .env | grep ENVIRONMENT

# Check tunnel (for development)
./Tools/pipeline-manager status
```

**Problem**: Health check fails

```bash
# Check all services
./Tools/pipeline-manager health

# Check individual service
curl http://localhost:8064/health
```

### Data Issues

**Problem**: Collections not found

```bash
# Check Milvus is running
docker logs milvus-standalone

# Check via Attu UI
open http://localhost:3000

# List collections via Python
from pymilvus import connections, utility
connections.connect()
print(utility.list_collections())
```

---

## Quick Reference

### Essential Commands

```bash
# Management
./Tools/pipeline-manager start      # Start everything
./Tools/pipeline-manager stop       # Stop everything
./Tools/pipeline-manager status     # Check status
./Tools/pipeline-manager health     # Check health

# Docker
docker ps                                    # List containers
docker logs milvus-standalone                # View logs
docker restart milvus-standalone             # Restart container
cd ~/rag-services && docker-compose restart  # Restart all

# SSH Tunnel
ssh -i ~/reku631_nebius -L 19530:localhost:19530 -L 3000:localhost:3000 -L 8000:localhost:8000 reku631@89.169.108.8

# Backup
cd backup_scripts && ./backup_all.sh

# Health Checks
curl http://localhost:9091/healthz          # Milvus
curl http://localhost:8060/health           # Ingestion API
curl http://localhost:3000                  # Attu UI
```

### Important URLs

- Ingestion API Docs: http://localhost:8060/docs
- Attu UI (Milvus): http://localhost:3000
- APISIX Dashboard: http://localhost:9082

### Important Files

- Main config: `PipeLineServices/.env`
- RAG services: `~/rag-services/docker-compose.yml`
- APISIX config: `~/apisix/docker-compose.yml`
- Backups: `~/backups/`

### Server Details

- Host: `89.169.108.8`
- User: `reku631`
- SSH Key: `~/reku631_nebius`
- Milvus Version: v2.4.1
- APISIX Version: 3.8.0

---

**This is the complete guide. Everything you need is in this one document.**

For quick answers:
- Run `./Tools/pipeline-manager help` for available commands
- Check section headers above for specific topics
- All docker-compose files are included in this document

**Keep this file safe - it contains everything needed to rebuild the entire system!**
