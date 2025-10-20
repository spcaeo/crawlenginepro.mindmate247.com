#!/usr/bin/env python3
"""Check the schema of test_comprehensive_v4 collection"""

from pymilvus import connections, Collection

connections.connect(host="localhost", port="19530")

collection = Collection("test_comprehensive_v4")

print("Collection schema fields:")
for field in collection.schema.fields:
    print(f"  {field.name}: {field.dtype}")

connections.disconnect("default")
