# 🤖 Models Configuration - CrawlEnginePro

**Central Model Registry**: `/code/shared/model_registry.py`

---

## 🎯 **ACTIVE CONFIGURATION**

**Current Preset**: `SAMBANOVA_FAST` (Line 198 in model_registry.py)

### **Models Currently In Use:**

| Task | Model | Provider | Size | Cost |
|------|-------|----------|------|------|
| **Intent Detection** | Qwen3-32B | SambaNova | 32B | FREE |
| **Answer (Simple)** | Meta-Llama-3.1-8B-Instruct | SambaNova | 8B | FREE |
| **Answer (Complex)** | Meta-Llama-3.3-70B-Instruct | SambaNova | 70B | FREE |
| **Compression** | Qwen3-32B | SambaNova | 32B | FREE |
| **Metadata Extraction** | Meta-Llama-3.3-70B-Instruct | SambaNova | 70B | FREE |
| **Embeddings** | jina-embeddings-v3 | Jina AI | 1024-dim | $0.02/M tokens |
| **Reranking** | jina-reranker-v2-base-multilingual | Jina AI | N/A | API-based |

---

## 📊 **ALL AVAILABLE LLM MODELS**

### **🚀 Nebius AI Studio (Paid)**

#### Fast Models (Best for Simple Queries)
| Model | Size | Context | Speed | Use Cases | JSON | Cost |
|-------|------|---------|-------|-----------|------|------|
| `google/gemma-2-2b-it` | 2B | 8K | Fastest | Yes/No, Lists | ❌ | Ultra Low |
| `google/gemma-2-9b-it-fast` | 9B | 8K | Very Fast | Simple lookup | ❌ | Low |
| `meta-llama/Meta-Llama-3.1-8B-Instruct-fast` | 8B | 128K | Very Fast | Factual retrieval | ✅ | Low |

#### Medium Models (Balanced)
| Model | Size | Context | Speed | Use Cases | JSON | Reasoning |
|-------|------|---------|-------|-----------|------|-----------|
| `mistralai/Devstral-Small-2505` | ~22B | 128K | Fast | Code generation | ✅ | ❌ |
| `Qwen/Qwen3-32B-fast` | 32B | 41K | Medium | Cross-reference, Synthesis | ✅ | ✅ (has <think>) |
| `Qwen/QwQ-32B-fast` | 32B | 32K | Medium | Math reasoning | ✅ | ✅ (has <think>) |

#### Large Models (Best Quality)
| Model | Size | Context | Speed | Use Cases | JSON | Reasoning |
|-------|------|---------|-------|-----------|------|-----------|
| `meta-llama/Llama-3.3-70B-Instruct-fast` | 70B | 128K | Slow | Complex reasoning | ❌ | ❌ |
| `Qwen/Qwen2.5-72B-Instruct` | 72B | 128K | Slow | Synthesis | ✅ | ❌ |
| `Qwen/Qwen3-Coder-480B-A35B-Instruct` | 480B | 32K | Very Slow | Code expert | ✅ | ❌ |
| `deepseek-ai/DeepSeek-R1-0528` | ~70B | 64K | Slow | Best reasoning | ❌ | ✅ (has <think>) |

**Pricing**: $0.20 per 1M tokens (input + output)

---

### **⚡ SambaNova AI (FREE Tier)**

#### Reasoning Models (with <think> tags)
| Model | Size | Context | Use Cases | JSON | FREE |
|-------|------|---------|-----------|------|------|
| `DeepSeek-R1-0528` | 671B MoE | 64K | Best reasoning, Scientific research | ✅ | ✅ |
| `DeepSeek-R1-Distill-Llama-70B` | 70B | 64K | Fast reasoning, Aggregation | ✅ | ✅ |
| `DeepSeek-V3.1-Terminus` | 671B MoE | 64K | Advanced reasoning | ✅ | ✅ |
| `Qwen3-32B` | 32B | 32K | Reasoning, Code, Math | ✅ | ✅ |

**⚠️ All reasoning models require cleaning `<think>` tags from output!**

#### Text Generation Models (no <think> tags)
| Model | Size | Context | Use Cases | JSON | FREE |
|-------|------|---------|-----------|------|------|
| `DeepSeek-V3-0324` | 671B MoE | 64K | Best quality writing | ✅ | ✅ |
| `Meta-Llama-3.1-8B-Instruct` | 8B | 128K | Fastest, Simple queries | ✅ | ✅ |
| `Meta-Llama-3.3-70B-Instruct` | 70B | 128K | Complex reasoning | ✅ | ✅ |
| `Llama-3.3-Swallow-70B-Instruct-v0.4` | 70B | 128K | Japanese/Multilingual | ✅ | ✅ |
| `gpt-oss-120b` | 120B | 32K | General purpose | ✅ | ✅ |

