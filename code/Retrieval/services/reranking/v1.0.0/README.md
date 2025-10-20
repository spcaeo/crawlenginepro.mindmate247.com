# Reranking Service v2.0.0

Rerank documents by relevance using BGE-Reranker-v2-M3 or Jina AI reranker.

Part of **Retrieval Pipeline** - Stage 2: Reranking

## Features

- **Cross-Encoder Reranking**: Uses BAAI/bge-reranker-v2-m3 for high-quality relevance scoring
- **Jina AI Support**: Alternative reranker backend via Jina AI API
- **Versioned API**: `/v2/rerank` with backward compatibility `/v1/rerank`
- **Health Monitoring**: `/health`, `/version` endpoints with API connectivity test
- **Batch Processing**: Rerank up to 100 documents per request
- **Speed-Optimized Defaults**: top_k=**3** (changed from 10 for faster pipeline)
- **RAG Pipeline Compatibility**: `/v1/rerank` endpoint for chunk-based reranking
- **Performance Metrics**: Track processing time
- **Security Middleware**: Localhost and internal network only

## API Endpoints

### Health & Info
- `GET /health` - Service health check
- `GET /version` - Version information

### Reranking
- `POST /v2/rerank` - Rerank documents by relevance
- `POST /v1/rerank` - Legacy endpoint (backward compatibility)

## Model

| Model | Type | Use Case |
|-------|------|----------|
| **bge-reranker-v2-m3** | BAAI/bge-reranker-v2-m3 | Cross-encoder reranking with high accuracy |

## Usage Example

### Local Testing (Direct Access)
```bash
curl -X POST http://localhost:8002/v2/rerank \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "documents": [
      "Machine learning is a subset of artificial intelligence...",
      "Python is a programming language...",
      "Deep learning uses neural networks for pattern recognition...",
      "JavaScript is used for web development..."
    ],
    "top_n": 2
  }'
```

## Response Format

```json
{
  "results": [
    {
      "index": 0,
      "relevance_score": 0.95,
      "document": "Machine learning is a subset of artificial intelligence..."
    },
    {
      "index": 2,
      "relevance_score": 0.87,
      "document": "Deep learning uses neural networks for pattern recognition..."
    }
  ],
  "query": "machine learning algorithms",
  "total_documents": 4,
  "returned_count": 2,
  "model": "BAAI/bge-reranker-v2-m3",
  "processing_time_ms": 145.3,
  "api_version": "2.0.0"
}
```

## Installation

```bash
pip install -r requirements.txt
python reranking_api.py
```

## Configuration

Edit `.env` file:
```bash
HOST=0.0.0.0
PORT=8072  # Retrieval pipeline internal service
MODEL_NAME=BAAI/bge-reranker-v2-m3
MAX_LENGTH=512
DEVICE=cpu
MAX_DOCUMENTS=100
RERANKER_BACKEND=bge  # or "jina" for Jina AI backend
JINA_AI_KEY=<your_jina_api_key>  # Required if RERANKER_BACKEND=jina
```

## Default Parameters

- `top_k`: **3** (speed-optimized for Retrieval pipeline, changed from 10 in v2.0.0)

## Production Deployment

### Target Setup
**Server:** 89.169.108.8
**Location:** `/home/reku631/services/reranking_v2.0.0/`
**Port:** 8002
**APISIX Route:** `/api/v2/rerank/*`
**API Key:** `sk-enterprise-mindmate247-2025-v2`

### Production Access (APISIX Gateway)
```bash
curl -X POST http://89.169.108.8:9080/api/v2/rerank/rerank \
  -H "apikey: sk-enterprise-mindmate247-2025-v2" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "documents": [
      "Machine learning is a subset of artificial intelligence...",
      "Python is a programming language...",
      "Deep learning uses neural networks for pattern recognition..."
    ],
    "top_n": 2
  }'
```

### Deployment Steps

1. **Create tarball**:
```bash
cd /Users/rakesh/Desktop/CrawlEnginePro/nebius_hosting/ai_studio/hosting/services/reranking
tar -czf reranking_v2.0.0.tar.gz v2.0.0/
```

2. **Upload to server**:
```bash
scp reranking_v2.0.0.tar.gz reku631@89.169.108.8:/home/reku631/
```

3. **Deploy on server**:
```bash
ssh reku631@89.169.108.8
cd /home/reku631/
mkdir -p services/reranking_v2.0.0
tar -xzf reranking_v2.0.0.tar.gz -C services/reranking_v2.0.0 --strip-components=1
cd services/reranking_v2.0.0
cp .env.example .env
pip install -r requirements.txt
nohup python reranking_api.py > reranking.log 2>&1 &
```

4. **Configure APISIX route** (via APISIX Admin API)

5. **Test with and without API keys**

## Security

- **Security Middleware**: Blocks all external direct access
- **APISIX Gateway**: Required for external access
- **API Key Authentication**: Enforced by APISIX
- **Rate Limiting**: Configured at gateway level
- **Internal Only**: Service only accepts localhost/internal network IPs

## Troubleshooting

### Service Health Check
```bash
curl http://localhost:8002/health
```

### Version Check
```bash
curl http://localhost:8002/version
```

### Check Logs
```bash
tail -f /home/reku631/services/reranking_v2.0.0/reranking.log
```

### Kill Process
```bash
pkill -f reranking_api.py
```

## Problems Fixed During Development

1. **Security Middleware**: Added middleware to block external direct access
2. **Versioned Endpoints**: Created `/v2/rerank` with `/v1/rerank` backward compatibility
3. **Proper Structure**: Organized into v2.0.0 directory with config, models, and API separation

See `/Users/rakesh/Desktop/CrawlEnginePro/nebius_hosting/ai_studio/hosting/services/ARCHITECTURE.md` for complete architecture.
