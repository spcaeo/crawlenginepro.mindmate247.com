#!/usr/bin/env python3
"""
Timed Markdown Document Ingestion Script
Track timing for each stage of the ingestion pipeline
"""

import requests
import sys
import time
from pathlib import Path
from typing import Dict, Any

def format_time(seconds: float) -> str:
    """Format seconds into human-readable time"""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    return f"{seconds:.2f}s"

def ingest_markdown_timed(
    file_path: str,
    collection: str = "test_collection",
    tenant_id: str = "test_tenant",
    api_url: str = "http://localhost:8070"
):
    """
    Ingest a markdown file with detailed stage timing

    Args:
        file_path: Path to the markdown file
        collection: Collection name
        tenant_id: Tenant ID for multi-tenancy
        api_url: Ingestion API URL
    """
    timings = {}
    total_start = time.time()

    # Stage 1: File Reading
    stage_start = time.time()
    file_path = Path(file_path)

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False, None

    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    timings['file_reading'] = time.time() - stage_start

    print(f"\n" + "="*70)
    print(f"📄 TIMED INGESTION: {file_path.name}")
    print(f"="*70)
    print(f"File Size: {len(text):,} characters")
    print(f"Collection: {collection}")
    print(f"Tenant ID: {tenant_id}")
    print(f"="*70)

    # Use filename (without extension) as document ID
    document_id = file_path.stem

    payload = {
        "text": text,
        "document_id": document_id,
        "collection_name": collection,
        "tenant_id": tenant_id
    }

    # Stage 2: API Request (includes all pipeline stages)
    print(f"\n🚀 Starting ingestion pipeline...")
    stage_start = time.time()

    try:
        response = requests.post(
            f"{api_url}/v1/ingest",
            json=payload,
            timeout=180
        )

        timings['api_request'] = time.time() - stage_start

        if response.status_code == 200:
            result = response.json()

            # Extract detailed timings from response if available
            if 'stages' in result:
                pipeline_stages = result['stages']
                print(f"\n📊 PIPELINE STAGE TIMINGS:")
                print(f"-"*70)

                # Display each stage timing with details
                for stage_name, stage_data in pipeline_stages.items():
                    if isinstance(stage_data, dict) and 'time_ms' in stage_data:
                        timing_ms = stage_data['time_ms']
                        timing_sec = timing_ms / 1000

                        # Build details string
                        details = []
                        if stage_name == 'chunking':
                            details.append(f"chunks: {stage_data.get('chunks_created', 0)}")
                        elif stage_name == 'metadata':
                            details.append(f"generated: {stage_data.get('generated', False)}")
                        elif stage_name == 'embeddings':
                            details.append(f"model: {stage_data.get('model', 'N/A')}")
                            details.append(f"generated: {stage_data.get('generated', False)}")
                        elif stage_name == 'storage':
                            details.append(f"collection: {stage_data.get('collection_name', 'N/A')}")
                            details.append(f"stored: {stage_data.get('stored', False)}")

                        detail_str = ', '.join(details) if details else ''
                        print(f"  {stage_name.capitalize():<15} {format_time(timing_sec):>12}    {detail_str}")

                # Store stage timings
                for stage_name, stage_data in pipeline_stages.items():
                    if isinstance(stage_data, dict) and 'time_ms' in stage_data:
                        timings[f'stage_{stage_name}'] = stage_data['time_ms']

            # Total pipeline time
            total_elapsed = time.time() - total_start
            timings['total'] = total_elapsed * 1000  # Convert to ms

            print(f"-"*70)

            # Calculate stage percentages
            total_stage_time = sum(stage_data.get('time_ms', 0)
                                  for stage_data in pipeline_stages.values()
                                  if isinstance(stage_data, dict))

            if total_stage_time > 0:
                print(f"\n📈 STAGE BREAKDOWN (% of pipeline time):")
                print(f"-"*70)
                for stage_name, stage_data in pipeline_stages.items():
                    if isinstance(stage_data, dict) and 'time_ms' in stage_data:
                        percentage = (stage_data['time_ms'] / total_stage_time) * 100
                        print(f"  {stage_name.capitalize():<15} {percentage:>6.1f}%")
                print(f"-"*70)

            print(f"\n✅ INGESTION COMPLETE!")
            print(f"="*70)
            print(f"Document ID:    {result.get('document_id')}")
            print(f"Total Chunks:   {result.get('chunks_created', 0)}")
            print(f"Chunks Stored:  {result.get('chunks_inserted', 0)}")
            print(f"-"*70)
            print(f"File Reading:   {format_time(timings['file_reading']):>12}")
            print(f"Pipeline Time:  {format_time(result.get('processing_time_ms', 0) / 1000):>12}")
            print(f"Total Time:     {format_time(total_elapsed):>12}")
            print(f"="*70)

            return True, timings
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            print(f"   {response.text[:500]}")
            return False, None

    except requests.exceptions.Timeout:
        print(f"\n❌ ERROR: Request timeout after 180s")
        return False, None
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False, None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest_markdown_timed.py <file_path> [collection] [tenant_id]")
        print("\nExamples:")
        print("  python ingest_markdown_timed.py /path/to/document.md")
        print("  python ingest_markdown_timed.py /path/to/document.md my_collection")
        print("  python ingest_markdown_timed.py /path/to/document.md my_collection my_tenant")
        sys.exit(1)

    file_path = sys.argv[1]
    collection = sys.argv[2] if len(sys.argv) > 2 else "test_collection"
    tenant_id = sys.argv[3] if len(sys.argv) > 3 else "test_tenant"

    success, timings = ingest_markdown_timed(file_path, collection, tenant_id)
    sys.exit(0 if success else 1)
