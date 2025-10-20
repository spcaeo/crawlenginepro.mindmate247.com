# Shared Utilities for PipeLineServices

**Central registry for models, health checks, and common utilities**

## Contents
1. [Model Registry](#model-registry) - AI model management
2. [Health Check Utilities](#health-check-utilities) - Standardized health checks

## Problem Solved

Before: Model names scattered across 10+ config files in different services. Updating models required editing multiple files.

After: All models managed in one place. Update once, effect everywhere.

## Architecture

```
PipeLineServices/
├── .env                          # Environment variables (model overrides)
├── shared/
│   ├── __init__.py              # Package exports
│   ├── model_registry.py        # ⭐ CENTRAL REGISTRY ⭐
│   └── README.md                # This file
├── Ingestion/
│   └── services/
│       ├── llm_gateway/         # Uses: LLMModels enum
│       ├── metadata/            # Uses: get_llm_for_task("metadata_generation")
│       └── embeddings/          # Uses: get_embedding_model()
└── Retrieval/
    └── services/
        ├── intent/              # Uses: get_llm_for_task("intent_detection")
        ├── answer_generation/   # Uses: get_llm_for_task("answer_generation", intent=X)
        ├── compression/         # Uses: get_llm_for_task("compression")
        └── reranking/           # Uses: get_reranking_model()
```

## Usage Examples

### 1. Get Model for Specific Task

```python
from shared import get_llm_for_task

# Intent detection
model = get_llm_for_task("intent_detection")
# Returns: "Qwen/Qwen3-32B-fast"

# Answer generation (dynamic based on intent & complexity)
model = get_llm_for_task(
    task="answer_generation",
    intent="cross_reference",  # Complex reasoning needed
    complexity="complex"
)
# Returns: "Qwen/Qwen3-32B-fast" (uses INTENT_TO_MODEL_COMPLEX mapping)

model = get_llm_for_task(
    task="answer_generation",
    intent="simple_lookup",    # Simple fact lookup
    complexity="simple"
)
# Returns: "meta-llama/Meta-Llama-3.1-8B-Instruct-fast" (faster model)
```

### 2. Use Model Enums Directly

```python
from shared import LLMModels, EmbeddingModels

# Type-safe model selection
model_id = LLMModels.QWEN_32B_FAST.value
# Returns: "Qwen/Qwen3-32B-fast"

embedding_model = EmbeddingModels.NEBIUS_E5_MULTILINGUAL.value
# Returns: "intfloat/multilingual-e5-large-instruct"
```

### 3. Check Model Capabilities

```python
from shared import get_model_info, supports_reasoning

# Get model info
info = get_model_info("Qwen/Qwen3-32B-fast")
print(info)
# {
#   "params": "32B",
#   "context_window": 41000,
#   "speed": "medium",
#   "use_cases": ["cross_reference", "synthesis", ...],
#   "supports_json": True,
#   "supports_reasoning": True,  # Has <think> tags
#   "cost_tier": "medium"
# }

# Check if model needs <think> tag cleaning
if supports_reasoning(model):
    # Clean <think> tags from response
    answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL)
```

### 4. Get Default Models

```python
from shared import (
    DEFAULT_LLM_INTENT,
    DEFAULT_LLM_ANSWER_SIMPLE,
    DEFAULT_LLM_ANSWER_COMPLEX
)

# These are loaded from .env or use defaults
print(DEFAULT_LLM_INTENT)          # Qwen/Qwen3-32B-fast
print(DEFAULT_LLM_ANSWER_SIMPLE)   # meta-llama/Meta-Llama-3.1-8B-Instruct-fast
print(DEFAULT_LLM_ANSWER_COMPLEX)  # Qwen/Qwen3-32B-fast
```

## Model Categories

### LLM Models (Text Generation)

| Model | Params | Context | Speed | Best For |
|-------|--------|---------|-------|----------|
| `LLAMA_8B_FAST` | 8B | 128K | ⚡⚡⚡ | Simple queries, fast retrieval |
| `QWEN_32B_FAST` | 32B | 41K | ⚡⚡ | Complex reasoning, cross-reference |
| `LLAMA_70B_FAST` | 70B | 128K | ⚡ | Multi-step analysis |
| `DEEPSEEK_R1` | ~70B | 64K | ⚡ | Mathematical reasoning |

### Embedding Models

| Model | Dimensions | Languages | Best For |
|-------|------------|-----------|----------|
| `NEBIUS_E5_MULTILINGUAL` | 1024 | 77 | Multilingual vector search |

### Reranking Models

| Model | Type | Languages | Best For |
|-------|------|-----------|----------|
| `JINA_RERANKER_V2_BASE` | Cross-encoder | 90 | Semantic relevance scoring |

## Dynamic Model Selection

The registry supports **intent-based dynamic model selection**:

```python
# Automatically selects best model based on intent & complexity
model = get_llm_for_task(
    task="answer_generation",
    intent="cross_reference",      # Needs strong reasoning
    complexity="complex"
)
# Uses: Qwen-32B-fast (strong reasoning)

model = get_llm_for_task(
    task="answer_generation",
    intent="simple_lookup",        # Just fact lookup
    complexity="simple"
)
# Uses: Llama-8B-fast (faster, sufficient)
```

### Intent-to-Model Mapping

**Simple/Moderate Complexity:**
- Core retrieval intents → Llama-8B-fast (fast)
- Advanced logic intents → Qwen-32B-fast (reasoning)

**Complex Complexity:**
- Most intents → Qwen-32B-fast (better quality)
- Except trivial ones → Llama-8B-fast

## Configuration

### Override Models via .env

```bash
# Use different models for specific tasks
LLM_MODEL_INTENT=Qwen/Qwen3-32B-fast
LLM_MODEL_ANSWER_SIMPLE=meta-llama/Meta-Llama-3.1-8B-Instruct-fast
LLM_MODEL_ANSWER_COMPLEX=meta-llama/Llama-3.3-70B-Instruct-fast
LLM_MODEL_COMPRESSION=Qwen/Qwen3-32B-fast
LLM_MODEL_METADATA=Qwen/Qwen3-32B-fast

EMBEDDING_MODEL=intfloat/multilingual-e5-large-instruct
RERANKING_MODEL=jina-reranker-v2-base-multilingual
```

### Add New Models

1. Add to enum in `model_registry.py`:
```python
class LLMModels(str, Enum):
    NEW_MODEL = "provider/new-model-name"
```

2. Add capabilities:
```python
LLM_CAPABILITIES = {
    LLMModels.NEW_MODEL: {
        "params": "13B",
        "context_window": 100000,
        "speed": "fast",
        "use_cases": ["factual_retrieval"],
        "supports_json": True,
        "supports_reasoning": False,
        "cost_tier": "low"
    }
}
```

3. Update intent mappings if needed:
```python
INTENT_TO_MODEL_SIMPLE = {
    "factual_retrieval": LLMModels.NEW_MODEL,
    # ...
}
```

## Migration Guide

### Before (scattered):
```python
# In answer_generation/config.py
DEFAULT_LLM_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-fast"

# In intent/config.py
INTENT_DETECTION_MODEL = "Qwen/Qwen3-32B-fast"

# In metadata/config.py
METADATA_LLM_MODEL = "Qwen/Qwen3-32B-fast"
```

### After (centralized):
```python
# In ALL services
from shared import get_llm_for_task

# Service-specific usage
model = get_llm_for_task("answer_generation", intent="cross_reference", complexity="complex")
model = get_llm_for_task("intent_detection")
model = get_llm_for_task("metadata_generation")
```

## Benefits

✅ **Single Source of Truth** - All models in one file
✅ **Type Safety** - Enums prevent typos
✅ **Easy Updates** - Change once, effect everywhere
✅ **Dynamic Selection** - Auto-select best model for task
✅ **Capability Tracking** - Know what each model can do
✅ **Cost Estimation** - Track token usage and costs
✅ **Documentation** - Clear use cases for each model

## Cost Tracking

```python
from shared import estimate_cost

# Calculate request cost
cost = estimate_cost(input_tokens=1000, output_tokens=500)
# Returns: 0.0003 USD ($0.20 per 1M tokens)
```

## Future Enhancements

- [ ] Add model performance metrics (speed, accuracy)
- [ ] Add model health monitoring
- [ ] Add automatic fallback on model failure
- [ ] Add A/B testing support
- [ ] Add cost optimization recommendations

## Support

For issues or questions about the central registry:
1. Check this README
2. Review `model_registry.py` comments
3. Check `.env` configuration

When Nebius adds/deprecates models, just update `model_registry.py` once!

---

# Health Check Utilities

**Standardized health check helpers for consistent service monitoring**

## Problem Solved

Before: Each service implemented health checks differently with varying timeouts, no code reuse, and inconsistent behavior.

After: Shared utilities provide consistent health checks, standardized timeouts (2s), and reusable patterns.

## Quick Start

```python
from shared import check_service_health, STANDARD_HEALTH_TIMEOUT

# Check a single service
result = await check_service_health(
    http_client=http_client,
    service_url="http://localhost:8062/health",
    config=HealthCheckConfig(timeout=STANDARD_HEALTH_TIMEOUT)
)

# Result: {"status": "healthy", "version": "3.0.0", "response_time_ms": 45.2}
```

## Core Functions

### 1. Check Single Service

```python
from shared import check_service_health, HealthCheckConfig

result = await check_service_health(
    http_client=http_client,
    service_url="http://localhost:8063/health",
    config=HealthCheckConfig(
        timeout=2.0,
        include_version=True,
        include_response_time=True
    )
)

# Returns:
# {
#     "status": "healthy" | "timeout" | "unreachable" | "unhealthy",
#     "version": "3.0.2",
#     "response_time_ms": 125.5,
#     "error": "..."  # Only if failed
# }
```

### 2. Check Multiple Services in Parallel

```python
from shared import check_multiple_services

services = {
    "chunking": "http://localhost:8061/health",
    "metadata": "http://localhost:8062/health",
    "embeddings": "http://localhost:8063/health"
}

results = await check_multiple_services(
    http_client=http_client,
    services=services,
    config=HealthCheckConfig(timeout=2.0)
)

# Returns:
# {
#     "chunking": {"status": "healthy", "version": "5.0.0", ...},
#     "metadata": {"status": "healthy", "version": "3.0.0", ...},
#     "embeddings": {"status": "degraded", "version": "3.0.2", ...}
# }
```

### 3. Aggregate Health Status

```python
from shared import aggregate_health_status

# After checking multiple services
overall_status = aggregate_health_status(results)

# Returns: "healthy" | "degraded" | "unhealthy"
# Logic:
#   - "healthy": All services healthy
#   - "degraded": Some services down
#   - "unhealthy": All services down
```

### 4. Create Health Summary

```python
from shared import create_health_summary

summary = create_health_summary(results)

# Returns:
# {
#     "total_services": 5,
#     "healthy": 4,
#     "unhealthy": 1,
#     "status_breakdown": {
#         "healthy": 4,
#         "timeout": 1
#     }
# }
```

### 5. Test External API Connectivity

```python
from shared import test_api_connectivity

# Test if external API is reachable
connected = await test_api_connectivity(
    http_client=http_client,
    api_url="https://api.studio.nebius.ai/v1/models",
    api_key=NEBIUS_API_KEY,
    timeout=2.0
)

# Returns: True if API returns 2xx, False otherwise
```

### 6. Add Cache Stats to Health

```python
from shared import add_cache_stats_to_health

health_response = {
    "status": "healthy",
    "version": "1.0.0"
}

cache_stats = embeddings_cache.stats()

# Add cache info to health response
health = add_cache_stats_to_health(health_response, cache_stats)

# Now includes:
# {
#     "status": "healthy",
#     "version": "1.0.0",
#     "cache": {
#         "enabled": True,
#         "entries": 200,
#         "max_size": 10000,
#         "hit_rate": 92.3,
#         "total_hits": 1850,
#         "total_misses": 150
#     }
# }
```

## Standard Timeout

All health checks use a **standardized 2-second timeout**:

```python
from shared import STANDARD_HEALTH_TIMEOUT, STANDARD_CONFIG

# Constant: 2.0 seconds
timeout = STANDARD_HEALTH_TIMEOUT

# Pre-configured standard config
config = STANDARD_CONFIG
```

**Why 2 seconds?**
- Fast enough for responsive health checks
- Long enough to handle network variance
- Prevents cascading timeouts
- Consistent across all services

## Complete Example

```python
from fastapi import FastAPI
from shared import (
    check_multiple_services,
    aggregate_health_status,
    create_health_summary,
    STANDARD_CONFIG
)

@app.get("/health")
async def health_check():
    """Aggregated health check using shared utilities"""

    # Check all dependencies in parallel
    services = {
        "chunking": "http://localhost:8061/health",
        "metadata": "http://localhost:8062/health",
        "embeddings": "http://localhost:8063/health",
        "storage": "http://localhost:8064/health"
    }

    results = await check_multiple_services(
        http_client=http_client,
        services=services,
        config=STANDARD_CONFIG
    )

    # Aggregate status
    overall_status = aggregate_health_status(results)
    summary = create_health_summary(results)

    return {
        "status": overall_status,
        "version": API_VERSION,
        "service": SERVICE_NAME,
        "dependencies": results,
        "summary": summary
    }
```

## Benefits

✅ **Consistent Timeouts** - All services use 2s
✅ **Code Reuse** - Write once, use everywhere
✅ **Parallel Checks** - Check multiple services simultaneously
✅ **Status Aggregation** - Smart overall health calculation
✅ **Type Safety** - Dataclass configuration
✅ **Easy Testing** - Standardized responses
✅ **Cache Integration** - Easy cache stats inclusion

## Migration from Manual Health Checks

### Before (manual):
```python
@app.get("/health")
async def health():
    try:
        response = await http_client.get(
            "http://localhost:8062/health",
            timeout=5.0  # Inconsistent timeout
        )
        if response.status_code == 200:
            return {"status": "healthy"}
    except Exception:
        return {"status": "unhealthy"}
```

### After (shared utilities):
```python
from shared import check_service_health, STANDARD_CONFIG

@app.get("/health")
async def health():
    result = await check_service_health(
        http_client=http_client,
        service_url="http://localhost:8062/health",
        config=STANDARD_CONFIG
    )
    return result
```

## Testing Health Checks

Use the provided test script:

```bash
# From PipeLineServices root
./check_health_all.sh

# Output shows all services with:
# - Version
# - API connectivity status
# - Cache statistics
# - Overall system health
```

## Configuration

### HealthCheckConfig Options

```python
from shared import HealthCheckConfig

config = HealthCheckConfig(
    timeout=2.0,              # Request timeout in seconds
    include_version=True,      # Include service version
    include_response_time=True # Include response time
)
```

## Files

- `shared/health_utils.py` - Core health check utilities
- `shared/__init__.py` - Exports health utilities
- `check_health_all.sh` - Test script for all services

## See Also

- [HEALTH_CHECK_FIXES.md](../HEALTH_CHECK_FIXES.md) - Complete changelog
- [Model Registry](#model-registry) - AI model management
