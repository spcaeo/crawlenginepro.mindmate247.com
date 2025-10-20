#!/usr/bin/env python3
"""
Verify that data is immediately visible after ingestion (without manual flush)
"""

from pymilvus import connections, Collection

print("=" * 80)
print("🔍 VERIFYING IMMEDIATE DATA VISIBILITY")
print("=" * 80)

# Connect to Milvus
connections.connect(host='localhost', port='19530')

collection_name = 'benchmark_test_collection'
collection = Collection(collection_name)

print(f"\n📊 Collection: {collection_name}")

# Check entity count (should be 18 immediately)
count = collection.num_entities
print(f"✅ Entities visible: {count}")

if count == 18:
    print("✅ SUCCESS: All 18 chunks are immediately visible!")
    print("✅ The flush() in storage service is working!")
else:
    print(f"❌ ISSUE: Expected 18 entities, but found {count}")

# Query to verify data is accessible
collection.load()
results = collection.query(
    expr="chunk_index >= 0",
    output_fields=["id", "keywords", "topics"],
    limit=3
)

print(f"\n📄 Sample query results (first 3):")
for i, r in enumerate(results, 1):
    keywords = r.get('keywords', '')[:60]
    print(f"   {i}. {r['id'][:40]}...")
    print(f"      Keywords: {keywords}...")

collection.release()
connections.disconnect('default')

print("\n" + "=" * 80)
print("✅ VERIFICATION COMPLETE")
print("=" * 80)
print("\n🌐 Check UI: http://localhost:3000/#/databases/default/benchmark_test_collection/data")
print("   You should see all 18 chunks immediately without manual flush!\n")
