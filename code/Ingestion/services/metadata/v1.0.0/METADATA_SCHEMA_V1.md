# Metadata Service v1.0.0 - Schema Design

**Version:** 1.0.0
**Date:** October 9, 2025
**Purpose:** Extract 7 metadata fields for RAG systems
**LLM Gateway:** Port 8075 (SambaNova API proxy)
**Model:** SambaNova Qwen3-32B (via LLM Gateway)

---

## 📊 Metadata Schema

The Metadata Service v1.0.0 extracts **7 fields** from text chunks to enhance search and retrieval:

### Metadata Fields (7 fields)

```python
keywords: str           # "Apple, iPhone, smartphone, 5G, premium" - Exact terms from text (5-10 keywords)
topics: str             # "Consumer Electronics, Mobile Technology" - High-level categories (2-5 topics)
questions: str          # "What is iPhone 15 Pro?|How much does it cost?" - Answerable questions (2-5 questions)
summary: str            # "Description of Apple iPhone 15 Pro features" - Brief summary (1-2 sentences)
semantic_keywords: str  # "mobile device, iOS device, premium phone" - Synonyms and semantic expansions
entity_relationships: str # "Apple Inc. → manufacturer-of → iPhone 15 Pro" - Entity triplets
attributes: str         # "brand: Apple, price: 1199, currency: USD" - Key-value pairs for filtering
```

---

## 🎯 LLM Extraction Prompt Template

```python
METADATA_PROMPT = """
You are a data extraction API. Extract metadata from the text below.

Text to analyze:
{text}

Extract the following and return as valid JSON:

{{
  "keywords": "comma, separated, exact keywords from text",
  "topics": "comma, separated, topics",
  "questions": "question1?|question2?",
  "summary": "brief summary here",
  "semantic_keywords": "comma, separated, synonyms and semantic expansions",
  "entity_relationships": "Entity1 → relationship → Entity2; Entity3 → relationship → Entity4",
  "attributes": "key1: value1, key2: value2"
}}

Requirements:
1. Extract {keywords_count} exact keywords from text (5-10 recommended)
2. Identify {topics_count} high-level topics (2-5 recommended)
3. Generate {questions_count} answerable questions (2-5 recommended), pipe-separated
4. Write {summary_length} summary (1-2 sentences)
5. Generate semantic_keywords: synonyms, industry terms, semantic expansions
6. Extract entity_relationships: Entity → relationship → Entity triplets, semicolon-separated
7. Identify attributes: structured key-value pairs for filtering, comma-separated
8. Return ONLY valid JSON (no markdown, no explanations)
9. If field cannot be extracted, use empty string ""
10. Use same language as input text

Start your response with opening brace: {{
"""
```

---

## 🔄 Response Model (Pydantic)

```python
from pydantic import BaseModel, Field
from typing import Optional

class MetadataResponse(BaseModel):
    """v1.0.0 Response with 7 metadata fields"""

    # Core metadata
    keywords: str = Field(..., description="Comma-separated exact keywords (5-10)")
    topics: str = Field(..., description="Comma-separated topics (2-5)")
    questions: str = Field(..., description="Pipe-separated questions (2-5)")
    summary: str = Field(..., description="Brief summary (1-2 sentences)")
    semantic_keywords: str = Field(..., description="Comma-separated synonyms and semantic expansions")
    entity_relationships: str = Field(..., description="Entity triplets (Entity → relationship → Entity)")
    attributes: str = Field(..., description="Key-value pairs for filtering (key: value, ...)")

    # Processing metadata (auto-generated)
    chunk_id: Optional[str] = None
    processing_time_ms: Optional[float] = None
```

---

## 🧪 Test Examples

### Example 1: Technical Documentation

**Input:**
```
The ITVAMS system provides vehicle tracking and management capabilities.
It supports GPS monitoring, route optimization, and fleet analytics.
Used by transportation companies worldwide for efficient operations.
```

