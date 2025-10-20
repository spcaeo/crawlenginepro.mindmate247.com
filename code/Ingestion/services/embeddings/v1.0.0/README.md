# Embeddings Service v1.0.0 - Multi-Provider Support

Part of **PipeLineServices** - Ingestion Pipeline Internal Service

**Version:** 1.0.0
**Port:** 8073 (Internal only)
**Providers:** Jina AI, Nebius AI Studio, SambaNova AI
**Vectors:** Dense embeddings (optional sparse support)
**Speed:** 10-20x faster than local CPU inference

## Architecture

```
Ingestion API (8060)
    ↓
Chunking Service (8071)
    ↓
Embeddings Service (8073) ← YOU ARE HERE
    ↓ (Multiple providers)
    ├── Jina AI API (1024/2048-dim)
    ├── Nebius AI Studio API (3584/4096-dim)
    └── SambaNova AI API (4096-dim, FREE)
```

---

## 🚀 Overview

Version 1.0.0 provides **multi-provider embedding support** with **auto-dimension detection** for maximum flexibility and performance.

### Key Features

- ✅ **Multi-Provider Support**: Jina AI, Nebius AI Studio, SambaNova AI
- ✅ **Auto-Dimension Detection**: Dimensions automatically match selected model
- ✅ **FREE Option**: SambaNova AI (4096-dim embeddings at no cost)
- ✅ **Model Selection**: Choose embedding model via parameter
- ✅ **Fast Performance**: 50-200ms per batch (GPU-accelerated)
- ✅ **Batch Processing**: Up to 128 texts per request
- ✅ **Caching**: LRU cache for repeated texts
- ✅ **Failover**: Automatic fallback between providers

---

## 📊 Supported Models

### Jina AI (Fast, Multilingual)

| Model | Dimensions | Cost | Use Case | Speed |
|-------|------------|------|----------|-------|
| **jina-embeddings-v3** | 1024 | Paid | Fast, multilingual (89 languages) - **DEFAULT** | 50-100ms |
| **jina-embeddings-v4** | 2048 | Paid | Multimodal (text + images) | 80-120ms |

**Recommended**: Fast and cost-effective, supports 89 languages

### Nebius AI Studio (High Quality)

| Model | Dimensions | Cost | Use Case | Speed |
|-------|------------|------|----------|-------|
| **intfloat/e5-mistral-7b-instruct** | 4096 | Paid | Best for RAG, high accuracy | 100-150ms |
| **BAAI/bge-en-icl** | 4096 | Paid | English-optimized | 100-140ms |
| **BAAI/bge-multilingual-gemma2** | 3584 | Paid | Multilingual | 120-160ms |
| **Qwen/Qwen3-Embedding-8B** | 4096 | Paid | Latest Qwen model | 120-160ms |

**Recommended**: High-quality embeddings for production RAG

### SambaNova AI (FREE)

| Model | Dimensions | Cost | Use Case | Speed |
|-------|------------|------|----------|-------|
| **E5-Mistral-7B-Instruct** | 4096 | **FREE** | Same as Nebius E5, no cost | 100-150ms |

**Recommended**: FREE tier, same quality as Nebius E5-Mistral, perfect for development and cost-sensitive production

---

## 🔌 API Endpoints

### Health & Info
- `GET /health` - Health check with provider connectivity tests
- `GET /version` - Version information

### Embedding Generation
- `POST /v1/embeddings` - Generate embeddings (single or batch)

---

## 📝 Usage Examples

### Example 1: Default Jina Embeddings (1024-dim, fast)

```python
import requests

payload = {
    "input": "RAG systems combine retrieval and generation for accurate answers.",
    "model": "jina-embeddings-v3"  # Optional, this is the default
}

response = requests.post("http://localhost:8073/v1/embeddings", json=payload)
result = response.json()

print(f"Dimension: {result['dense_dimension']}")  # 1024
print(f"Provider: {result['source']}")  # jina_api
print(f"Processing time: {result['processing_time_ms']}ms")
print(f"Embedding: {result['data'][0]['dense_embedding'][:5]}...")
```

**Response:**
```json
{
  "data": [
    {
      "dense_embedding": [0.123, -0.456, 0.789, ...],  // 1024 floats
      "index": 0
    }
  ],
  "model": "jina-embeddings-v3",
  "dense_dimension": 1024,
  "processing_time_ms": 85.3,
  "source": "jina_api",
  "cached": false
}
```