**Cost**: FREE tier with unlimited tokens!

---

## 🎨 **EMBEDDING MODELS**

### **Nebius AI Studio**

| Model | Dimensions | Context | Languages | MTEB Score | Use Case | Provider |
|-------|------------|---------|-----------|------------|----------|----------|
| `intfloat/e5-mistral-7b-instruct` | **4096** | 32K | Multilingual | 0.83 | **Best for RAG** | Nebius |
| `BAAI/bge-en-icl` | **4096** | 32K | English | 0.76 | English retrieval | Nebius |
| `BAAI/bge-multilingual-gemma2` | **3584** | 8K | 100+ | 0.78 | Multilingual | Nebius |
| `Qwen/Qwen3-Embedding-8B` | **4096** | 32K | Multilingual | 0.79 | High performance | Nebius |

**Cost**: Paid (exact pricing TBD)

### **SambaNova AI (FREE)**

| Model | Dimensions | Context | Languages | MTEB Score | Use Case | Cost |
|-------|------------|---------|-----------|------------|----------|------|
| `E5-Mistral-7B-Instruct` | **4096** | 4K | Multilingual | 0.83 | Same as Nebius E5 | **FREE** |

**Cost**: $0.13/M input tokens, $0.00/M output tokens (FREE tier unlimited)

### **Jina AI**

| Model | Dimensions | Context | Languages | MTEB Score | Use Case | Free Tier |
|-------|------------|---------|-----------|------------|----------|-----------|
| `jina-embeddings-v3` | **1024** | 8K | 89 | 0.80 | **4x faster search** | 10M tokens |
| `jina-embeddings-v4` | **2048** | 8K | 89 + images | 0.82 | Multimodal | Paid only |

**Cost**: $0.02/M tokens (free tier: 10M tokens, 500 RPM)

---

## 🎯 **RERANKING MODELS**

### **BGE Reranker (Local)**

| Model | Type | Use Case | Speed |
|-------|------|----------|-------|
| `BAAI/bge-reranker-v2-m3` | Local CPU/GPU | Best for local deployment | ~2,700ms for 20 chunks |

### **Jina AI Reranker (API)**

| Model | Languages | Speed | API |
|-------|-----------|-------|-----|
| `jina-reranker-v2-base-multilingual` | 90 | ~780ms for 20 chunks (3.5x faster) | Yes |

---

## 🔄 **SWITCHING BETWEEN PRESETS**

**Location**: `/code/shared/model_registry.py` (Line 198)

Change ONLY this line to switch all models:

```python
# Current (SambaNova Fast & FREE)
ACTIVE_PRESET = ProviderPreset.SAMBANOVA_FAST

# Available presets:
# ACTIVE_PRESET = ProviderPreset.NEBIUS_FAST        # Nebius with Qwen 32B + Llama 8B
# ACTIVE_PRESET = ProviderPreset.SAMBANOVA_BEST     # SambaNova with DeepSeek R1 671B (best quality)
# ACTIVE_PRESET = ProviderPreset.NEBIUS_BALANCED    # Nebius with Llama 70B for complex queries
```

### **Available Presets:**

#### 1. **SAMBANOVA_FAST** (Current) ⭐
- Intent: Qwen3-32B (SambaNova)
- Answer Simple: Llama 8B (SambaNova)
- Answer Complex: Llama 70B (SambaNova)
- Metadata: Qwen3-32B (SambaNova)
- Embeddings: Jina V3 (1024-dim)
- **Cost**: FREE!

#### 2. **SAMBANOVA_BEST**
- Intent: DeepSeek R1 671B (SambaNova)
- Answer Simple: Llama 70B (SambaNova)
- Answer Complex: DeepSeek R1 671B (SambaNova)
- Metadata: Qwen3-32B (SambaNova)
- Embeddings: Jina V3 (1024-dim)
- **Cost**: FREE (but slower)

#### 3. **NEBIUS_FAST**
- Intent: Qwen 32B Fast (Nebius)
- Answer Simple: Llama 8B Fast (Nebius)
- Answer Complex: Qwen 32B Fast (Nebius)
- Metadata: Qwen 32B Fast (Nebius)
- Embeddings: Jina V3 (1024-dim)
- **Cost**: $0.20/M tokens