**Expected Output:**
```json
{
  "keywords": "ITVAMS, vehicle tracking, GPS monitoring, fleet management, route optimization",
  "topics": "Fleet Management, GPS Technology, Transportation",
  "questions": "What is ITVAMS?|What features does it provide?|Who uses ITVAMS?",
  "summary": "ITVAMS is a vehicle tracking system with GPS monitoring and route optimization for fleet management.",
  "semantic_keywords": "vehicle monitoring, fleet tracker, GPS system, auto tracking, transportation software",
  "entity_relationships": "ITVAMS → tracks → Vehicles; GPS → enables → Location Tracking; Fleet Analytics → provides → Insights",
  "attributes": "type: software, industry: transportation, deployment: cloud, features: GPS tracking",
  "chunk_id": "doc_001_chunk_0",
  "processing_time_ms": 450.5
}
```

### Example 2: Product Description

**Input:**
```
Apple iPhone 15 Pro in Natural Titanium, 128GB storage.
Features A17 Pro chip, 48MP camera, and 120Hz display.
Price: $999 USD.
```

**Expected Output:**
```json
{
  "keywords": "Apple, iPhone 15 Pro, A17 Pro chip, 48MP camera, smartphone",
  "topics": "Consumer Electronics, Mobile Devices, Apple Products",
  "questions": "What is iPhone 15 Pro?|What are the specs?|How much does it cost?",
  "summary": "Apple iPhone 15 Pro with 128GB storage, A17 Pro chip, and 48MP camera priced at $999.",
  "semantic_keywords": "mobile device, iOS device, premium phone, flagship smartphone, titanium phone",
  "entity_relationships": "Apple Inc. → manufacturer-of → iPhone 15 Pro; A17 Pro → powers → iPhone 15 Pro; Natural Titanium → material-of → iPhone 15 Pro",
  "attributes": "brand: Apple, model: iPhone 15 Pro, storage: 128GB, price: 999, currency: USD, color: Natural Titanium",
  "chunk_id": "doc_002_chunk_0",
  "processing_time_ms": 520.3
}
```

---

## ✅ Validation Rules

1. **All 7 fields are required** (keywords, topics, questions, summary, semantic_keywords, entity_relationships, attributes)
2. **Keywords:** 5-10 comma-separated exact keywords from text
3. **Topics:** 2-5 comma-separated high-level topics
4. **Questions:** 2-5 questions separated by pipes (|)
5. **Summary:** 1-2 sentences (max 200 characters recommended)
6. **Semantic Keywords:** Synonyms, industry terms, semantic expansions (comma-separated)
7. **Entity Relationships:** Entity → relationship → Entity triplets (semicolon-separated)
8. **Attributes:** Key-value pairs (key: value, key: value format)
9. **JSON validity:** Must return valid JSON (100%)
10. **Language:** Use same language as input text

---

## 📈 Performance Targets

- **Extraction time:** <800ms per chunk (target)
- **Success rate:** >95% valid JSON responses
- **Field quality:** Relevant keywords/topics for 90%+ of chunks
- **Batch processing:** <5s for 10 chunks (parallel)

---

## 🔧 Configuration

The metadata service uses these environment variables:

```bash
# LLM Gateway (port 8075 - part of Ingestion services 8060-8069)
LLM_GATEWAY_URL_DEVELOPMENT=http://localhost:8065/v1/chat/completions
LLM_GATEWAY_URL_PRODUCTION=http://localhost:8065/v1/chat/completions
LLM_GATEWAY_API_KEY=internal_service_2025_secret_key_metadata_embeddings

# Metadata Service Configuration
METADATA_SERVICE_PORT=8072
DEFAULT_MODEL=Qwen3-32B  # SambaNova Qwen3-32B via LLM Gateway
EXTRACTION_MODE=basic    # Only mode in v1.0.0
```

---

## 🏗️ Architecture

```
Ingestion API (8070)
    ↓
Metadata Service (8072) ← This service
    ↓
LLM Gateway (8075) ← SambaNova API proxy
    ↓
SambaNova AI ← Qwen3-32B model
```

**Key Points:**
- Metadata Service calls LLM Gateway (port 8075) for AI extraction
- LLM Gateway proxies requests to SambaNova AI
- Uses SambaNova Qwen3-32B model (best balance: fast + accurate)
- Extracts 7 metadata fields optimized for RAG
- Supports batch processing for efficiency

