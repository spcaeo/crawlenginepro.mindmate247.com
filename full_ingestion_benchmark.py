#!/usr/bin/env python3
"""
COMPLETE INGESTION BENCHMARK - From Collection Drop to Final Verification
Tracks every single step with detailed timing
"""

import requests
import time
import json
from pathlib import Path
from datetime import datetime
from pymilvus import connections, Collection, utility
import sys

# Configuration
TEST_DOCUMENT = "/Users/rakesh/Desktop/crawlenginepro.mindmate247.com/code/TestingDocuments/ComprehensiveTestDocument.md"
COLLECTION_NAME = "benchmark_test_collection"
TENANT_ID = "default"
INGESTION_API_URL = "http://localhost:8070"
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"

# Comprehensive timing tracker
timings = {
    "test_started_at": datetime.now().isoformat(),
    "stages": {}
}

def record_timing(stage_name, start_time, extra_data=None):
    """Record timing for a stage"""
    elapsed_ms = (time.time() - start_time) * 1000
    timings["stages"][stage_name] = {
        "duration_ms": elapsed_ms,
        "duration_seconds": elapsed_ms / 1000,
        "timestamp": datetime.now().isoformat()
    }
    if extra_data:
        timings["stages"][stage_name].update(extra_data)
    return elapsed_ms

def print_header(text):
    print("\n" + "=" * 100)
    print(f"  {text}")
    print("=" * 100)

def print_stage(stage_num, text):
    print(f"\n{'─' * 100}")
    print(f"🔹 STAGE {stage_num}: {text}")
    print(f"{'─' * 100}")

def print_timing(label, elapsed_ms):
    print(f"   ⏱️  {label}: {elapsed_ms:.2f}ms ({elapsed_ms/1000:.3f}s)")

