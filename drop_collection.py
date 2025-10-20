#!/usr/bin/env python3
"""Drop test_comprehensive_v4 collection"""

from pymilvus import connections, utility

# Connect
connections.connect(host="localhost", port="19530")

# Drop collection if it exists
if utility.has_collection("test_comprehensive_v4"):
    utility.drop_collection("test_comprehensive_v4")
    print("✅ Dropped collection: test_comprehensive_v4")
else:
    print("Collection test_comprehensive_v4 does not exist")

connections.disconnect("default")
