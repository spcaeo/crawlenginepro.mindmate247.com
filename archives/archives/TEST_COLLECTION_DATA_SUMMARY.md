# test_collection Data Summary

**Database**: Milvus (via SSH tunnel on localhost:19530)
**Attu UI**: http://localhost:3000/#/databases/default/test_collection/data
**Collection**: `test_collection`
**Total Records**: 18 chunks
**Document**: `comprehensive_test_doc` (single test document)
**Tenant**: `test_tenant`
**Vector Dimension**: 1024 (Jina embeddings v3)
**Index**: FLAT with Inner Product (IP) metric

---

## Data Inventory by Category

### 📱 Electronics (3 chunks)
- **Chunk #0**: Header - "Comprehensive Product Catalog & Business Documents Test"
- **Chunk #1**: Apple iPhone 15 Pro Max - Full specs, pricing ($1,199), features
- **Chunk #2**: Nike Air Zoom Pegasus 40 - Running shoes with tech specs
- **Chunk #3**: Nike contact information

### 🚗 Automotive (1 chunk)
- **Chunk #6**: Michelin Pilot Sport 4S Tire - Summer performance tire specs

### 🏠 Real Estate (1 chunk)
- **Chunk #7**: Modern Luxury Townhouse - Austin, TX listing ($875,000)

### 💊 Medical/Healthcare (4 chunks)
- **Chunk #8**: Medical Equipment Invoice - Philips IntelliVue MX40, $32,450.85
- **Chunk #9**: Hospital procurement entities (St. Mary's Hospital, Dr. Emily Rodriguez)
- **Chunk #14**: CardioHealth Plus Supplement - Pharmaceutical product info
- **Chunk #15**: Supplement details (120 capsules, $34.95)

### 📚 Book Publishing (2 chunks)
- **Chunk #10**: "The Future of Artificial Intelligence" - Book details (ISBN, $49.95)
- **Chunk #11**: AI book topics (ML, neural networks, ethics, transformer models)

### 🧾 Invoices/Financial (5 chunks)
- **Chunk #4**: Technology Purchase Invoice - Dell XPS 15, Samsung monitor ($2,647.97)
- **Chunk #12**: Restaurant Supply Order - Commercial kitchen equipment ($19,220.76)
- **Chunk #13**: Restaurant equipment financing details
- **Chunk #16**: Construction Materials Invoice - Lumber, concrete, paint ($3,927.73)
- **Chunk #17**: Construction materials specifications (Douglas Fir, 4000 PSI concrete)

### 🚙 Headers/Sections (2 chunks)
- **Chunk #0**: Main document header
- **Chunk #5**: "Product Information - Automotive Parts" section header

---

## Schema Structure

```json
{
  "fields": [
    {"name": "id", "type": "VARCHAR", "max_length": 100},
    {"name": "document_id", "type": "VARCHAR", "max_length": 100},
    {"name": "chunk_index", "type": "INT64"},
    {"name": "text", "type": "VARCHAR", "max_length": 65535},
    {"name": "tenant_id", "type": "VARCHAR", "max_length": 100},
    {"name": "created_at", "type": "VARCHAR", "max_length": 50},
    {"name": "updated_at", "type": "VARCHAR", "max_length": 50},
    {"name": "char_count", "type": "INT64"},
    {"name": "token_count", "type": "INT64"},
    {"name": "dense_vector", "type": "FLOAT_VECTOR", "dim": 1024},
    {"name": "keywords", "type": "VARCHAR", "max_length": 500},
    {"name": "topics", "type": "VARCHAR", "max_length": 500},
    {"name": "questions", "type": "VARCHAR", "max_length": 500},
    {"name": "summary", "type": "VARCHAR", "max_length": 1000}
  ]
}
```

---

## Sample Records

### Electronics Example (Chunk #1)
```
ID: comprehensive_test_doc_chunk_1
Text: Apple iPhone 15 Pro Max specs...
Keywords: Apple, iPhone 15 Pro Max, A17 Pro chip, 256GB, Natural Titanium Blue...
Topics: Smartphones, Technology, Mobile Devices, Camera Systems...
Size: 943 chars
```

### Invoice Example (Chunk #4)
```
ID: comprehensive_test_doc_chunk_4
Text: Invoice #INV-2024-00789, Dell XPS 15...
Keywords: Invoice, Dell XPS 15, Samsung, Logitech MX Master 3S...
Topics: Technology Purchase, Invoice Details, Vendor Information...
Total: $2,647.97
Size: 998 chars
```

### Book Example (Chunk #10)
```
ID: comprehensive_test_doc_chunk_10
Text: "The Future of Artificial Intelligence: A Comprehensive Guide"
Authors: Dr. Sarah Mitchell, Prof. James Wang
Keywords: Artificial Intelligence, TechPress Publishing, ISBN 978-0-123456-78-9
Topics: Machine learning, Ethics in AI, Future trends, NLP, Computer vision
Price: $49.95
Size: 771 chars
```

---

## Test Coverage

This test document comprehensively covers:

✅ **E-commerce**: Product catalogs (electronics, shoes, automotive)
✅ **Financial**: Invoices, purchase orders, payment terms
✅ **Healthcare**: Medical equipment, pharmaceutical products
✅ **Real Estate**: Property listings with detailed specs
✅ **Publishing**: Book metadata with ISBN, pricing
✅ **B2B**: Vendor-buyer relationships, SKUs, specifications

**Metadata Quality**:
- All chunks have keywords, topics, and summaries
- Keywords include proper nouns, brands, models, technical terms
- Topics are high-level themes for categorization
- Summaries provide 1-2 sentence overviews

**Use Cases Demonstrated**:
1. Product search by brand/model/SKU
2. Invoice retrieval by invoice number
3. Price range filtering
4. Multi-field metadata queries
5. Semantic search across diverse content types

---

## Access Methods

### Via Attu UI (Visual)
```
http://localhost:3000/#/databases/default/test_collection/data
```

### Via Storage Service API
```bash
# List collections
curl -s http://localhost:8064/v1/collections

# Get collection info
curl -s http://localhost:8064/v1/collection/test_collection

# Health check
curl -s http://localhost:8064/health | jq '{milvus_connected, collections_count}'
```

### Via Search Service API
```bash
curl -X POST http://localhost:8071/v1/search \
  -H 'Content-Type: application/json' \
  -d '{
    "query_text": "Apple iPhone",
    "collection": "test_collection",
    "top_k": 5
  }'
```

### Via Python (pymilvus)
```python
from pymilvus import connections, Collection

connections.connect(host="localhost", port="19530")
collection = Collection("test_collection")
collection.load()

results = collection.query(
    expr="chunk_index >= 0",
    output_fields=["id", "text", "keywords"],
    limit=18
)
```

---

## Notes

- **Vector embeddings**: Generated using Jina AI embeddings v3 (1024 dimensions)
- **Tenant isolation**: All records belong to "test_tenant"
- **Document structure**: Sequential chunks (0-17) from single comprehensive test document
- **Metadata extraction**: Keywords, topics, and summaries generated by LLM (Qwen3-32B-fast)
- **Index type**: FLAT (exact search, no compression) for accuracy in testing