---

## 📝 API Endpoints

### POST /v3/metadata
Extract metadata from a single chunk.

**Request:**
```json
{
  "text": "Your chunk text here...",
  "chunk_id": "chunk_001",
  "model": "32B-fast",
  "extraction_mode": "basic"
}
```

**Response:**
```json
{
  "keywords": "keyword1, keyword2, keyword3",
  "topics": "topic1, topic2",
  "questions": "Question 1?; Question 2?",
  "summary": "Brief summary of the chunk.",
  "chunk_id": "chunk_001",
  "processing_time_ms": 450.5
}
```

### POST /v3/metadata/batch
Extract metadata from multiple chunks in parallel.

**Request:**
```json
{
  "chunks": [
    {
      "text": "First chunk text...",
      "chunk_id": "chunk_001",
      "model": "32B-fast",
      "extraction_mode": "basic"
    },
    {
      "text": "Second chunk text...",
      "chunk_id": "chunk_002",
      "model": "32B-fast",
      "extraction_mode": "basic"
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "keywords": "...",
      "topics": "...",
      "questions": "...",
      "summary": "...",
      "chunk_id": "chunk_001",
      "processing_time_ms": 450.5
    },
    {
      "keywords": "...",
      "topics": "...",
      "questions": "...",
      "summary": "...",
      "chunk_id": "chunk_002",
      "processing_time_ms": 520.3
    }
  ],
  "successful": 2,
  "failed": 0,
  "total_time_ms": 2150.8
}
```

---

## 🔍 Field Descriptions

### keywords
- **Purpose:** Key terms for search/filtering
- **Format:** Comma-separated string
- **Count:** 5-10 keywords recommended
- **Examples:**
  - `"ITVAMS, vehicle tracking, GPS, fleet management, route optimization"`
  - `"Apple, iPhone 15 Pro, smartphone, A17 chip, camera"`

### topics
- **Purpose:** High-level categories for classification
- **Format:** Comma-separated string
- **Count:** 2-5 topics recommended
- **Examples:**
  - `"Fleet Management, GPS Technology, Transportation"`
  - `"Consumer Electronics, Mobile Devices, Apple Products"`

### questions
- **Purpose:** Questions this chunk can answer (for QA retrieval)
- **Format:** Pipe-separated string
- **Count:** 2-5 questions recommended
- **Examples:**
  - `"What is ITVAMS?|What features does it provide?|Who uses ITVAMS?"`
  - `"What is iPhone 15 Pro?|What are the specs?|How much does it cost?"`

### summary
- **Purpose:** Brief description for display/preview
- **Format:** 1-2 sentences
- **Length:** Max 200 characters recommended
- **Examples:**
  - `"ITVAMS is a vehicle tracking system with GPS monitoring and route optimization."`
  - `"Apple iPhone 15 Pro with 128GB storage and A17 Pro chip priced at $999."`

### semantic_keywords
- **Purpose:** Semantic expansion for better search recall
- **Format:** Comma-separated synonyms and related terms
- **Examples:**
  - `"vehicle monitoring, fleet tracker, GPS system, auto tracking, transportation software"`
  - `"mobile device, iOS device, premium phone, flagship smartphone, titanium phone"`

### entity_relationships
- **Purpose:** Knowledge graph triplets for entity linking
- **Format:** "Entity1 → relationship → Entity2" (semicolon-separated)
- **Examples:**
  - `"ITVAMS → tracks → Vehicles; GPS → enables → Location Tracking; Fleet Analytics → provides → Insights"`
  - `"Apple Inc. → manufacturer-of → iPhone 15 Pro; A17 Pro → powers → iPhone 15 Pro"`

### attributes
- **Purpose:** Structured key-value pairs for faceted filtering
- **Format:** "key: value, key: value" (comma-separated)
- **Examples:**
  - `"type: software, industry: transportation, deployment: cloud, features: GPS tracking"`
  - `"brand: Apple, model: iPhone 15 Pro, storage: 128GB, price: 999, currency: USD"`

---

**END OF SCHEMA DESIGN**
