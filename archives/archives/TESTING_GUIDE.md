# CrawlEnginePro - Complete Testing Guide
## Local → Staging → Production Deployment Workflow

---

## Infrastructure Overview

### ⚠️ CRITICAL: Where Things Run

**On Server (89.169.108.8) ONLY:**
- Milvus vector database (port 19530)
- Attu UI (port 3000)
- LLM Gateway / Nebius AI Studio (port 8000)
- PostgreSQL (port 5432)
- Redis (port 6379)
- All Docker services

**On Local Machine (for Development):**
- Python services (connect to server infrastructure via SSH tunnel)
- Code development
- Testing before deployment

**Key Point**: You **cannot** run a fully local version because Milvus and infrastructure are **server-only**. Local testing requires SSH tunnel to server infrastructure.

---

## Testing Workflow: 3-Stage Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                        TESTING WORKFLOW                          │
│                                                                   │
│  Local Development → Deploy to Dev → Test Staging → Production  │
│  (SSH Tunnel)         (Server)       (Server)       (Server)     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Stage 1: Local Development Testing

### Prerequisites

1. **SSH Tunnel to Server Infrastructure** (REQUIRED)
   ```bash
   ssh -i ~/reku631_nebius \
       -L 19530:localhost:19530 \
       -L 3000:localhost:3000 \
       -L 8000:localhost:8000 \
       reku631@89.169.108.8
   ```

   **Keep this terminal open throughout local testing!**

2. **Local Python Environment**
   ```bash
   cd ~/Desktop/crawlenginepro.mindmate247.com/code

   # Create local virtual environment
   python3 -m venv ../local_dev/venv
   source ../local_dev/venv/bin/activate

   # Install all dependencies
   pip install -r Ingestion/services/storage/v1.0.0/requirements.txt
   pip install -r Ingestion/services/embeddings/v1.0.0/requirements.txt
   pip install -r Ingestion/services/metadata/v1.0.0/requirements.txt
   pip install -r Ingestion/services/chunking/v1.0.0/requirements.txt
   pip install -r Ingestion/services/llm_gateway/v1.0.0/requirements.txt
   pip install -r Ingestion/v1.0.0/requirements.txt
   pip install -r Retrieval/v1.0.0/requirements.txt
   ```

3. **Configure Local Environment**
   ```bash
   # Link development .env file
   cd ~/Desktop/crawlenginepro.mindmate247.com/code
   ln -sf shared/.env.dev .env

   # Verify it points to development ports (8070-8095)
   cat .env | grep PORT
   ```

### Local Testing Steps

#### Test 1: Individual Service Testing

Start services manually one by one for debugging:

```bash
# Terminal 1 (SSH Tunnel - keep running)
ssh -i ~/reku631_nebius -L 19530:localhost:19530 -L 3000:localhost:3000 -L 8000:localhost:8000 reku631@89.169.108.8

# Terminal 2 (Storage Service)
cd ~/Desktop/crawlenginepro.mindmate247.com/code
source ../local_dev/venv/bin/activate
export PYTHONPATH=$PWD:$PWD/shared
python Ingestion/services/storage/v1.0.0/storage_api.py

# Terminal 3 (Embeddings Service)
source ../local_dev/venv/bin/activate
export PYTHONPATH=$PWD:$PWD/shared
python Ingestion/services/embeddings/v1.0.0/embeddings_api.py

# Continue for other services...
```

**Verify each service:**
```bash
# Storage service (should be on port 8074)
curl http://localhost:8074/health

# Embeddings service (should be on port 8073)
curl http://localhost:8073/health
```

#### Test 2: Full Ingestion Pipeline

```bash
# With all Ingestion services running locally, test document ingestion:

curl -X POST http://localhost:8070/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Test document for local development",
    "document_id": "local_test_001",
    "collection_name": "local_test_dev",
    "embedding_model": "jina-embeddings-v3",
    "chunking_strategy": "semantic"
  }'
```

