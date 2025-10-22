# VM Setup Status - Oct 22, 2025

## ✅ COMPLETED - PRODUCTION SERVER

### 1. VM Details
- **VM Name:** `lavender-chameleon-instance-2`
- **Instance ID:** `computeinstance-e00akjpdm3mceg5ps0`
- **Public IP:** `89.169.103.3`
- **Private IP:** `10.0.0.65/32`
- **Region:** `eu-north1`
- **Platform:** Non-GPU Intel Ice Lake (cpu-e2)
- **Resources:**
  - CPUs: 16 vCPUs
  - Memory: 64 GiB
  - Boot Disk: 1280 GiB SSD (Ubuntu 24.04 LTS)
- **Created:** Oct 21, 2025
- **Status:** ✅ Running (12+ hours uptime)

### 2. Network Configuration
- ✅ SSH configured on ports 22 AND 443
- ✅ Public IPv4: 89.169.103.3/32
- ✅ Private IPv4: 10.0.0.65/32
- ✅ Subnet: default-subnet-o9cxcezl
- ✅ DNS records configured:
  - milvus.mindmate247.com → 89.169.103.3
  - crawlenginepro.mindmate247.com → 89.169.103.3
  - mindmate247.com → 89.169.103.3

### 3. Software Installation
- ✅ Docker installed and running
- ✅ Python 3.12 installed
- ✅ Python virtual environment created
- ✅ Git, curl, wget, jq, tree installed
- ✅ All service dependencies installed (fastapi, uvicorn, pymilvus, etc.)

### 4. Milvus Database - **UPGRADED OCT 22, 2025**
- ✅ **Milvus v2.6.4** (Latest - Upgraded from v2.3.3)
- ✅ **Attu v2.5.7** (Latest open-source - Upgraded from v2.3.10)
- ✅ All containers healthy:
  - **milvus-standalone** (v2.6.4) - Port 19530 ✅ HEALTHY
  - **milvus-attu** (v2.5.7) - Port 3000 ✅ Admin UI
  - **milvus-etcd** (v3.5.5) - Port 2379 ✅ HEALTHY
  - **milvus-minio** (RELEASE.2023-03-20) - Ports 9000, 9001 ✅ HEALTHY
- ✅ Python connection verified
- ✅ Attu UI accessible via SSH tunnel
- ✅ **Fresh installation** - All data cleared during upgrade

**Milvus v2.6.4 New Features:**
- Native WAL (no Kafka/Pulsar dependency)
- RaBitQ 1-bit quantization
- Struct in ARRAY support
- JSON shredding (default enabled)
- Streaming node architecture
- Enhanced performance

### 5. Code Deployment
- ✅ All Ingestion services deployed
- ✅ All Retrieval services deployed
- ✅ Fixed temporal prompt deployed (concise 50-100 word answers)
- ✅ Directory structure:
  ```
  ~/crawlenginepro/
  ├── milvus/               # Docker Compose for Milvus v2.6.4
  ├── retrieval-services/   # All Python services
  ├── llm-gateway/          # LLM Gateway service
  └── backups/              # (reserved)
  ```

### 6. Local Development Environment
- ✅ All services running on Mac (development mode)
- ✅ SSH tunnel established to production Milvus
- ✅ Ports: 8070-8079 (Ingestion), 8090-8099 (Retrieval - reserved)
- ✅ LLM Gateway: 8075 (local development)

---

## 📊 SERVICE STATUS - OCT 22, 2025

### Local Development Services (Mac)
| Service | Port | Status | Version |
|---------|------|--------|---------|
| Ingestion API | 8070 | ✅ HEALTHY | v1.0.0 |
| Chunking | 8071 | ✅ HEALTHY | v1.0.0 |
| Metadata | 8072 | ✅ HEALTHY | v1.0.0 |
| Embeddings | 8073 | ✅ HEALTHY | v1.0.0 |
| Storage | 8074 | ✅ HEALTHY | v1.0.0 |
| LLM Gateway | 8075 | ✅ HEALTHY | v1.0.0 |

### Production Server (89.169.103.3)
| Service | Port | Status | Version |
|---------|------|--------|---------|
| Milvus Database | 19530 | ✅ HEALTHY | v2.6.4 |
| Attu UI | 3000 | ✅ RUNNING | v2.5.7 |
| Minio Object Storage | 9000/9001 | ✅ HEALTHY | 2023-03-20 |
| etcd | 2379 | ✅ HEALTHY | v3.5.5 |

**Note:** Retrieval services will be deployed to production server in future phase.

---

## 🗄️ MILVUS COLLECTIONS STATUS

### Current Collections (Fresh - Oct 22, 2025)
| Collection | Entities | Status | Purpose |
|------------|----------|--------|---------|
| simple_test | 1 | ✅ Active | Test collection (single document) |
| comprehensive_test | 18 | ✅ Active | Comprehensive test document (259 lines) |
| test_collection | 0 | ✅ Active | Empty test collection |

**All metadata fields verified populated:**
- ✅ Keywords
- ✅ Topics
- ✅ Questions
- ✅ Summary
- ✅ Semantic Keywords
- ✅ Entity Relationships
- ✅ Attributes

**Metadata Generation:** SambaNova Qwen3-32B via LLM Gateway

---

## ✅ RECENT UPGRADES (Oct 22, 2025)

### Milvus Upgrade: v2.3.3 → v2.6.4
- **Status:** ✅ COMPLETE
- **Duration:** ~45 minutes
- **Data Migration:** Fresh installation (all old data cleared)
- **Downtime:** ~10 minutes
- **Testing:** Verified with comprehensive test document

