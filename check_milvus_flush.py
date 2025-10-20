#!/usr/bin/env python3
"""Flush and reload collection, then query data"""

from pymilvus import connections, Collection

connections.connect(host="localhost", port="19530")

collection = Collection("test_comprehensive_v4")

# Flush to ensure all data is persisted
print("Flushing collection...")
collection.flush()

# Release and reload
print("Reloading collection...")
collection.release()
collection.load()

# Query with limit 2
results = collection.query(
    expr="chunk_index >= 0",
    output_fields=["id", "text", "keywords", "semantic_keywords", "entity_relationships", "attributes"],
    limit=2
)

print(f"\nFound {len(results)} chunks:\n")
for i, chunk in enumerate(results, 1):
    print(f"=== Chunk {i}: {chunk['id']} ===")
    print(f"Text (first 60 chars): {chunk['text'][:60]}...")
    print(f"\nAll 7 metadata fields:")
    print(f"  keywords: {chunk.get('keywords', 'NULL')[:80]}")
    print(f"  semantic_keywords: '{chunk.get('semantic_keywords', 'NULL')}'")
    print(f"  entity_relationships: '{chunk.get('entity_relationships', 'NULL')[:80]}'")
    print(f"  attributes: '{chunk.get('attributes', 'NULL')[:80]}'")

    if chunk.get('semantic_keywords'):
        print(f"\n✅ semantic_keywords has data!")
    else:
        print(f"\n❌ semantic_keywords is empty")
    print()

connections.disconnect("default")
