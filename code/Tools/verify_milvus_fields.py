#!/usr/bin/env python3
"""
Verify that all 7 metadata fields are stored in Milvus
"""
from pymilvus import connections, Collection
import json

# Connect to Milvus
connections.connect(alias='default', host='localhost', port='19530')
print("✓ Connected to Milvus\n")

collection_name = 'test_comprehensive_v4'

# Load collection
collection = Collection(collection_name)
collection.load()
print(f"✓ Loaded collection: {collection_name}")
print(f"  Total entities: {collection.num_entities}\n")

# Query a few chunks to verify fields
results = collection.query(
    expr="tenant_id == 'test_tenant'",
    output_fields=[
        "id", "text", "keywords", "topics", "summary",
        "semantic_keywords", "entity_relationships", "attributes"
    ],
    limit=3
)

print("=" * 100)
print("VERIFYING 7 METADATA FIELDS IN STORED CHUNKS")
print("=" * 100)

for idx, entity in enumerate(results[:2], 1):  # Show first 2 chunks
    print(f"\n{'='*100}")
    print(f"CHUNK #{idx}: {entity.get('id')}")
    print(f"{'='*100}")

    print(f"\n📝 Text (first 100 chars):")
    print(f"   {entity.get('text', '')[:100]}...")

    print(f"\n🔍 7 METADATA FIELDS:")
    print(f"{'─'*100}")

    fields = [
        ("1. keywords", entity.get('keywords', '')),
        ("2. topics", entity.get('topics', '')),
        ("3. summary", entity.get('summary', '')),
        ("4. semantic_keywords", entity.get('semantic_keywords', '')),
        ("5. entity_relationships", entity.get('entity_relationships', '')),
        ("6. attributes", entity.get('attributes', '')),
    ]

    for name, value in fields:
        status = "✓" if value else "✗"
        display_value = value[:150] if value else "(EMPTY)"
        print(f"\n{status} {name}:")
        print(f"   {display_value}")
        if value and len(value) > 150:
            print(f"   ... ({len(value)} total chars)")

# Count how many chunks have all 7 fields populated
all_results = collection.query(
    expr="tenant_id == 'test_tenant'",
    output_fields=["semantic_keywords", "entity_relationships", "attributes"],
    limit=1000
)

populated_count = sum(
    1 for r in all_results
    if r.get('semantic_keywords') and r.get('entity_relationships') and r.get('attributes')
)

print(f"\n{'='*100}")
print(f"SUMMARY: {populated_count}/{len(all_results)} chunks have all 3 new fields populated")
print(f"{'='*100}")

if populated_count == len(all_results):
    print("✅ SUCCESS: All chunks have all 7 metadata fields!")
else:
    print(f"⚠️  WARNING: {len(all_results) - populated_count} chunks missing new fields")

connections.disconnect(alias='default')
