#!/usr/bin/env python3
from pymilvus import connections, Collection

connections.connect(alias='default', host='localhost', port='19530')

collection = Collection('test_comprehensive_v4')

print("Collection Schema:")
print("=" * 80)
for field in collection.schema.fields:
    print(f"- {field.name}: {field.dtype}")

connections.disconnect(alias='default')
