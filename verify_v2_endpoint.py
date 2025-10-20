#!/usr/bin/env python3
"""Verify what /v2/metadata endpoint returns"""

import requests
import json

text = """The Apple iPhone 15 Pro Max is a premium smartphone manufactured by Apple Inc.
It features the powerful A17 Pro chip, advanced 48MP camera system, and durable titanium design.
The device runs iOS 17 and costs $1199 USD."""

response = requests.post(
    "http://localhost:8072/v2/metadata",
    json={"text": text, "chunk_id": "verification_test"},
    timeout=30
)

if response.status_code == 200:
    data = response.json()
    print("✅ /v2/metadata endpoint response:\n")
    print(f"Fields returned: {list(data.keys())}\n")
    print("=" * 80)
    for key, value in data.items():
        if key in ['processing_time_ms', 'api_version', 'chunk_id', 'model_used']:
            print(f"{key}: {value}")
        else:
            print(f"\n{key}:")
            print(f"  {value}")
    print("=" * 80)
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
