#!/usr/bin/env python3
"""
Direct ingestion using chunking orchestrator
"""
import requests
import json
from pathlib import Path

# Read the document
doc_path = Path("/Users/rakesh/Desktop/crawlenginepro.mindmate247.com/code/TestingDocuments/ComprehensiveTestDocument.md")
with open(doc_path, 'r', encoding='utf-8') as f:
    text = f.read()

print(f"📄 Document: {doc_path.name}")
print(f"   Length: {len(text):,} characters\n")

# Prepare payload
payload = {
    "text": text,
    "document_id": "ComprehensiveTestDocument",
    "collection_name": "test_comprehensive_v4",
    "tenant_id": "test_tenant",
    "chunk_size": 512,
    "chunk_overlap": 50,
    "extraction_mode": "basic",  # Use basic mode (7 fields)
    "model": "72B",  # Llama 70B
    "skip_cache": True,
    "storage_mode": "new",  # Create new collection
    "generate_embeddings": True,  # Need embeddings for storage
    "generate_metadata": True  # Need metadata for storage
}

print("🚀 Starting ingestion...")
print(f"   Collection: {payload['collection_name']}")
print(f"   Tenant: {payload['tenant_id']}")
print(f"   Model: {payload['model']}")
print(f"   Mode: {payload['extraction_mode']}\n")

try:
    response = requests.post(
        "http://localhost:8071/v1/orchestrate",  # Development port
        json=payload,
        timeout=180
    )

    if response.status_code == 200:
        result = response.json()
        print("✅ INGESTION SUCCESSFUL!\n")
        print("=" * 80)
        print(f"Document ID: {result.get('document_id')}")
        print(f"Collection: {result.get('collection_name')}")
        print(f"Total chunks: {result.get('total_chunks')}")
        print(f"Successful: {result.get('successful_chunks')}")
        print(f"Failed: {result.get('failed_chunks')}")
        print(f"Total time: {result.get('total_processing_time_ms', 0)/1000:.2f}s")
        print("=" * 80)

        # Show sample chunk
        if result.get('chunks'):
            print(f"\nSample chunk (first):")
            chunk = result['chunks'][0]
            print(f"  Chunk ID: {chunk.get('chunk_id')}")
            print(f"  Text: {chunk.get('text', '')[:100]}...")
            print(f"\n  Metadata fields:")
            print(f"    keywords: {chunk.get('keywords', 'MISSING')[:80]}...")
            print(f"    topics: {chunk.get('topics', 'MISSING')}")
            print(f"    summary: {chunk.get('summary', 'MISSING')[:80]}...")
            print(f"    semantic_keywords: {chunk.get('semantic_keywords', 'MISSING')[:80]}...")
            print(f"    entity_relationships: {chunk.get('entity_relationships', 'MISSING')[:80]}...")
            print(f"    attributes: {chunk.get('attributes', 'MISSING')[:80]}...")

    else:
        print(f"❌ Error: HTTP {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Exception: {e}")
