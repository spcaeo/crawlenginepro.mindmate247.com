#!/usr/bin/env python3
"""
Force Milvus UI to see the data by releasing and reloading collections
"""

from pymilvus import connections, Collection, utility
import time

print("=" * 80)
print("🔄 FORCING MILVUS UI REFRESH")
print("=" * 80)

connections.connect(host='localhost', port='19530')

collections = utility.list_collections()
print(f"\n📊 Found {len(collections)} collection(s): {collections}\n")

for coll_name in collections:
    print(f"{'─' * 80}")
    print(f"📦 Collection: {coll_name}")
    print(f"{'─' * 80}")

    collection = Collection(coll_name)

    # Force flush
    print(f"  💾 Flushing to disk...")
    collection.flush()
    time.sleep(2)

    # Release from memory
    try:
        collection.release()
        print(f"  🔓 Released from memory")
        time.sleep(1)
    except:
        print(f"  ℹ️  Collection not loaded, skipping release")

    # Load back into query engine
    print(f"  📥 Loading into query engine...")
    collection.load()
    time.sleep(2)

    # Verify count
    count = collection.num_entities
    print(f"  ✅ Entities: {count}")

    # Compact collection (helps with UI visibility)
    print(f"  🗜️  Compacting collection...")
    collection.compact()
    time.sleep(1)

    print()

connections.disconnect('default')

print("=" * 80)
print("✅ ALL COLLECTIONS REFRESHED")
print("=" * 80)
print()
print("🌐 Now check the Milvus UI:")
print(f"   http://localhost:3000")
print()
print("💡 If still not visible:")
print("   1. Hard refresh browser: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)")
print("   2. Clear browser cache")
print("   3. Click 'Query' button in the UI")
print("   4. Make sure you're on the 'Data' tab, not 'Schema' tab")
print()
print("=" * 80)
