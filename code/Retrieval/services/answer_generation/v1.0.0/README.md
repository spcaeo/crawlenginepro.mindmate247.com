# Answer Generation Service v1.0.0

**LLM-based Answer Generation with Context and Citations**

**Last Updated:** October 9, 2025

## Overview

The Answer Generation Service takes retrieved context chunks and generates comprehensive, accurate answers using LLM (Llama-3.3-70B-Instruct-fast). It includes citation support, metadata enrichment, and caching for better performance.

## Key Features

- 🤖 **LLM-powered Answers** - Uses Llama-3.3-70B-Instruct-fast for high-quality answer generation (no thinking tokens)
- 📚 **Context-aware** - Generates answers based on retrieved context chunks
- 🏷️  **Metadata Enrichment** - Supports topics, keywords, and summary metadata for better context understanding
- 🔗 **Citations** - Automatically extracts and provides source citations
- ⚡ **Redis Caching** - Cache answers for frequently asked questions
- 🎯 **Configurable** - Adjust model, max tokens, temperature, and max context chunks
- 🔒 **Localhost-only Access** - Security middleware blocks external requests

## How It Works

1. **Receive Context**: Get query + retrieved context chunks (from Search/Reranking/Compression)
2. **Build Prompt**: Format context into LLM-friendly prompt with metadata (topics, keywords, summary) and instructions
3. **Generate Answer**: Call LLM Gateway to generate comprehensive answer
4. **Extract Citations**: Parse answer for [Source X] references
5. **Return Result**: Send answer with citations and metadata

## API Endpoints

### POST /v1/generate

Generate answer from retrieved context.

**Request:**
```json
{
  "query": "Which vendors appear in both technology and medical equipment invoices?",
  "context_chunks": [
    {
      "chunk_id": "doc1_chunk5",
      "text": "Vendor Name: TechSupply Solutions\nItems: Dell XPS 15 Laptop",
      "document_id": "invoice_tech_001",
      "chunk_index": 5,
      "score": 0.95,
      "topics": "Technology Purchase, Business Transactions",
      "keywords": "TechSupply Solutions, Dell, laptop",
      "summary": "Technology equipment purchased from TechSupply Solutions"
    },
    {
      "chunk_id": "doc2_chunk3",
      "text": "Vendor Name: MedTech Equipment Supply\nItems: Philips IntelliVue MX40",
      "document_id": "invoice_med_001",
      "topics": "Medical Equipment, Healthcare Supplies",
      "keywords": "MedTech Equipment Supply, Philips, monitor",
      "summary": "Medical equipment purchased from MedTech Equipment Supply"
    }
  ],
  "llm_model": "meta-llama/Llama-3.3-70B-Instruct-fast",
  "max_tokens": 2048,
  "temperature": 0.3,
  "enable_citations": true,
  "use_cache": true
}
```

**Response:**
```json
{
  "success": true,
  "query": "Which vendors appear in both technology and medical equipment invoices?",
  "answer": "Based on the provided context, there are two vendors:\n1. TechSupply Solutions (Technology) [Source 1]\n2. MedTech Equipment Supply (Medical Equipment) [Source 2]\n\nThere is no vendor appearing in both technology and medical equipment invoices.",
  "citations": [
    {
      "source_id": 1,
      "chunk_id": "doc1_chunk5",
      "document_id": "invoice_tech_001",
      "text_snippet": "Vendor Name: TechSupply Solutions..."
    },
    {
      "source_id": 2,
      "chunk_id": "doc2_chunk3",
      "document_id": "invoice_med_001",
      "text_snippet": "Vendor Name: MedTech Equipment Supply..."
    }
  ],
  "num_chunks_used": 2,
  "generation_time_ms": 1250.5,
  "cache_hit": false,
  "llm_model_used": "meta-llama/Llama-3.3-70B-Instruct-fast",
  "tokens_used": 456,
  "api_version": "1.0.0"
}
```

### POST /v1/cache/clear

Clear answer cache.

**Response:**
```json
{
  "success": true,
  "message": "Cleared 25 cache entries",
  "api_version": "1.0.0"
}
```

### GET /health

