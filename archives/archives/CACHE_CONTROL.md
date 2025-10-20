# Cache Control - PipeLineServices

## Overview

This document explains how to enable/disable caching across all Retrieval services for performance testing and optimization.

## Complete Service Caching Status

### ✅ Services WITH Caching (2)

#### 1. LLM Gateway Service (Port 8065) - INGESTION
- **Location**: `Ingestion/services/llm_gateway/v1.0.0/`
- **Cache Type**: In-memory cache (not Redis)
- **What it caches**: LLM responses (chat completions)
- **Purpose**: Avoid redundant LLM API calls for identical requests
- **Default TTL**: 7200 seconds (2 hours)
- **Max Size**: 10,000 entries
- **Controlled by**: `ENABLE_CACHE` in `.env` ✅

#### 2. Answer Generation Service (Port 8074) - RETRIEVAL
- **Location**: `Retrieval/services/answer_generation/v1.0.0/`
- **Cache Type**: Redis cache (requires Redis server)
- **What it caches**: Generated answers with citations
- **Purpose**: Avoid regenerating identical answers
- **Default TTL**: 7200 seconds (2 hours)
- **Redis DB**: 3
- **Controlled by**: `ENABLE_CACHE` in `.env` ✅

### ❌ Services WITHOUT Caching (4)

#### 3. Search Service (Port 8071) - RETRIEVAL
- **Location**: `Retrieval/services/search/v1.0.0/`
- **Cache Status**: **NO CACHE IMPLEMENTATION**
- **Note**: Config has `ENABLE_CACHE` variable but code doesn't use it
- **Reason**: Search is fast (~2s) and results vary by query

#### 4. Reranking Service (Port 8072) - RETRIEVAL
- **Location**: `Retrieval/services/reranking/v1.0.0/`
- **Cache Status**: **NO CACHE**
- **Reason**: Reranking is deterministic but input varies per query

#### 5. Compression Service (Port 8073) - RETRIEVAL
- **Location**: `Retrieval/services/compression/v1.0.0/`
- **Cache Status**: **NO CACHE**
- **Reason**: Compression is context-dependent and varies per query

#### 6. Intent & Prompt Adaptation Service (Port 8075) - RETRIEVAL
- **Location**: `Retrieval/services/intent/v1.0.0/`
- **Cache Status**: **NO CACHE** (intentionally disabled in config)
- **Reason**: Intent detection is fast (~3-4s), caching not beneficial

## Quick Start: Disable All Caching

### Step 1: Edit `.env` File

Open `/PipeLineServies/.env` and set:

```bash
ENABLE_CACHE=false
```

### Step 2: Restart All Services

After changing the `.env`, you must **restart** all running services:

```bash
# Kill all services
lsof -ti:8065,8074 | xargs kill -9

# Restart LLM Gateway
cd Ingestion/services/llm_gateway/v1.0.0
python llm_gateway.py > /tmp/llm_gateway.log 2>&1 &

# Restart Answer Generation
cd Retrieval/services/answer_generation/v1.0.0
python answer_api.py > /tmp/answer.log 2>&1 &
```

### Step 3: Verify Cache is Disabled

Check the logs:

```bash
# LLM Gateway should print:
tail /tmp/llm_gateway.log
# Expected output: "⚠️  LLM Gateway cache DISABLED via ENABLE_CACHE=false"

# Answer Generation should show:
curl -s http://localhost:8074/health | jq .dependencies.cache
# Expected output: false
```

## Re-enabling Cache After Testing

### Step 1: Edit `.env`

```bash
ENABLE_CACHE=true
```

### Step 2: Restart Services (same as above)

```bash
lsof -ti:8065,8074 | xargs kill -9
# Then restart services
```

## Configuration Variables

All cache settings are in `/PipeLineServies/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_CACHE` | `true` | Master switch: `true` or `false` |
| `CACHE_TTL` | `7200` | Cache lifetime in seconds (2 hours) |
| `CACHE_MAX_SIZE` | `10000` | Maximum cached entries (LLM Gateway only) |

## Cache Endpoints

### LLM Gateway (Port 8065)

**Get cache stats:**
```bash
curl http://localhost:8065/cache/stats
```

**Clear cache:**
```bash
curl -X POST http://localhost:8065/cache/clear
```

### Answer Generation (Port 8074)

