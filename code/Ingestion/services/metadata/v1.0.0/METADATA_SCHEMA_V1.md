# Metadata Service v1.0.0 - Schema Design

**Version:** 1.0.0
**Date:** October 9, 2025
**Purpose:** Extract 4 core metadata fields for RAG systems
**LLM Gateway:** Port 8065 (Nebius AI Studio proxy)

---

## 📊 Metadata Schema

The Metadata Service v1.0.0 extracts **4 core fields** from text chunks to enhance search and retrieval:

### Core Metadata Fields (4 fields)

```python
keywords: str           # "Apple, iPhone, smartphone, 5G, premium" (5-10 keywords)
topics: str             # "Consumer Electronics, Mobile Technology" (2-5 topics)
questions: str          # "What is iPhone 15 Pro?, How much does it cost?" (2-5 questions)
summary: str            # "Description of Apple iPhone 15 Pro features" (1-2 sentences)
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
  "keywords": "comma, separated, keywords",
  "topics": "comma, separated, topics",
  "questions": "question1?, question2?",
  "summary": "brief summary here"
}}

Requirements:
1. Extract {keywords_count} keywords (5-10 recommended)
2. Identify {topics_count} topics (2-5 recommended)
3. Generate {questions_count} questions (2-5 recommended)
4. Write {summary_length} summary (1-2 sentences)
5. Return ONLY valid JSON (no markdown, no explanations)
6. If field cannot be extracted, use empty string ""
7. Use same language as input text

Start your response with opening brace: {{
"""
```

---

## 🔄 Response Model (Pydantic)

```python
from pydantic import BaseModel, Field
from typing import Optional

class MetadataResponse(BaseModel):
    """v1.0.0 Response with 4 core fields"""

    # Core metadata
    keywords: str = Field(..., description="Comma-separated keywords (5-10)")
    topics: str = Field(..., description="Comma-separated topics (2-5)")
    questions: str = Field(..., description="Semicolon-separated questions (2-5)")
    summary: str = Field(..., description="Brief summary (1-2 sentences)")

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
  "questions": "What is ITVAMS?, What features does it provide?, Who uses ITVAMS?",
  "summary": "ITVAMS is a vehicle tracking system with GPS monitoring and route optimization for fleet management.",
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
  "questions": "What is iPhone 15 Pro?, What are the specs?, How much does it cost?",
  "summary": "Apple iPhone 15 Pro with 128GB storage, A17 Pro chip, and 48MP camera priced at $999.",
  "chunk_id": "doc_002_chunk_0",
  "processing_time_ms": 520.3
}
```

---

## ✅ Validation Rules

1. **All 4 core fields are required** (keywords, topics, questions, summary)
2. **Keywords:** 5-10 comma-separated keywords
3. **Topics:** 2-5 comma-separated topics
4. **Questions:** 2-5 questions separated by semicolons
5. **Summary:** 1-2 sentences (max 200 characters recommended)
6. **JSON validity:** Must return valid JSON (100%)
7. **Language:** Use same language as input text

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
# LLM Gateway (port 8065 - part of Ingestion services 8060-8069)
LLM_GATEWAY_URL_DEVELOPMENT=http://localhost:8065/v1/chat/completions
LLM_GATEWAY_URL_PRODUCTION=http://localhost:8065/v1/chat/completions
LLM_GATEWAY_API_KEY=internal_service_2025_secret_key_metadata_embeddings

# Metadata Service Configuration
METADATA_SERVICE_PORT=8062
DEFAULT_MODEL=32B-fast  # Qwen/Qwen3-32B-fast via LLM Gateway
EXTRACTION_MODE=basic    # Only mode in v1.0.0
```

---

## 🏗️ Architecture

```
Ingestion API (8060)
    ↓
Metadata Service (8062) ← This service
    ↓
LLM Gateway (8065) ← Nebius AI Studio proxy
    ↓
Nebius AI Studio ← Qwen/Qwen3-32B-fast model
```

**Key Points:**
- Metadata Service calls LLM Gateway (port 8065) for AI extraction
- LLM Gateway proxies requests to Nebius AI Studio
- Uses Qwen3-32B-fast model (best balance: fast + accurate)
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
- **Format:** Semicolon-separated string
- **Count:** 2-5 questions recommended
- **Examples:**
  - `"What is ITVAMS?; What features does it provide?; Who uses ITVAMS?"`
  - `"What is iPhone 15 Pro?; What are the specs?; How much does it cost?"`

### summary
- **Purpose:** Brief description for display/preview
- **Format:** 1-2 sentences
- **Length:** Max 200 characters recommended
- **Examples:**
  - `"ITVAMS is a vehicle tracking system with GPS monitoring and route optimization."`
  - `"Apple iPhone 15 Pro with 128GB storage and A17 Pro chip priced at $999."`

---

**END OF SCHEMA DESIGN**