### Example 2: FREE 4096-dim Embeddings (SambaNova)

```python
import requests

payload = {
    "input": "Your text content here...",
    "model": "E5-Mistral-7B-Instruct"  # FREE tier
}

response = requests.post("http://localhost:8073/v1/embeddings", json=payload)
result = response.json()

print(f"Dimension: {result['dense_dimension']}")  # 4096
print(f"Provider: {result['source']}")  # sambanova_api
print(f"Cost: FREE")
```

### Example 3: High-Quality Nebius Embeddings (4096-dim)

```python
import requests

payload = {
    "input": "Your text content here...",
    "model": "intfloat/e5-mistral-7b-instruct"  # Best for RAG
}

response = requests.post("http://localhost:8073/v1/embeddings", json=payload)
result = response.json()

print(f"Dimension: {result['dense_dimension']}")  # 4096
print(f"Provider: {result['source']}")  # nebius_api
```

### Example 4: Batch Processing (Recommended)

```python
import requests

payload = {
    "input": [
        "First text to embed",
        "Second text to embed",
        "Third text to embed",
        "Fourth text to embed"
    ],
    "model": "jina-embeddings-v3"  # Default
}

response = requests.post("http://localhost:8073/v1/embeddings", json=payload)
result = response.json()

for item in result['data']:
    print(f"Index {item['index']}: {len(item['dense_embedding'])} dims")
```

**Performance gain**: Batch processing is 3-5x faster than sequential single calls

### Example 5: Multimodal Embeddings (Jina v4)

```python
import requests

payload = {
    "input": "Text with potential image context...",
    "model": "jina-embeddings-v4"  // 2048-dim, multimodal
}

response = requests.post("http://localhost:8073/v1/embeddings", json=payload)
result = response.json()

print(f"Dimension: {result['dense_dimension']}")  # 2048
print(f"Provider: {result['source']}")  # jina_api
```

---

## ⚙️ Configuration

### Default Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model` | `jina-embeddings-v3` | Embedding model (see Supported Models) |
| `input` | - | Single text or array of texts (required) |

### Auto-Dimension Detection

Collection dimensions **automatically match** the selected embedding model:
- `jina-embeddings-v3` → 1024 dims
- `jina-embeddings-v4` → 2048 dims
- `intfloat/e5-mistral-7b-instruct` (Nebius) → 4096 dims
- `E5-Mistral-7B-Instruct` (SambaNova) → 4096 dims
- `BAAI/bge-multilingual-gemma2` → 3584 dims

**No manual dimension configuration needed!**

### Environment Variables

All settings in `config.py`:

```python
# API Version
API_VERSION = "1.0.0"

# Server
PORT = 8063
HOST = "0.0.0.0"

# Provider API Keys
JINA_API_KEY = "your_jina_key_here"
JINA_API_URL = "https://api.jina.ai/v1/embeddings"

NEBIUS_API_KEY = "your_nebius_key_here"
NEBIUS_API_URL = "https://api.studio.nebius.ai/v1/embeddings"

SAMBANOVA_API_KEY = "your_sambanova_key_here"
SAMBANOVA_API_URL = "https://api.sambanova.ai/v1/embeddings"

# Performance
MAX_CONCURRENT_REQUESTS = 20  # Parallel API calls
BATCH_SIZE = 32
MAX_BATCH_SIZE = 128

# Caching
ENABLE_CACHING = True
CACHE_TTL = 7200  # 2 hours
CACHE_MAX_SIZE = 10000
```

---

## 🚀 Performance Comparison

### Provider Speed Comparison (22 chunks)

| Provider | Model | Dimension | Time | Per Chunk | Cost |
|----------|-------|-----------|------|-----------|------|
| **Jina AI** | jina-embeddings-v3 | 1024 | ~1.8s | 80ms | Paid |
| **Jina AI** | jina-embeddings-v4 | 2048 | ~2.2s | 100ms | Paid |
| **Nebius AI** | e5-mistral-7b-instruct | 4096 | ~2.8s | 125ms | Paid |
| **SambaNova** | E5-Mistral-7B-Instruct | 4096 | ~2.8s | 125ms | **FREE** |

