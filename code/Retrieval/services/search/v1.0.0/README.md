# Search Service v1.0.0

Dense vector search with metadata boosting using **ALL 4 metadata fields**.

Part of **Retrieval Pipeline** - Stage 1: Search

## Features

- ✅ Dense vector search (multi-dimension support: 1024/2048/3584/4096-dim)
- ✅ Metadata boosting using keywords, topics, questions, summary (4 fields)
- ✅ Configurable boost weights
- ✅ Collection-based multi-tenancy
- ✅ Optional metadata filtering
- ✅ **Speed-optimized defaults**: top_k=10 (changed from 20)
- ✅ localhost-only security

## Architecture

```
User Query
    ↓
Search Service (8071) ← YOU ARE HERE
    ↓
[1] Embeddings Service (8063) → Get query vector (1024/2048/3584/4096-dim)
    ↓
[2] Milvus Storage (8064) → Dense vector search
    ↓
[3] Metadata Boost → Apply ALL 4 field boosts
    ↓
Top-K Results (sorted by boosted score)
```

## Metadata Boosting Strategy

### 1. Keywords Boost (+0.10 per match, max 3)
Exact keyword matching between query and chunk keywords.

**Example:**
- Query: "What damage did vajra cause?"
- Chunk keywords: "Hanuman, vajra, jaw, damage"
- Matches: ["vajra", "damage"]
- Boost: 0.10 × 2 = **+0.20**

### 2. Topics Boost (+0.05 per match)
Category relevance - does query relate to chunk topics?

**Example:**
- Query: "What damage did vajra cause to Hanuman?"
- Chunk topics: "Hindu mythology, Hanuman origin"
- Matches: ["Hindu mythology"]
- Boost: 0.05 × 1 = **+0.05**

### 3. Questions Boost (+0.08 if similar)
Does the chunk answer a similar question?

**Example:**
- Query: "What damage did vajra cause?"
- Chunk question: "What is the origin of Hanuman's name?"
- Similarity: 0.65 (high)
- Boost: **+0.08**

### 4. Summary Boost (+0.07 if high coverage)
Does the summary cover query keywords?

**Example:**
- Query keywords: ["vajra", "damage", "hanuman"]
- Summary: "Indra's vajra struck Hanuman's jaw"
- Coverage: 2/3 = 0.67 (high)
- Boost: **+0.07**

**Total Boost:** 0.20 + 0.05 + 0.08 + 0.07 = **+0.40** (capped at 0.30)

## API Endpoints

### POST /v1/search
Main search endpoint with metadata boosting.

**Default Parameters:**
- `top_k`: **10** (speed-optimized, changed from 20 in v1.0.0)
- `use_metadata_boost`: `true` (always enabled by default)

**Request:**
```json
{
  "query_text": "What damage did vajra cause to Hanuman?",
  "collection": "test_jaishreeram_v1",
  "tenant_id": "test_tenant",
  "top_k": 10,
  "use_metadata_boost": true,
  "boost_weights": {
    "keywords": 0.10,
    "topics": 0.05,
    "questions": 0.08,
    "summary": 0.07
  }
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "chunk_id": "chunk_6",
      "text": "The Name Hanuman: Indra struck Hanuman with his vajra...",
      "score": 0.92,
      "vector_score": 0.75,
      "metadata_boost": 0.17,
      "metadata_matches": {
        "keywords_matched": ["Hanuman", "vajra"],
        "topics_matched": ["Hindu mythology"],
        "question_similarity": 0.65,
        "summary_coverage": 0.67
      },
      "document_id": "doc_jaishreeram",
      "chunk_index": 6,
      "keywords": "Hanuman, vajra, jaw, damage",
      "topics": "Hindu mythology, Hanuman origin",
      "questions": "What is the origin of Hanuman's name?",
      "summary": "Indra's vajra struck Hanuman's jaw"
    }
  ],
  "total_found": 10,
  "collection": "test_jaishreeram_v1",
  "search_time_ms": 45.2,
  "metadata_boost_applied": true,
  "api_version": "1.0.0"
}
```

