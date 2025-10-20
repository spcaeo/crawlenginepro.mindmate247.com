#!/usr/bin/env python3
"""
Quick script to drop test_comprehensive_v4 collection
"""
from pymilvus import connections, utility

try:
    # Connect to Milvus
    connections.connect(alias='default', host='localhost', port='19530')
    print("✓ Connected to Milvus")

    collection_name = 'test_comprehensive_v4'

    # Check if collection exists
    if utility.has_collection(collection_name):
        print(f"Found collection: {collection_name}")
        utility.drop_collection(collection_name)
        print(f"✓ Dropped collection: {collection_name}")
    else:
        print(f"Collection {collection_name} does not exist")

    connections.disconnect(alias='default')
    print("✓ Disconnected from Milvus")

except Exception as e:
    print(f"✗ Error: {e}")