**Clear cache:**
```bash
curl -X POST http://localhost:8074/v1/cache/clear
```

## Performance Impact

### With Cache Enabled (Default)

**Query 1 (First Time)**:
- Answer Generation: ~5,200ms
- Intent Detection: ~3,800ms
- **Total**: ~9,000ms

**Query 1 (Cached)**:
- Answer Generation: ~50ms (cache hit)
- Intent Detection: ~3,800ms (no cache)
- **Total**: ~3,850ms

**Speedup**: ~2.3x faster

### With Cache Disabled

**All Queries**:
- Answer Generation: ~5,200ms (always fresh)
- Intent Detection: ~3,800ms (no cache anyway)
- **Total**: ~9,000ms

**Benefit**: Accurate performance measurements without cache interference

## Testing Workflow

### 1. Baseline Performance Testing (Cache Off)

```bash
# 1. Disable cache
echo "ENABLE_CACHE=false" >> .env

# 2. Restart services
lsof -ti:8065,8074 | xargs kill -9
# ... restart services

# 3. Run performance tests
curl -X POST http://localhost:8070/v1/query ...

# 4. Record metrics: search_ms, rerank_ms, compress_ms, intent_ms, answer_ms
```

### 2. Optimized Performance Testing (Cache On)

```bash
# 1. Enable cache
echo "ENABLE_CACHE=true" >> .env

# 2. Restart services
lsof -ti:8065,8074 | xargs kill -9
# ... restart services

# 3. Run same performance tests
# First query will populate cache
# Subsequent identical queries will hit cache

# 4. Compare metrics
```

## Architecture Notes

### Why LLM Gateway Uses In-Memory Cache?

- **Speed**: In-memory is ~10x faster than Redis
- **Simplicity**: No external dependency (Redis not required)
- **Shared Service**: LLM Gateway serves both Ingestion and Retrieval pipelines

### Why Answer Generation Uses Redis Cache?

- **Persistence**: Answers survive service restarts
- **Large Data**: Generated answers with citations are larger than LLM requests
- **Future**: Could be shared across multiple Answer service instances

## Troubleshooting

### Cache Not Disabling?

**Check service logs:**
```bash
tail -f /tmp/llm_gateway.log
# Should see: "⚠️  LLM Gateway cache DISABLED via ENABLE_CACHE=false"
```

**If not showing:**
1. Did you restart the service after editing `.env`?
2. Is the `.env` file in the correct location? (`/PipeLineServies/.env`)
3. Check the `parents[5]` path in `cache.py` is correct

### Redis Connection Errors?

**Answer Generation requires Redis when cache is enabled.**

If you see:
```
⚠️  Redis connection failed: Connection refused
   Cache disabled - will generate fresh answers each time
```

**Solution 1**: Install and start Redis
```bash
brew install redis  # macOS
redis-server
```

**Solution 2**: Disable cache
```bash
ENABLE_CACHE=false
```

## Summary

### Services Audited (All Retrieval Pipeline Services)

| Service | Port | Has Cache? | Controlled by ENABLE_CACHE? |
|---------|------|------------|---------------------------|
| Search | 8071 | ❌ No | N/A |
| Reranking | 8072 | ❌ No | N/A |
| Compression | 8073 | ❌ No | N/A |
| Answer Generation | 8074 | ✅ Yes (Redis) | ✅ Yes |
| Intent & Prompt | 8075 | ❌ No | N/A |

### External Dependency (Shared Service)

| Service | Port | Has Cache? | Controlled by ENABLE_CACHE? |
|---------|------|------------|---------------------------|
| LLM Gateway | 8065 | ✅ Yes (In-memory) | ✅ Yes |

### Key Takeaways

- **Master Switch**: `ENABLE_CACHE` in `.env`
- **Affects**: **ONLY 2 services** - LLM Gateway (8065) + Answer Generation (8074)
- **Does NOT Affect**: Search, Reranking, Compression, Intent (these have no cache)
- **Restart Required**: Yes, after changing `.env`
- **Verification**: Check logs and health endpoints

### For Performance Testing

Setting `ENABLE_CACHE=false` will disable caching in:
1. **LLM Gateway** - No cached LLM responses (affects Metadata, Compression, Answer, Intent)
2. **Answer Generation** - No cached answers (affects final response generation)

All other services (Search, Reranking, Compression, Intent) operate without caching regardless of this setting.