### Scaling (100 chunks)

| Provider | Model | Time | Throughput |
|----------|-------|------|------------|
| **Jina AI** | jina-embeddings-v3 | ~8s | 12.5 chunks/sec |
| **Nebius AI** | e5-mistral-7b-instruct | ~12s | 8.3 chunks/sec |
| **SambaNova** | E5-Mistral-7B-Instruct | ~12s | 8.3 chunks/sec |

**Recommendation**: Use Jina v3 (1024-dim) for speed, Nebius/SambaNova (4096-dim) for quality

---

## 💰 Cost Analysis

### Provider Pricing

| Provider | Model | Price | Per 1M Tokens | Per Document (22 chunks) |
|----------|-------|-------|---------------|--------------------------|
| **Jina AI** | jina-embeddings-v3 | Paid | ~$0.10 | ~$0.0011 |
| **Nebius AI** | e5-mistral-7b-instruct | Paid | ~$0.20 | ~$0.0022 |
| **SambaNova** | E5-Mistral-7B-Instruct | **FREE** | $0 | **$0** |

**Typical document**: ~500 tokens/chunk × 22 chunks = 11,000 tokens

### Cost for 1000 Documents

| Provider | Cost | Time |
|----------|------|------|
| **Jina AI** | ~$1.10 | 30 minutes |
| **Nebius AI** | ~$2.20 | 47 minutes |
| **SambaNova** | **$0** | 47 minutes |

**Recommendation**: Use SambaNova FREE tier for development and cost-sensitive production, Jina for speed-critical applications

---

## 🔄 Dense vs Sparse Vectors

### Current Implementation (v1.0.0)

- **Dense vectors**: ✅ Supported (all providers)
- **Sparse vectors**: ❌ Not supported (removed for simplicity)

### What You Get (Dense Vectors Only)

✅ Semantic similarity (90%+ of search quality)
✅ Synonym matching
✅ Context understanding
✅ Cross-lingual search (with multilingual models)

### What's Missing (No Sparse Vectors)

❌ Exact keyword matching (e.g., product codes, SKUs)
❌ Technical term precision (e.g., "COVID-19" vs "coronavirus")
❌ BM25-style term frequency scoring

### Recommendation

**For most RAG applications**, dense-only embeddings provide excellent search quality. If you need exact keyword matching, consider adding metadata filters (keywords field) or using a hybrid search approach with a separate BM25 index.

---

## 📦 Deployment

### Prerequisites

**API Keys Required**: At least one provider API key must be configured

```bash
# Required: At least one of these
JINA_API_KEY=your_jina_key
NEBIUS_API_KEY=your_nebius_key
SAMBANOVA_API_KEY=your_sambanova_key  # FREE tier
```

### Local Development

```bash
cd /PipeLineServices/Ingestion/services/embeddings/v1.0.0
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure .env
cp .env.example .env
nano .env  # Add API keys

# Start service
python3 embeddings_api.py
```

Expected output:
```
================================================================================
Embeddings Service v1.0.0
================================================================================
Port: 8063
Providers:
  ✅ Jina AI (jina-embeddings-v3, 1024-dim)
  ✅ Nebius AI Studio (e5-mistral-7b-instruct, 4096-dim)
  ✅ SambaNova AI (E5-Mistral-7B-Instruct, 4096-dim, FREE)
Default model: jina-embeddings-v3 (1024-dim)
Batch size: 32 (max 128)
Caching: Enabled
================================================================================
```

### Production (Server)

Same setup - Configure API keys in `.env`

---

## 🔍 Model Selection Guide

### Choose by Use Case

| Use Case | Recommended Model | Provider | Dimension | Why |
|----------|-------------------|----------|-----------|-----|
| **Fast ingestion** | jina-embeddings-v3 | Jina | 1024 | Fastest, multilingual |
| **High accuracy** | intfloat/e5-mistral-7b-instruct | Nebius | 4096 | Best for RAG |
| **FREE/Cost-sensitive** | E5-Mistral-7B-Instruct | SambaNova | 4096 | No cost, same quality |
| **Multimodal** | jina-embeddings-v4 | Jina | 2048 | Text + images |
| **Multilingual** | BAAI/bge-multilingual-gemma2 | Nebius | 3584 | Cross-lingual search |