Health check endpoint.

### GET /version

Version information.

## Configuration

Copy `.env.example` to `.env` and adjust settings:

```bash
# Server
PORT=8019
HOST=0.0.0.0

# LLM Gateway
LLM_GATEWAY_URL=http://localhost:8000

# LLM parameters
DEFAULT_LLM_MODEL=meta-llama/Llama-3.3-70B-Instruct-fast
DEFAULT_MAX_TOKENS=2048
DEFAULT_TEMPERATURE=0.3

# Answer settings
MAX_CONTEXT_CHUNKS=10
ENABLE_CITATIONS=true
ENABLE_STREAMING=true

# Cache
ENABLE_CACHE=true
CACHE_TTL=3600
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=3

# Performance
REQUEST_TIMEOUT=60
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run service
python answer_api.py
```

## Service Dependencies

- **LLM Gateway (port 8000)** - For answer generation
- **Redis (port 6379, DB 3)** - For caching (optional)

## Performance

- **Generation Time**: ~1-2 seconds per answer (2048 tokens max)
- **Cache Hit Time**: <10ms
- **Cache TTL**: 1 hour (configurable)
- **Cost**: ~$0.005-$0.010 per answer (Llama-3.3-70B-Instruct-fast at $0.20/1M tokens)

## New Features (October 9, 2025)

### 🏷️ Metadata Enrichment

The service now accepts and utilizes metadata fields in context chunks:
- **topics**: Content categories (e.g., "Technology Purchase, Medical Equipment")
- **keywords**: Key entities and terms (e.g., "Dell, TechSupply Solutions")
- **summary**: Brief content description

**Why This Matters:**
Metadata helps the LLM understand chunk context without relying solely on compressed text. This is especially critical for:
- Cross-referencing queries (e.g., "which vendors appear in both X and Y?")
- Entity disambiguation (e.g., distinguishing "TechSupply" from "MedTech")
- Comparison queries (e.g., "compare products from different categories")

**Example Context with Metadata:**
```
[Source 1]
Topics: Technology Purchase, Business Transactions
Keywords: TechSupply Solutions, Dell XPS 15, laptop
Summary: Technology equipment purchased from TechSupply Solutions

Vendor Name: TechSupply Solutions
Items: Dell XPS 15 Laptop
(Document: invoice_tech_001)
```

The LLM can now clearly identify this is a "Technology Purchase" from "TechSupply Solutions" even if compression removed category labels.

### Enhanced System Prompt

The service includes specialized instructions for:
1. **Comparison Queries**: Identify similarities, differences, patterns, and relationships
2. **Cross-Referencing**: Explicitly compare lists to find overlaps (or lack thereof)
3. **Analytical Depth**: Synthesize insights beyond listing facts

## Model Change History

**October 8, 2025 - Switched from Qwen3-32B-fast to Llama-3.3-70B-Instruct-fast**

**Reason:** Nebius changed Qwen3 models to output `<think>` reasoning tokens by default, polluting answer output with chain-of-thought reasoning instead of clean answers.

**Result:**
- ✅ Clean answers without `<think>` tags
- ✅ Better quality for end-user presentation
- ✅ Same cost ($0.20/1M tokens)
- ✅ Similar performance (~1-2s generation time)

## Citation Format

The service automatically detects and extracts citations in the format `[Source X]`:

**Example:**
```
The vajra struck Hanuman's jaw [Source 1], causing severe damage.
Indra later apologized for this action [Source 2].
```

**Extracted Citations:**
- Source 1 → chunk_id, document_id, text snippet
- Source 2 → chunk_id, document_id, text snippet

## When to Use

✅ **Good for:**
- Question answering with factual accuracy
- Generating comprehensive answers from multiple sources
- Providing cited, verifiable responses
- Cross-referencing and comparison queries
- Queries requiring understanding of document categories

❌ **Not needed for:**
- Simple keyword searches
- Document retrieval only
- Real-time chat without context

## API Version

v1.0.0 - October 2025
- LLM-based answer generation with citations
- Metadata enrichment support (topics, keywords, summary)
- Enhanced prompts for cross-referencing and comparison queries