### POST /v1/search/vector-only
Pure vector search without metadata boosting (for comparison).

### GET /health
Health check with dependency status.

### GET /version
Service version and endpoint list.

## Installation

### Local Development
```bash
cd /Users/rakesh/Desktop/CrawlEnginePro/nebius_hosting/ai_studio/hosting/services/search/v1.0.0

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env

# Run service
python search_api.py
```

### Server Deployment
```bash
# On server (as reku631)
cd /home/reku631/services/search/v1.0.0

# Create virtual environment
python3 -m venv /home/reku631/venvs/search_v1
source /home/reku631/venvs/search_v1/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create systemd service
sudo nano /etc/systemd/system/search.service
```

**systemd service file:**
```ini
[Unit]
Description=Search Service v1.0.0
After=network.target embeddings.service milvus-storage.service

[Service]
Type=simple
User=reku631
WorkingDirectory=/home/reku631/services/search/v1.0.0
ExecStart=/home/reku631/venvs/search_v1/bin/python search_api.py
Restart=always
RestartSec=10
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable search.service
sudo systemctl start search.service
sudo systemctl status search.service

# View logs
journalctl -u search.service -f
```

## Testing

### Test with curl
```bash
# Health check
curl http://localhost:8017/health

# Search test
curl -X POST http://localhost:8017/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "What damage did vajra cause to Hanuman?",
    "collection": "test_jaishreeram_v1",
    "top_k": 5
  }'
```

### Test with Python
```python
import httpx

async def test_search():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8017/v1/search",
            json={
                "query_text": "What damage did vajra cause to Hanuman?",
                "collection": "test_jaishreeram_v1",
                "top_k": 10,
                "use_metadata_boost": True
            }
        )
        data = response.json()

        print(f"Found {data['total_found']} results")
        print(f"Search time: {data['search_time_ms']:.2f}ms")

        for i, result in enumerate(data['results'][:3], 1):
            print(f"\n{i}. Score: {result['score']:.3f} (vector: {result['vector_score']:.3f}, boost: {result['metadata_boost']:.3f})")
            print(f"   Text: {result['text'][:100]}...")
            print(f"   Keywords matched: {result['metadata_matches']['keywords_matched']}")
```

## Configuration

Adjust boost weights in `.env` or via API request:

```bash
# Increase keyword boost for exact matching
BOOST_KEYWORDS=0.15

# Decrease topic boost if less important
BOOST_TOPICS=0.03

# Increase question boost for FAQ-style queries
BOOST_QUESTIONS=0.12
```

## Performance

**Target Latency:** <100ms (99% SLA)

Typical breakdown:
- Embedding: 15-20ms
- Vector search: 10-15ms
- Metadata boost: 5-10ms
- **Total:** 30-45ms

## Dependencies

- **Embeddings Service (8063):** For query embedding
- **Milvus Storage (8064):** For vector search

## Port

**8071** (configured in `config.py` - Retrieval pipeline internal service)

## Security

- Localhost-only access (172.*, 10.*, 192.168.* allowed)
- No external API keys required
- All data stays local

## Next Steps

1. Test with both collections (test_jaishreeram_v1, test_comprehensivetestdocument_v1)
2. Tune boost weights based on results
3. Deploy to server
4. Integrate with HyDE and Reranking services

## Version History

- **v1.0.0** (2025-10-18): Production release
  - Dense vector search with metadata boosting (4 fields)
  - Multi-dimension embedding support (1024/2048/3584/4096)
  - **Parameter change**: Default top_k reduced from 20 → **10** (speed optimization)
  - Collection-based multi-tenancy
  - Configurable boost weights
  - localhost-only security

---

**Version:** 1.0.0
**Date:** 2025-10-18
**Port:** 8071
**Status:** Production-ready