### Choose by Budget

| Budget | Recommended Model | Provider |
|--------|-------------------|----------|
| **Development** | E5-Mistral-7B-Instruct | SambaNova (FREE) |
| **Low volume** | jina-embeddings-v3 | Jina (cheapest paid) |
| **High volume** | E5-Mistral-7B-Instruct | SambaNova (FREE) |
| **Quality-critical** | intfloat/e5-mistral-7b-instruct | Nebius |

---

## 🧪 Testing

### Test Service

```bash
# Start service
python3 embeddings_api.py

# Health check
curl http://localhost:8073/health

# Test default model (Jina v3)
curl -X POST http://localhost:8073/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Test text for embeddings"
  }'

# Test SambaNova FREE
curl -X POST http://localhost:8073/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Test text for embeddings",
    "model": "E5-Mistral-7B-Instruct"
  }'
```

### Performance Testing

```python
import time
import requests

texts = ["Test text " + str(i) for i in range(100)]

start = time.time()
response = requests.post("http://localhost:8073/v1/embeddings", json={
    "input": texts,
    "model": "jina-embeddings-v3"
})
duration = time.time() - start

print(f"100 texts in {duration:.1f}s ({100/duration:.1f} texts/sec)")
print(f"Dimension: {response.json()['dense_dimension']}")
```

---

## 🐛 Troubleshooting

### Provider API Connection Failed

```bash
# Check health endpoint
curl http://localhost:8073/health

# Should show provider connectivity:
# "jina_connected": true
# "nebius_connected": true
# "sambanova_connected": true

# If a provider is down, service will failover to another provider
```

### Missing API Key

```bash
# Check .env file
cat .env | grep API_KEY

# At least one provider API key must be configured
# Service will fail to start if no API keys are found
```

### Dimension Mismatch

```bash
# Dimension is auto-detected from model
# Check which model you're using:
curl -X POST http://localhost:8073/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"input": "test", "model": "jina-embeddings-v3"}'

# Response shows: "dense_dimension": 1024
```

### Slow Performance

Possible causes:
1. Network latency to provider API
2. Large batch size (try smaller batches)
3. Cache disabled (check ENABLE_CACHING=True)
4. Provider rate limiting

Solutions:
- Use batch mode (32 texts per request optimal)
- Try different provider (Jina is fastest)
- Enable caching for repeated texts

---

## 📈 Performance Comparison (v1.0.0 vs Previous)

| Feature | v3.0.0 (Local BGE-M3) | v3.0.1 (Nebius only) | v1.0.0 (Multi-provider) |
|---------|----------------------|----------------------|------------------------|
| **Providers** | None (local CPU) | Nebius AI only | Jina/Nebius/SambaNova |
| **Speed** | ~900ms/chunk | ~125ms/chunk | **50-150ms/chunk** (Jina) |
| **Dimensions** | 1024 (fixed) | 4096 (fixed) | **1024/2048/3584/4096** (auto-detected) |
| **Cost** | $0 (slow) | ~$0.002/doc | **$0 (SambaNova) - $0.002/doc** |
| **Vectors** | Dense + Sparse | Dense only | Dense only |
| **Model Selection** | None (fixed model) | Limited (4 models) | **Flexible (7+ models)** |
| **FREE Option** | Yes (slow CPU) | No | **Yes (SambaNova)** |

**Improvement**: 10-20x faster with multi-provider support and FREE option

---

## 📚 Files

```
v1.0.0/
├── README.md                    # This file
├── config.py                    # Configuration (API keys, models)
├── models.py                    # Pydantic models
├── embeddings_api.py            # FastAPI application (v1 endpoints)
├── model_registry.py            # Model definitions and dimensions
└── test_embeddings_api.py       # Test suite
```

---

## 📄 License

Internal use only - CrawlEnginePro / MindMate247

## 🤝 Support

For issues or questions:
- Check health endpoint: `curl http://localhost:8073/health`
- Verify API keys are configured in `.env`
- Test with simple text first before batch processing
- Try different providers if one is slow/unavailable

---

**Version**: v1.0.0
**Date**: October 18, 2025
**Status**: Production-ready
**Changes**: Multi-provider support (Jina/Nebius/SambaNova), auto-dimension detection, FREE option