### Attu Upgrade: v2.3.10 → v2.5.7
- **Status:** ✅ COMPLETE
- **New Features:**
  - Enhanced search capabilities
  - Better visualization
  - WebSocket log support
  - REST API Playground (beta)
  - Improved role management

**Backup Created:**
- docker-compose.yml.backup_20251022_135000

---

## 🔧 PORT ALLOCATION SUMMARY

### Current Active Ports

**Development Services (Running Locally on Mac):**
- 8070: Ingestion API (Main orchestrator - Public)
- 8071: Chunking Service (Internal)
- 8072: Metadata Service (Internal)
- 8073: Embeddings Service (Internal)
- 8074: Storage Service (Internal)
- 8075: LLM Gateway (Shared)

**Production Infrastructure (Running on Server 89.169.103.3):**
- 19530: Milvus Vector Database v2.6.4
- 3000: Attu Admin UI v2.5.7
- 9000/9001: Minio Object Storage
- 2379: etcd v3.5.5

### Future Port Allocation (Not Yet Deployed)

**Production Services (Will run on server):**
- 8060-8069: Production Ingestion Pipeline
- 8110-8119: Production Retrieval Pipeline

**Staging Services (Will run on server):**
- 8080-8089: Staging Ingestion Pipeline
- 8100-8109: Staging Retrieval Pipeline

**Development Retrieval (Reserved for local Mac):**
- 8090-8099: Development Retrieval Pipeline (not yet implemented)

---

## 🎯 TESTING & VALIDATION

### Completed Tests (Oct 22, 2025)
- ✅ Simple document ingestion (1 chunk)
- ✅ Comprehensive document ingestion (18 chunks)
- ✅ All 7 metadata fields populated
- ✅ Milvus v2.6.4 compatibility verified
- ✅ Attu v2.5.7 UI verified
- ✅ SSH tunnel connectivity verified
- ✅ Service health checks passing
- ✅ LLM Gateway → SambaNova integration verified

### Sample Results
**Document:** ComprehensiveTestDocument.md
- Size: 11,577 characters (259 lines)
- Processing time: 39.9 seconds
- Chunks created: 18
- Metadata generation: 100% success
- Storage: 100% success

---

## 📝 CONFIGURATION FILES

### Docker Compose (Milvus)
**Location:** `~/crawlenginepro/milvus/docker-compose.yml`
**Updated:** Oct 22, 2025
**Key Settings:**
- Milvus image: `milvusdb/milvus:v2.6.4`
- Attu image: `zilliz/attu:v2.5.7`
- Health checks enabled
- Network: `milvus` (bridge)

### Environment Configuration
**Location:** `/code/shared/.env.dev`
**Key Variables:**
- `PIPELINE_ENV=dev`
- `LLM_GATEWAY_URL_DEVELOPMENT=http://localhost:8075/v1/chat/completions`
- `MILVUS_HOST=localhost`
- `MILVUS_PORT=19530`
- `SAMBANOVA_API_KEY=9a2acb34-97f8-4f3c-a37c-d11aa5b699dd`

### Model Registry
**Active Preset:** `SAMBANOVA_FAST`
- Model: `Meta-Llama-3.1-8B-Instruct`
- Provider: SambaNova Cloud
- Max tokens: 1024
- Temperature: 0.1

---

## 🔗 ACCESS INFORMATION

### SSH Access (Mac → Production Server)
```bash
ssh -i ~/reku631_nebius reku631@89.169.103.3
```

### SSH Tunnel (Milvus + Attu)
```bash
ssh -i ~/reku631_nebius \
  -L 19530:localhost:19530 \
  -L 3000:localhost:3000 \
  reku631@89.169.103.3
```

### Service URLs (via SSH Tunnel)
- **Attu UI:** http://localhost:3000
- **Milvus:** localhost:19530 (PyMilvus connection)
- **Minio Console:** http://localhost:9001

### Local Development URLs
- **Ingestion API:** http://localhost:8070
- **LLM Gateway:** http://localhost:8075
- **Health Checks:** http://localhost:8070/health

---

## ⚠️ IMPORTANT NOTES

### Current Environment
- **This is a PRODUCTION server** with live Milvus v2.6.4
- **Development work happens locally** on Mac (ports 8070-8079)
- **SSH tunnel required** for Milvus/Attu access from local machine
- **All old data was cleared** during Oct 22 upgrade

### Attu UI Configuration
- Default page size: Cannot be set via environment variable
- Page size is stored in browser's local storage
- To change: Use UI dropdown or browser console: `localStorage.setItem('dataPageSize', '50')`

### Server Specifications
- **16 vCPUs, 64 GiB RAM** - Sufficient for current workload
- **1280 GiB SSD** - Ample storage for vector database
- **No GPU** - Not required for current services

---

## 📋 NEXT STEPS

### Immediate (Complete)
- ✅ Milvus v2.6.4 upgrade
- ✅ Attu v2.5.7 upgrade
- ✅ Comprehensive test document ingestion
- ✅ Metadata generation verification

### Short-term (Pending)
- ⏳ Deploy production data to Milvus
- ⏳ Deploy Retrieval services to production server
- ⏳ Configure production ingestion pipeline on server
- ⏳ Set up monitoring and alerting

### Long-term (Planned)
- ⏳ Implement automated backups
- ⏳ Set up CI/CD pipeline
- ⏳ Configure SSL/TLS for production services
- ⏳ Implement API authentication

---

**Last Updated:** Oct 22, 2025 10:00 UTC
**Status:** ✅ **PRODUCTION READY** - Milvus v2.6.4 & Attu v2.5.7 upgraded and verified
**Environment:** Hybrid (Local development + Remote production Milvus)