def main():
    test_start = time.time()

    print_header("🚀 COMPLETE INGESTION BENCHMARK - FULL CYCLE TEST")
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Document: {Path(TEST_DOCUMENT).name}")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"API: {INGESTION_API_URL}")

    # ========================================================================
    # STAGE 1: Connect to Milvus
    # ========================================================================
    print_stage(1, "Milvus Connection")
    stage_start = time.time()

    try:
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        elapsed = record_timing("milvus_connection", stage_start, {
            "host": MILVUS_HOST,
            "port": MILVUS_PORT,
            "status": "success"
        })
        print_timing("Connected to Milvus", elapsed)
    except Exception as e:
        print(f"   ❌ Failed to connect: {e}")
        sys.exit(1)

    # ========================================================================
    # STAGE 2: Check for Existing Collection
    # ========================================================================
    print_stage(2, "Check for Existing Collection")
    stage_start = time.time()

    collections_before = utility.list_collections()
    collection_exists = COLLECTION_NAME in collections_before

    elapsed = record_timing("check_existing_collection", stage_start, {
        "collections_found": len(collections_before),
        "target_exists": collection_exists,
        "collections": collections_before
    })

    print(f"   📊 Existing collections: {len(collections_before)}")
    for coll in collections_before:
        print(f"      - {coll}")
    print_timing("Check completed", elapsed)

    # ========================================================================
    # STAGE 3: Drop Collection (if exists)
    # ========================================================================
    if collection_exists:
        print_stage(3, "Drop Existing Collection")
        stage_start = time.time()

        try:
            # Get entity count before dropping
            collection = Collection(COLLECTION_NAME)
            entity_count = collection.num_entities

            # Drop collection
            utility.drop_collection(COLLECTION_NAME)

            elapsed = record_timing("drop_collection", stage_start, {
                "collection_name": COLLECTION_NAME,
                "entities_dropped": entity_count,
                "status": "success"
            })

            print(f"   🗑️  Dropped collection: {COLLECTION_NAME}")
            print(f"   📊 Entities dropped: {entity_count}")
            print_timing("Drop completed", elapsed)
        except Exception as e:
            print(f"   ❌ Failed to drop: {e}")
            elapsed = record_timing("drop_collection", stage_start, {
                "status": "failed",
                "error": str(e)
            })
    else:
        print_stage(3, "Drop Existing Collection")
        print(f"   ℹ️  Collection '{COLLECTION_NAME}' does not exist - nothing to drop")
        record_timing("drop_collection", time.time(), {
            "status": "skipped",
            "reason": "collection_not_found"
        })

    # ========================================================================
    # STAGE 4: Verify Collection Dropped
    # ========================================================================
    print_stage(4, "Verify Collection Dropped")
    stage_start = time.time()

    collections_after = utility.list_collections()
    is_dropped = COLLECTION_NAME not in collections_after

    elapsed = record_timing("verify_drop", stage_start, {
        "collections_remaining": len(collections_after),
        "target_dropped": is_dropped,
        "collections": collections_after
    })

    if is_dropped:
        print(f"   ✅ Confirmed: Collection '{COLLECTION_NAME}' has been dropped")
    else:
        print(f"   ❌ Error: Collection '{COLLECTION_NAME}' still exists!")
        sys.exit(1)

    print(f"   📊 Remaining collections: {len(collections_after)}")
    print_timing("Verification completed", elapsed)

    # ========================================================================
    # STAGE 5: Read Test Document
    # ========================================================================
    print_stage(5, "Read Test Document")
    stage_start = time.time()

    doc_path = Path(TEST_DOCUMENT)
    if not doc_path.exists():
        print(f"   ❌ Document not found: {doc_path}")
        sys.exit(1)

    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    char_count = len(content)
    word_count = len(content.split())
    line_count = content.count('\n')
    est_tokens = char_count // 4

    elapsed = record_timing("read_document", stage_start, {
        "file_path": str(doc_path),
        "file_size_bytes": doc_path.stat().st_size,
        "char_count": char_count,
        "word_count": word_count,
        "line_count": line_count,
        "estimated_tokens": est_tokens
    })

    print(f"   📄 Document: {doc_path.name}")
    print(f"   📊 Characters: {char_count:,}")
    print(f"   📊 Words: {word_count:,}")
    print(f"   📊 Lines: {line_count:,}")
    print(f"   📊 Est. Tokens: {est_tokens:,}")
    print_timing("Read completed", elapsed)

    # ========================================================================
    # STAGE 6: Send Ingestion Request
    # ========================================================================
    print_stage(6, "Send Ingestion Request to API")
    stage_start = time.time()

    payload = {
        "text": content,
        "document_id": "ComprehensiveTestDocument",
        "collection_name": COLLECTION_NAME,
        "tenant_id": TENANT_ID,
        "chunking_method": "recursive",
        "max_chunk_size": 1000,
        "chunk_overlap": 300,
        "generate_metadata": True,
        "keywords_count": 5,
        "topics_count": 3,
        "questions_count": 3,
        "summary_length": "1-2 sentences",
        "generate_embeddings": True,
        "embedding_model": "E5-Mistral-7B-Instruct",
        "storage_mode": "new_collection",
        "create_collection_if_missing": True
    }

    print(f"   📤 Sending to: {INGESTION_API_URL}/v1/ingest")
    print(f"   📊 Document ID: {payload['document_id']}")
    print(f"   📊 Chunking: {payload['chunking_method']} (size={payload['max_chunk_size']}, overlap={payload['chunk_overlap']})")
    print(f"   📊 Embedding Model: {payload['embedding_model']}")
    print(f"   📊 Metadata: Enabled (7 fields)")

    try:
        response = requests.post(
            f"{INGESTION_API_URL}/v1/ingest",
            json=payload,
            timeout=300
        )

        api_elapsed = record_timing("api_request_total", stage_start)

        if response.status_code == 200:
            result = response.json()

            # Extract pipeline stages
            stages = result.get('stages', {})

            timings["stages"]["api_request_total"].update({
                "status": "success",
                "http_code": 200,
                "chunks_created": result.get('chunks_created'),
                "chunks_inserted": result.get('chunks_inserted'),
                "pipeline_response": {
                    "chunking_ms": stages.get('chunking', {}).get('time_ms', 0),
                    "metadata_ms": stages.get('metadata', {}).get('time_ms', 0),
                    "embeddings_ms": stages.get('embeddings', {}).get('time_ms', 0),
                    "storage_ms": stages.get('storage', {}).get('time_ms', 0),
                    "total_pipeline_ms": result.get('processing_time_ms', 0)
                }
            })

            print(f"   ✅ Ingestion successful!")
            print(f"   📊 Chunks created: {result.get('chunks_created')}")
            print(f"   📊 Chunks inserted: {result.get('chunks_inserted')}")
            print_timing("Total API request time", api_elapsed)

            # Print detailed pipeline breakdown
            print(f"\n   📊 Pipeline Stage Breakdown:")
            if 'chunking' in stages:
                print(f"      1. Chunking:    {stages['chunking'].get('time_ms', 0):.2f}ms")
            if 'metadata' in stages:
                print(f"      2. Metadata:    {stages['metadata'].get('time_ms', 0):.2f}ms")
            if 'embeddings' in stages:
                print(f"      3. Embeddings:  {stages['embeddings'].get('time_ms', 0):.2f}ms")
            if 'storage' in stages:
                print(f"      4. Storage:     {stages['storage'].get('time_ms', 0):.2f}ms")

            total_pipeline = result.get('processing_time_ms', 0)
            print(f"      ─────────────────────────────")
            print(f"      Total Pipeline: {total_pipeline:.2f}ms ({total_pipeline/1000:.2f}s)")

            chunks_count = result.get('chunks_created', 1)
            if chunks_count > 0:
                avg_per_chunk = total_pipeline / chunks_count
                print(f"      Avg/chunk:      {avg_per_chunk:.2f}ms")
                print(f"      Throughput:     {chunks_count / (total_pipeline/1000):.2f} chunks/sec")

        else:
            print(f"   ❌ Ingestion failed!")
            print(f"   HTTP Status: {response.status_code}")
            print(f"   Error: {response.text[:500]}")

            elapsed = record_timing("api_request_total", stage_start, {
                "status": "failed",
                "http_code": response.status_code,
                "error": response.text[:500]
            })

            sys.exit(1)

    except requests.exceptions.Timeout:
        print(f"   ❌ Request timeout after 300 seconds")
        record_timing("api_request_total", stage_start, {
            "status": "timeout"
        })
        sys.exit(1)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        record_timing("api_request_total", stage_start, {
            "status": "error",
            "error": str(e)
        })
        sys.exit(1)

    # ========================================================================
    # STAGE 7: Verify Collection Created
    # ========================================================================
    print_stage(7, "Verify Collection Created")
    stage_start = time.time()

    collections_after_ingest = utility.list_collections()
    collection_created = COLLECTION_NAME in collections_after_ingest

    elapsed = record_timing("verify_collection_created", stage_start, {
        "collections_total": len(collections_after_ingest),
        "target_created": collection_created,
        "collections": collections_after_ingest
    })

    if collection_created:
        print(f"   ✅ Collection '{COLLECTION_NAME}' created successfully")
    else:
        print(f"   ❌ Collection '{COLLECTION_NAME}' not found!")
        sys.exit(1)

    print_timing("Verification completed", elapsed)

    # ========================================================================
    # STAGE 8: Get Schema Information
    # ========================================================================
    print_stage(8, "Retrieve Collection Schema")
    stage_start = time.time()

    collection = Collection(COLLECTION_NAME)
    schema = collection.schema

    field_info = []
    for field in schema.fields:
        field_info.append({
            "name": field.name,
            "type": str(field.dtype),
            "description": field.description if hasattr(field, 'description') else ""
        })

    elapsed = record_timing("get_schema", stage_start, {
        "total_fields": len(schema.fields),
        "fields": field_info
    })

    print(f"   📋 Schema retrieved: {len(schema.fields)} fields")
    print(f"   📊 Fields:")
    for field in schema.fields[:5]:  # Show first 5
        print(f"      - {field.name}: {field.dtype}")
    if len(schema.fields) > 5:
        print(f"      ... and {len(schema.fields) - 5} more")

    print_timing("Schema retrieval completed", elapsed)

    # ========================================================================
    # STAGE 9: Flush Collection to Disk
    # ========================================================================
    print_stage(9, "Flush Collection to Disk")
    stage_start = time.time()

    count_before_flush = collection.num_entities
    collection.flush()
    count_after_flush = collection.num_entities

    elapsed = record_timing("flush_collection", stage_start, {
        "entities_before_flush": count_before_flush,
        "entities_after_flush": count_after_flush
    })

    print(f"   💾 Flushing collection...")
    print(f"   📊 Entities before flush: {count_before_flush}")
    print(f"   📊 Entities after flush: {count_after_flush}")
    print_timing("Flush completed", elapsed)

    # ========================================================================
    # STAGE 10: Load Collection into Memory
    # ========================================================================
    print_stage(10, "Load Collection into Query Engine")
    stage_start = time.time()

    collection.load()
    count_after_load = collection.num_entities

    elapsed = record_timing("load_collection", stage_start, {
        "entities_after_load": count_after_load
    })

    print(f"   📥 Loading collection...")
    print(f"   📊 Entities after load: {count_after_load}")
    print_timing("Load completed", elapsed)

    # ========================================================================
    # STAGE 11: Query and Verify Data
    # ========================================================================
    print_stage(11, "Query and Verify Data Quality")
    stage_start = time.time()

    results = collection.query(
        expr="chunk_index >= 0",
        output_fields=["id", "document_id", "chunk_index", "text",
                      "keywords", "topics", "questions", "summary",
                      "semantic_keywords", "entity_relationships", "attributes"],
        limit=100
    )

    # Analyze metadata quality
    metadata_fields = ['keywords', 'topics', 'questions', 'summary',
                      'semantic_keywords', 'entity_relationships', 'attributes']

    field_stats = {}
    for field in metadata_fields:
        populated = sum(1 for r in results if r.get(field, '').strip() != '')
        total = len(results)
        percentage = (populated / total) * 100 if total > 0 else 0
        field_stats[field] = {
            "populated": populated,
            "total": total,
            "percentage": percentage
        }

    elapsed = record_timing("query_and_verify", stage_start, {
        "total_chunks": len(results),
        "metadata_quality": field_stats
    })

    print(f"   🔍 Queried {len(results)} chunks")
    print(f"\n   📊 Metadata Quality:")
    for field, stats in field_stats.items():
        icon = '✅' if stats['percentage'] == 100 else ('⚠️' if stats['percentage'] > 50 else '❌')
        print(f"      {icon} {field:<22} {stats['populated']}/{stats['total']} ({stats['percentage']:.1f}%)")

    print_timing("Query completed", elapsed)

    # Show sample data
    if results:
        print(f"\n   📄 Sample Data (first chunk):")
        sample = results[0]
        print(f"      ID: {sample['id']}")
        print(f"      Keywords: {sample.get('keywords', '')[:60]}...")
        print(f"      Topics: {sample.get('topics', '')[:60]}...")
        print(f"      Summary: {sample.get('summary', '')[:80]}...")

    collection.release()

    # ========================================================================
    # STAGE 12: Calculate Total Time
    # ========================================================================
    test_end = time.time()
    total_elapsed = (test_end - test_start) * 1000

    timings["test_completed_at"] = datetime.now().isoformat()
    timings["total_test_duration_ms"] = total_elapsed
    timings["total_test_duration_seconds"] = total_elapsed / 1000

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print_header("✅ BENCHMARK COMPLETE")

    print(f"\n📊 TIMING SUMMARY:")
    print(f"{'─' * 100}")

    # Sort stages by order
    stage_order = [
        "milvus_connection",
        "check_existing_collection",
        "drop_collection",
        "verify_drop",
        "read_document",
        "api_request_total",
        "verify_collection_created",
        "get_schema",
        "flush_collection",
        "load_collection",
        "query_and_verify"
    ]

    for stage_key in stage_order:
        if stage_key in timings["stages"]:
            stage = timings["stages"][stage_key]
            duration_ms = stage["duration_ms"]
            duration_s = stage["duration_seconds"]
            percentage = (duration_ms / total_elapsed) * 100

            # Format stage name
            stage_name = stage_key.replace('_', ' ').title()

            print(f"  {stage_name:<35} {duration_ms:>10.2f}ms ({duration_s:>6.2f}s) [{percentage:>5.1f}%]")

    print(f"{'─' * 100}")
    print(f"  {'TOTAL TEST DURATION':<35} {total_elapsed:>10.2f}ms ({total_elapsed/1000:>6.2f}s) [100.0%]")
    print(f"{'─' * 100}")

    # Pipeline breakdown
    if "api_request_total" in timings["stages"] and "pipeline_response" in timings["stages"]["api_request_total"]:
        pipeline = timings["stages"]["api_request_total"]["pipeline_response"]
        print(f"\n📊 PIPELINE STAGE BREAKDOWN:")
        print(f"{'─' * 100}")
        print(f"  {'Chunking':<35} {pipeline['chunking_ms']:>10.2f}ms")
        print(f"  {'Metadata Extraction':<35} {pipeline['metadata_ms']:>10.2f}ms")
        print(f"  {'Embeddings Generation':<35} {pipeline['embeddings_ms']:>10.2f}ms")
        print(f"  {'Storage (Milvus Write)':<35} {pipeline['storage_ms']:>10.2f}ms")
        print(f"{'─' * 100}")
        print(f"  {'Total Pipeline':<35} {pipeline['total_pipeline_ms']:>10.2f}ms")
        print(f"{'─' * 100}")

    # Save detailed log
    log_file = Path("/Users/rakesh/Desktop/crawlenginepro.mindmate247.com/benchmark_detailed_log.json")
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(timings, f, indent=2)

    print(f"\n💾 Detailed timing log saved to:")
    print(f"   {log_file}")

    print(f"\n🌐 View data in Milvus UI:")
    print(f"   http://localhost:3000/#/databases/default/{COLLECTION_NAME}/data")

    print("\n" + "=" * 100)

    connections.disconnect('default')

if __name__ == "__main__":
    main()
