#!/usr/bin/env python3
"""Quick script to check what's stored in test_comprehensive_v4 collection"""

from pymilvus import connections, Collection

# Connect to Milvus
connections.connect(host="localhost", port="19530")

# Load collection
collection = Collection("test_comprehensive_v4")
collection.load()

# Query first 3 entries
results = collection.query(
    expr="chunk_index >= 0",
    output_fields=["id", "text", "keywords", "topics", "summary", "semantic_keywords", "entity_relationships", "attributes"],
    limit=3
)

print(f"Found {len(results)} chunks:\n")
for i, chunk in enumerate(results, 1):
    print(f"=== Chunk {i}: {chunk['id']} ===")
    print(f"Text (first 100 chars): {chunk['text'][:100]}...")
    print(f"\nMetadata fields:")
    print(f"  keywords: {chunk.get('keywords', 'EMPTY')}")
    print(f"  topics: {chunk.get('topics', 'EMPTY')}")
    print(f"  summary: {chunk.get('summary', 'EMPTY')}")
    print(f"  semantic_keywords: {chunk.get('semantic_keywords', 'EMPTY')}")
    print(f"  entity_relationships: {chunk.get('entity_relationships', 'EMPTY')}")
    print(f"  attributes: {chunk.get('attributes', 'EMPTY')}")
    print()

connections.disconnect("default")
