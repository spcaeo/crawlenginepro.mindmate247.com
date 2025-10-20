#!/usr/bin/env python3
"""
Force flush collection data and verify visibility in Milvus UI
"""

from pymilvus import connections, Collection, utility
import time

print("=" * 80)
print("🔄 FORCING MILVUS DATA FLUSH AND VERIFICATION")
print("=" * 80)

# Connect to Milvus
connections.connect(host='localhost', port='19530')

# Get all collections
collections = utility.list_collections()
print(f"\n📊 Found {len(collections)} collection(s): {collections}\n")

for coll_name in collections:
    print(f"{'─' * 80}")
    print(f"📦 Collection: {coll_name}")
    print(f"{'─' * 80}")

    collection = Collection(coll_name)

    # Get count before flush
    count_before = collection.num_entities
    print(f"  Entities (before flush): {count_before}")

    # Force flush to persist all data
    print(f"  💾 Flushing collection to disk...")
    collection.flush()
    time.sleep(1)  # Wait for flush to complete

    # Get count after flush
    count_after = collection.num_entities
    print(f"  Entities (after flush): {count_after}")

    # Release if loaded
    try:
        collection.release()
        print(f"  🔓 Released collection from memory")
    except:
        pass

    # Load collection
    print(f"  📥 Loading collection into query engine...")
    collection.load()
    time.sleep(1)  # Wait for loading

    # Get count after load
    count_loaded = collection.num_entities
    print(f"  Entities (after load): {count_loaded}")

    # Query to verify data is accessible
    if count_loaded > 0:
        print(f"  🔍 Verifying data accessibility...")
        results = collection.query(
            expr="chunk_index >= 0",
            output_fields=["id", "document_id", "keywords", "topics", "summary"],
            limit=3
        )

        if results:
            print(f"  ✅ Successfully queried {len(results)} chunks")
            for i, r in enumerate(results[:3], 1):
                keywords = r.get('keywords', '')[:50]
                print(f"     {i}. {r['id']}: {keywords}...")
        else:
            print(f"  ⚠️  Query returned no results")
    else:
        print(f"  ❌ Collection appears empty!")

    print()

connections.disconnect('default')

print("=" * 80)
print("✅ FLUSH COMPLETE!")
print("=" * 80)
print()
print("🌐 Now check the Milvus UI:")
print("   http://localhost:3000/#/databases/default/test_comprehensive_detailed/data")
print()
print("💡 If you still don't see data in the UI:")
print("   1. Click the 'Query' button in the UI")
print("   2. Try 'Load Collection' button if available")
print("   3. Refresh your browser (Ctrl+Shift+R / Cmd+Shift+R)")
print("   4. Check the 'Data' tab (not just 'Schema' tab)")
print()
print("=" * 80)
