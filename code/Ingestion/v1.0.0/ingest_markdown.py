#!/usr/bin/env python3
"""
Simple Markdown Document Ingestion Script
Directly ingest markdown files into the vector database
"""

import requests
import sys
import time
from pathlib import Path

def ingest_markdown_file(
    file_path: str,
    collection: str = "test_collection",
    tenant_id: str = "test_tenant",
    api_url: str = "http://localhost:8070"
):
    """
    Ingest a markdown file into the vector database

    Args:
        file_path: Path to the markdown file
        collection: Collection name
        tenant_id: Tenant ID for multi-tenancy
        api_url: Ingestion API URL
    """
    file_path = Path(file_path)

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    print(f"\n📄 Reading file: {file_path.name}")
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    print(f"   Length: {len(text):,} characters")

    # Use filename (without extension) as document ID
    document_id = file_path.stem

    payload = {
        "text": text,
        "document_id": document_id,
        "collection_name": collection,
        "tenant_id": tenant_id
    }

    print(f"\n🚀 Ingesting into collection: {collection}")
    print(f"   Document ID: {document_id}")
    print(f"   Tenant ID: {tenant_id}")

    start_time = time.time()

    try:
        response = requests.post(
            f"{api_url}/v1/ingest",
            json=payload,
            timeout=180
        )

        elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"   Document ID: {result.get('document_id')}")
            print(f"   Total Chunks: {result.get('total_chunks')}")
            print(f"   Collection: {result.get('collection_name')}")
            print(f"   Processing Time: {result.get('processing_time_ms', 0) / 1000:.1f}s")
            print(f"   Total Time: {elapsed:.1f}s")
            return True
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            print(f"   {response.text[:500]}")
            return False

    except requests.exceptions.Timeout:
        print(f"\n❌ ERROR: Request timeout after 180s")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest_markdown.py <file_path> [collection] [tenant_id]")
        print("\nExamples:")
        print("  python ingest_markdown.py /path/to/document.md")
        print("  python ingest_markdown.py /path/to/document.md my_collection")
        print("  python ingest_markdown.py /path/to/document.md my_collection my_tenant")
        sys.exit(1)

    file_path = sys.argv[1]
    collection = sys.argv[2] if len(sys.argv) > 2 else "test_collection"
    tenant_id = sys.argv[3] if len(sys.argv) > 3 else "test_tenant"

    success = ingest_markdown_file(file_path, collection, tenant_id)
    sys.exit(0 if success else 1)