**Expected Result:**
- Status 200 OK
- Collection created in Milvus (check via Attu UI: http://localhost:3000)
- Vectors stored successfully

#### Test 3: Full Retrieval Pipeline

```bash
# With all Retrieval services running locally:

curl -X POST http://localhost:8090/v1/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test document",
    "collection_name": "local_test_dev",
    "top_k": 5
  }'
```

**Expected Result:**
- Status 200 OK
- Retrieved chunks with relevance scores
- Generated answer from LLM

### Local Testing Checklist

- [ ] SSH tunnel active and stable
- [ ] All 6 Ingestion services healthy
- [ ] All 6 Retrieval services healthy
- [ ] Document ingestion successful
- [ ] Milvus collection created (verify in Attu UI)
- [ ] Vector search working
- [ ] Answer generation working
- [ ] No errors in service logs

---

## Stage 2: Development Environment on Server

Once local testing passes, deploy to server development environment:

### Deploy to Server

```bash
# From local machine
cd ~/Desktop/crawlenginepro.mindmate247.com/code
./deploy/deploy.sh
```

### Setup Development Environment

```bash
# SSH to server
ssh -i ~/reku631_nebius reku631@89.169.108.8

# First time setup (create venv, install dependencies)
cd ~/crawlenginepro/code
./deploy/server_setup.sh dev

# Verify API keys are set
cat ~/crawlenginepro/code/shared/.env.dev | grep API_KEY
```

### Start Development Services

```bash
cd ~/crawlenginepro/code

# Start all services
./deploy/manage.sh dev start

# Check status
./deploy/manage.sh dev status
```

**Expected Output:**
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

### Test on Development Environment

```bash
# From local machine with SSH tunnel:
ssh -i ~/reku631_nebius -L 8070:localhost:8070 -L 8090:localhost:8090 -L 19530:localhost:19530 -L 3000:localhost:3000 reku631@89.169.108.8

# Test Ingestion
curl -X POST http://localhost:8070/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Development environment test document",
    "document_id": "dev_test_001",
    "collection_name": "dev_test_collection",
    "embedding_model": "jina-embeddings-v3"
  }'

# Test Retrieval
curl -X POST http://localhost:8090/v1/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "development test",
    "collection_name": "dev_test_collection",
    "top_k": 5
  }'
```

### Development Testing Checklist

- [ ] Code deployed to server successfully
- [ ] Virtual environment created and dependencies installed
- [ ] All 12 services running (6 ingestion + 6 retrieval)
- [ ] Ingestion pipeline working
- [ ] Retrieval pipeline working
- [ ] Logs accessible and clean (no errors)
- [ ] Performance acceptable

---

## Stage 3: Staging Environment

After development testing passes, deploy to staging for pre-production validation:

### Deploy to Staging

```bash
# SSH to server
ssh -i ~/reku631_nebius reku631@89.169.108.8

# Setup staging environment (first time only)
cd ~/crawlenginepro/code
./deploy/server_setup.sh staging

# Verify staging configuration
cat ~/crawlenginepro/code/shared/.env.staging | grep PORT
# Should see: INGESTION_API_PORT=8080, RETRIEVAL_API_PORT=8100
```

### Start Staging Services

```bash
cd ~/crawlenginepro/code

# Start all staging services
./deploy/manage.sh staging start

# Check status
./deploy/manage.sh staging status
```

### Test on Staging

```bash
# From local machine with SSH tunnel:
ssh -i ~/reku631_nebius -L 8080:localhost:8080 -L 8100:localhost:8100 -L 19530:localhost:19530 -L 3000:localhost:3000 reku631@89.169.108.8

# Test Ingestion
curl -X POST http://localhost:8080/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Staging environment test document",
    "document_id": "staging_test_001",
    "collection_name": "staging_test_collection",
    "embedding_model": "E5-Mistral-7B-Instruct"
  }'

# Test Retrieval
curl -X POST http://localhost:8100/v1/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "staging test",
    "collection_name": "staging_test_collection",
    "top_k": 5
  }'
```

### Staging Testing Checklist

- [ ] All services running on staging ports (8080-8109)
- [ ] No port conflicts with development environment
- [ ] Ingestion working with different embedding model
- [ ] Retrieval working
- [ ] Performance monitoring
- [ ] Error handling working correctly
- [ ] Logs clean and informative

---

## Stage 4: Production Deployment

After staging validation, deploy to production:

### Deploy to Production

```bash
# SSH to server
ssh -i ~/reku631_nebius reku631@89.169.108.8

# Setup production environment (first time only)
cd ~/crawlenginepro/code
./deploy/server_setup.sh prod

# Verify production configuration
cat ~/crawlenginepro/code/shared/.env.prod | grep PORT
# Should see: INGESTION_API_PORT=8060, RETRIEVAL_API_PORT=8110
```

### Pre-Production Checks

```bash
# Verify all API keys are production-ready
cat ~/crawlenginepro/code/shared/.env.prod | grep API_KEY

# Ensure logging is set to WARNING (not DEBUG)
cat ~/crawlenginepro/code/shared/.env.prod | grep LOG_LEVEL

# Backup current production data (if exists)
docker exec milvus-standalone sh -c "milvus-backup create"
```

### Start Production Services

```bash
cd ~/crawlenginepro/code

# Start all production services
./deploy/manage.sh prod start

# Check status
./deploy/manage.sh prod status

# Monitor logs for first few minutes
./deploy/manage.sh prod logs
```

### Production Testing

```bash
# From local machine with SSH tunnel:
ssh -i ~/reku631_nebius -L 8060:localhost:8060 -L 8110:localhost:8110 -L 19530:localhost:19530 reku631@89.169.108.8

# Test Ingestion
curl -X POST http://localhost:8060/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Production environment test document",
    "document_id": "prod_test_001",
    "collection_name": "prod_test_collection",
    "embedding_model": "jina-embeddings-v3"
  }'

# Test Retrieval
curl -X POST http://localhost:8110/v1/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "query": "production test",
    "collection_name": "prod_test_collection",
    "top_k": 5
  }'
```

### Production Deployment Checklist

- [ ] All services running on production ports (8060-8119)
- [ ] No conflicts with dev/staging
- [ ] Ingestion pipeline operational
- [ ] Retrieval pipeline operational
- [ ] Logging at WARNING level
- [ ] Performance optimized
- [ ] Monitoring in place
- [ ] Backup strategy confirmed

---

## Testing Best Practices

### 1. Use Different Collections for Each Environment

```
Development:   {doc_name}_dev_{model}_{dims}
Staging:       {doc_name}_staging_{model}_{dims}
Production:    {doc_name}_prod_{model}_{dims}
```

### 2. Test with Multiple Embedding Models

```bash
# Test Jina (1024 dims)
curl -X POST http://localhost:8070/v1/ingest \
  -d '{"embedding_model": "jina-embeddings-v3", ...}'

# Test SambaNova (4096 dims)
curl -X POST http://localhost:8070/v1/ingest \
  -d '{"embedding_model": "E5-Mistral-7B-Instruct", ...}'
```

### 3. Monitor Service Health

```bash
# Check all services
./deploy/manage.sh dev status

# Monitor specific service logs
./deploy/manage.sh dev logs storage
./deploy/manage.sh dev logs ingestion
```

### 4. Progressive Rollout

1. **Week 1**: Deploy to development, test thoroughly
2. **Week 2**: Deploy to staging, validate with real-world scenarios
3. **Week 3**: Deploy to production during off-peak hours
4. **Ongoing**: Monitor production, keep dev/staging in sync

---

## Troubleshooting Testing Issues

### Issue: Services won't start locally

**Solution:**
```bash
# Verify SSH tunnel is active
lsof -i :19530

# Check Python path
export PYTHONPATH=$PWD:$PWD/shared
echo $PYTHONPATH

# Check .env file is linked correctly
ls -la .env
```

### Issue: Port conflicts between environments

**Solution:**
```bash
# Check which ports are in use
lsof -i :8070-8119

# Verify correct environment is active
cat .env | grep ENVIRONMENT

# Stop conflicting environment
./deploy/manage.sh dev stop
./deploy/manage.sh staging stop
```

### Issue: Cannot connect to Milvus

**Solution:**
```bash
# Verify SSH tunnel
lsof -i :19530

# Test Milvus connection
curl http://localhost:19530

# Check Milvus is running on server
ssh -i ~/reku631_nebius reku631@89.169.108.8 "docker ps | grep milvus"
```

---

## Quick Reference

### Environment Port Ranges

| Environment | Ingestion | Retrieval |
|-------------|-----------|-----------|
| Development | 8070-8075 | 8090-8095 |
| Staging     | 8080-8085 | 8100-8105 |
| Production  | 8060-8065 | 8110-8115 |

### SSH Tunnel Commands

```bash
# Local development testing
ssh -i ~/reku631_nebius \
    -L 19530:localhost:19530 \
    -L 3000:localhost:3000 \
    -L 8000:localhost:8000 \
    reku631@89.169.108.8

# Development environment testing
ssh -i ~/reku631_nebius \
    -L 8070:localhost:8070 \
    -L 8090:localhost:8090 \
    -L 19530:localhost:19530 \
    reku631@89.169.108.8

# Staging environment testing
ssh -i ~/reku631_nebius \
    -L 8080:localhost:8080 \
    -L 8100:localhost:8100 \
    -L 19530:localhost:19530 \
    reku631@89.169.108.8

# Production environment testing
ssh -i ~/reku631_nebius \
    -L 8060:localhost:8060 \
    -L 8110:localhost:8110 \
    -L 19530:localhost:19530 \
    reku631@89.169.108.8
```

---

**Ready to Start Testing!**

Follow this guide stage by stage. Do not skip to production without validating in development and staging first.