#### 4. **NEBIUS_BALANCED**
- Intent: Qwen 32B Fast (Nebius)
- Answer Simple: Llama 8B Fast (Nebius)
- Answer Complex: Llama 70B Fast (Nebius)
- Metadata: Qwen 32B Fast (Nebius)
- Embeddings: E5-Mistral (4096-dim)
- **Cost**: $0.20/M tokens (better quality)

---

## 📝 **MODEL CAPABILITIES**

### **Context Windows**

| Model | Context | Best For |
|-------|---------|----------|
| Llama 3.1 8B/70B | 128K | Long documents |
| Qwen 32B | 41K | Medium documents |
| DeepSeek R1/V3 | 64K | Long reasoning chains |
| Gemma 2B/9B | 8K | Short queries |

### **Special Features**

| Model | JSON Mode | Reasoning Tags | Speed Tier |
|-------|-----------|----------------|------------|
| Llama 8B Fast | ✅ | ❌ | Very Fast |
| Qwen 32B Fast | ✅ | ✅ (<think>) | Medium |
| Llama 70B Fast | ❌ | ❌ | Slow |
| DeepSeek R1 | ✅ | ✅ (<think>) | Slow |

---

## ⚙️ **CURRENT INGESTION PIPELINE**

Based on benchmark results, here's what's being used:

### **Metadata Extraction** (6.43s / 41.8% of pipeline)
- **Model**: Llama 70B (SambaNova FREE)
- **Fields**: 7 (keywords, topics, questions, summary, semantic_keywords, entity_relationships, attributes)
- **Provider**: SambaNova AI
- **Cost**: FREE

### **Embeddings Generation** (2.56s / 16.6% of pipeline)
- **Model**: E5-Mistral-7B-Instruct (SambaNova FREE)
- **Dimensions**: 4096
- **Provider**: SambaNova AI
- **Cost**: FREE

### **Storage** (6.37s / 41.4% of pipeline)
- **Database**: Milvus
- **Schema**: 17 fields (9 core + 1 vector + 7 metadata)
- **Dimension**: Auto-detected (4096)

---

## 🎛️ **OPTIMIZATION RECOMMENDATIONS**

### **For Speed**:
1. Switch to `NEBIUS_FAST` preset
2. Use `jina-embeddings-v3` (1024-dim instead of 4096)
3. Set `generate_metadata: false` to skip metadata extraction
4. Increase `max_chunk_size` to 1500

### **For Quality**:
1. Switch to `SAMBANOVA_BEST` preset (DeepSeek R1 671B)
2. Use `E5-Mistral` embeddings (4096-dim)
3. Keep all 7 metadata fields
4. Use smaller `max_chunk_size` (800)

### **For Cost**:
1. Stay with `SAMBANOVA_FAST` (current) ✅
2. Everything is FREE!

---

## 📊 **COST COMPARISON**

| Configuration | Cost per 1M tokens | Speed | Quality |
|---------------|-------------------|-------|---------|
| **SAMBANOVA_FAST** (current) | **FREE** | Fast | Good |
| **SAMBANOVA_BEST** | **FREE** | Slow | Best |
| NEBIUS_FAST | $0.20 | Very Fast | Good |
| NEBIUS_BALANCED | $0.20 | Medium | Better |

**Current Usage (per your benchmark)**:
- 18 chunks, 2,894 estimated tokens
- With SAMBANOVA_FAST: **$0.00** (FREE!)
- With NEBIUS: ~$0.0006 (negligible)

---

## 🔍 **HOW TO CHANGE MODELS**

### **1. Change Entire Preset** (Easiest)
Edit `/code/shared/model_registry.py` line 198:
```python
ACTIVE_PRESET = ProviderPreset.SAMBANOVA_BEST  # Switch to best quality
```

### **2. Override Individual Models**
Edit your `.env` file:
```bash
# Override just the metadata model
LLM_MODEL_METADATA=DeepSeek-R1-0528

# Override embedding model
EMBEDDING_MODEL=E5-Mistral-7B-Instruct
```

### **3. Per-Request Override**
In your API request:
```json
{
  "text": "...",
  "embedding_model": "jina-embeddings-v3",
  "generate_metadata": true
}
```

---

## 📚 **DOCUMENTATION REFERENCES**

- **Model Registry**: `/code/shared/model_registry.py`
- **Metadata Config**: `/code/Ingestion/services/metadata/v1.0.0/config.py`
- **Embeddings Config**: `/code/Ingestion/services/embeddings/v1.0.0/config.py`
- **Port Allocation**: `/code/PORT_ALLOCATION.md`
- **Ingestion API**: `/code/Ingestion/v1.0.0/README.md`

---

**Generated**: 2025-10-20
**Active Preset**: SAMBANOVA_FAST (FREE tier)
**Status**: All services operational ✅
