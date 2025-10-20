#!/usr/bin/env python3
"""
Detailed Ingestion Test Script with Performance Tracking
Ingests ComprehensiveTestDocument.md and tracks all metrics
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
COLLECTION_NAME = "test_comprehensive_detailed"
TENANT_ID = "default"
INGESTION_API_URL = "http://localhost:8070"  # Development environment
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"

# Performance tracking
performance_log = {
    "test_started_at": datetime.now().isoformat(),
    "document_path": TEST_DOCUMENT,
    "collection_name": COLLECTION_NAME,
    "stages": {}
}

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_stage(text):
    """Print stage marker"""
    print(f"\n{'─' * 80}")
    print(f"📍 {text}")
    print(f"{'─' * 80}")

def check_service_health():
    """Check if ingestion services are running"""
    print_stage("STAGE 1: Service Health Check")

    services = {
        "Main Ingestion API": f"{INGESTION_API_URL}/health",
        "Chunking Service": "http://localhost:8071/health",
        "Metadata Service": "http://localhost:8072/health",
        "Embeddings Service": "http://localhost:8073/health",
        "Storage Service": "http://localhost:8074/health",
        "LLM Gateway": "http://localhost:8075/health"
    }

    all_healthy = True
    service_status = {}

    for name, url in services.items():
        try:
            start = time.time()
            response = requests.get(url, timeout=3)
            elapsed = (time.time() - start) * 1000

            if response.status_code == 200:
                data = response.json()
                version = data.get("version", "unknown")
                status = data.get("status", "unknown")
                print(f"  ✓ {name:<25} - {status} (v{version}) [{elapsed:.0f}ms]")
                service_status[name] = {"status": "healthy", "version": version, "response_time_ms": elapsed}
            else:
                print(f"  ✗ {name:<25} - HTTP {response.status_code}")
                service_status[name] = {"status": "unhealthy", "http_code": response.status_code}
                all_healthy = False
        except requests.exceptions.ConnectionError:
            print(f"  ✗ {name:<25} - NOT RUNNING (connection refused)")
            service_status[name] = {"status": "not_running"}
            all_healthy = False
        except requests.exceptions.Timeout:
            print(f"  ✗ {name:<25} - TIMEOUT")
            service_status[name] = {"status": "timeout"}
            all_healthy = False
        except Exception as e:
            print(f"  ✗ {name:<25} - ERROR: {str(e)[:50]}")
            service_status[name] = {"status": "error", "error": str(e)}
            all_healthy = False

    performance_log["stages"]["service_health"] = service_status

    if not all_healthy:
        print("\n❌ ERROR: Not all services are running!")
        print("\n💡 To start services on your remote server:")
        print("   1. SSH into server: ssh -i ~/reku631_nebius reku631@89.169.108.8")
        print("   2. Navigate to service directories and start each service")
        print("   3. Use screen or tmux to keep services running")
        return False

    print("\n✅ All services are healthy and ready!")
    return True

def check_milvus_connection():
    """Check Milvus connection"""
    print_stage("STAGE 2: Milvus Connection Check")

    try:
        start = time.time()
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        elapsed = (time.time() - start) * 1000

        print(f"  ✓ Connected to Milvus at {MILVUS_HOST}:{MILVUS_PORT} [{elapsed:.0f}ms]")

        # List collections
        collections = utility.list_collections()
        print(f"  ✓ Current collections: {len(collections)}")
        for coll in collections:
            print(f"     - {coll}")

        performance_log["stages"]["milvus_connection"] = {
            "status": "connected",
            "connection_time_ms": elapsed,
            "existing_collections": collections
        }

        connections.disconnect('default')
        return True
    except Exception as e:
        print(f"  ✗ Failed to connect to Milvus: {e}")
        performance_log["stages"]["milvus_connection"] = {
            "status": "failed",
            "error": str(e)
        }
        return False

def read_document():
    """Read test document"""
    print_stage("STAGE 3: Document Loading")

    doc_path = Path(TEST_DOCUMENT)

    if not doc_path.exists():
        print(f"  ✗ Document not found: {doc_path}")
        return None

    start = time.time()
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    elapsed = (time.time() - start) * 1000

    # Calculate statistics
    char_count = len(content)
    line_count = content.count('\n')
    word_count = len(content.split())

    # Estimate token count (rough: ~4 chars per token)
    est_tokens = char_count // 4

    print(f"  ✓ Document loaded: {doc_path.name}")
    print(f"  📊 Statistics:")
    print(f"     - Characters: {char_count:,}")
    print(f"     - Lines: {line_count:,}")
    print(f"     - Words: {word_count:,}")
    print(f"     - Estimated tokens: {est_tokens:,}")
    print(f"     - Read time: {elapsed:.2f}ms")

    # Count sections (markdown headers)
    section_count = content.count('\n## ')
    subsection_count = content.count('\n### ')
    print(f"     - Sections (##): {section_count}")
    print(f"     - Subsections (###): {subsection_count}")

    performance_log["stages"]["document_loading"] = {
        "status": "success",
        "file_path": str(doc_path),
        "char_count": char_count,
        "line_count": line_count,
        "word_count": word_count,
        "estimated_tokens": est_tokens,
        "section_count": section_count,
        "subsection_count": subsection_count,
        "read_time_ms": elapsed
    }

    return content

def ingest_document(content):
    """Ingest document with detailed tracking"""
    print_stage("STAGE 4: Document Ingestion")

    # Prepare payload
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

    print(f"  📤 Sending ingestion request...")
    print(f"     - Document ID: {payload['document_id']}")
    print(f"     - Collection: {payload['collection_name']}")
    print(f"     - Chunking: {payload['chunking_method']} (size={payload['max_chunk_size']}, overlap={payload['chunk_overlap']})")
    print(f"     - Metadata: enabled (keywords={payload['keywords_count']}, topics={payload['topics_count']}, questions={payload['questions_count']})")
    print(f"     - Embeddings: {payload['embedding_model']}")

    try:
        start_time = time.time()
        response = requests.post(
            f"{INGESTION_API_URL}/v1/ingest",
            json=payload,
            timeout=300  # 5 minutes timeout
        )
        total_elapsed = (time.time() - start_time) * 1000

        if response.status_code == 200:
            result = response.json()

            print(f"\n  ✅ INGESTION SUCCESSFUL!")
            print(f"\n  📊 Results Summary:")
            print(f"     - Document ID: {result.get('document_id')}")
            print(f"     - Collection: {result.get('collection_name')}")
            print(f"     - Tenant ID: {result.get('tenant_id')}")
            print(f"     - Chunks Created: {result.get('chunks_created')}")
            print(f"     - Chunks Inserted: {result.get('chunks_inserted')}")
            print(f"     - Total Pipeline Time: {result.get('processing_time_ms', 0):.2f}ms ({result.get('processing_time_ms', 0)/1000:.2f}s)")
            print(f"     - Total Request Time: {total_elapsed:.2f}ms ({total_elapsed/1000:.2f}s)")

            # Detailed stage breakdown
            stages = result.get('stages', {})
            print(f"\n  ⏱️  Stage-by-Stage Performance:")

            if 'chunking' in stages:
                chunking = stages['chunking']
                print(f"     1. Chunking:")
                print(f"        - Time: {chunking.get('time_ms', 0):.2f}ms")
                print(f"        - Chunks: {chunking.get('chunks_created', 0)}")

            if 'metadata' in stages:
                metadata = stages['metadata']
                print(f"     2. Metadata Extraction:")
                print(f"        - Time: {metadata.get('time_ms', 0):.2f}ms")
                print(f"        - Generated: {metadata.get('generated', False)}")

            if 'embeddings' in stages:
                embeddings = stages['embeddings']
                print(f"     3. Embeddings Generation:")
                print(f"        - Time: {embeddings.get('time_ms', 0):.2f}ms")
                print(f"        - Model: {embeddings.get('model', 'unknown')}")
                print(f"        - Generated: {embeddings.get('generated', False)}")

            if 'storage' in stages:
                storage = stages['storage']
                print(f"     4. Storage (Milvus):")
                print(f"        - Time: {storage.get('time_ms', 0):.2f}ms")
                print(f"        - Stored: {storage.get('stored', False)}")
                print(f"        - Collection: {storage.get('collection_name', 'unknown')}")

            # Calculate per-chunk averages
            chunks_count = result.get('chunks_created', 1)
            total_time = result.get('processing_time_ms', 0)
            avg_per_chunk = total_time / chunks_count if chunks_count > 0 else 0

            print(f"\n  📈 Performance Metrics:")
            print(f"     - Average time per chunk: {avg_per_chunk:.2f}ms")
            print(f"     - Throughput: {chunks_count / (total_time/1000):.2f} chunks/second")

            performance_log["stages"]["ingestion"] = {
                "status": "success",
                "total_request_time_ms": total_elapsed,
                "pipeline_time_ms": result.get('processing_time_ms', 0),
                "chunks_created": result.get('chunks_created'),
                "chunks_inserted": result.get('chunks_inserted'),
                "avg_time_per_chunk_ms": avg_per_chunk,
                "throughput_chunks_per_second": chunks_count / (total_time/1000) if total_time > 0 else 0,
                "stages": stages,
                "full_response": result
            }

            return True
        else:
            print(f"\n  ❌ INGESTION FAILED!")
            print(f"     - HTTP Status: {response.status_code}")
            print(f"     - Error: {response.text[:500]}")

            performance_log["stages"]["ingestion"] = {
                "status": "failed",
                "http_code": response.status_code,
                "error": response.text[:500],
                "total_request_time_ms": total_elapsed
            }
            return False

    except requests.exceptions.Timeout:
        print(f"\n  ❌ REQUEST TIMEOUT after 300 seconds!")
        performance_log["stages"]["ingestion"] = {
            "status": "timeout",
            "timeout_seconds": 300
        }
        return False
    except Exception as e:
        print(f"\n  ❌ ERROR: {str(e)}")
        performance_log["stages"]["ingestion"] = {
            "status": "error",
            "error": str(e)
        }
        return False

def verify_data_in_milvus():
    """Verify data was stored correctly in Milvus"""
    print_stage("STAGE 5: Data Verification in Milvus")

    try:
        # Connect
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)

        # Check collection exists
        collections = utility.list_collections()
        print(f"  📊 Collections in database: {collections}")

        if COLLECTION_NAME not in collections:
            print(f"  ✗ Collection '{COLLECTION_NAME}' not found!")
            connections.disconnect('default')
            return False

        # Load collection
        collection = Collection(COLLECTION_NAME)
        collection.load()

        # Get entity count
        count = collection.num_entities
        print(f"  ✓ Collection '{COLLECTION_NAME}' found")
        print(f"  ✓ Total entities: {count}")

        if count == 0:
            print(f"  ✗ Collection is empty!")
            collection.release()
            connections.disconnect('default')
            return False

        # Query sample data (first 3 chunks)
        print(f"\n  🔍 Sampling first 3 chunks...")
        results = collection.query(
            expr="chunk_index >= 0",
            output_fields=["id", "document_id", "chunk_index", "text", "char_count", "token_count",
                          "keywords", "topics", "questions", "summary",
                          "semantic_keywords", "entity_relationships", "attributes"],
            limit=3
        )

        verification_results = {
            "collection_name": COLLECTION_NAME,
            "total_entities": count,
            "sample_chunks": []
        }

        for i, chunk in enumerate(results, 1):
            print(f"\n  {'─' * 76}")
            print(f"  📄 Chunk {i}/{len(results)}: {chunk['id']}")
            print(f"  {'─' * 76}")
            print(f"     Document ID: {chunk['document_id']}")
            print(f"     Chunk Index: {chunk['chunk_index']}")
            print(f"     Char Count: {chunk['char_count']}")
            print(f"     Token Count: {chunk['token_count']}")
            print(f"     Text Preview: {chunk['text'][:150]}...")

            print(f"\n     🏷️  Metadata Fields:")

            # Check each metadata field
            metadata_status = {}
            for field in ['keywords', 'topics', 'questions', 'summary', 'semantic_keywords', 'entity_relationships', 'attributes']:
                value = chunk.get(field, '')
                is_empty = not value or value.strip() == ''
                status = "❌ EMPTY" if is_empty else "✅ POPULATED"
                print(f"        {field:<22} {status}")
                if not is_empty:
                    # Show first 80 chars
                    preview = value[:80] + "..." if len(value) > 80 else value
                    print(f"        {' ' * 22} → {preview}")

                metadata_status[field] = {
                    "populated": not is_empty,
                    "length": len(value),
                    "preview": value[:100] if not is_empty else None
                }

            verification_results["sample_chunks"].append({
                "id": chunk['id'],
                "chunk_index": chunk['chunk_index'],
                "char_count": chunk['char_count'],
                "token_count": chunk['token_count'],
                "text_preview": chunk['text'][:150],
                "metadata_status": metadata_status
            })

        # Count empty vs populated metadata
        print(f"\n  📊 Metadata Quality Analysis (across {len(results)} sample chunks):")

        field_stats = {}
        for field in ['keywords', 'topics', 'questions', 'summary', 'semantic_keywords', 'entity_relationships', 'attributes']:
            populated_count = sum(1 for chunk in results if chunk.get(field, '').strip() != '')
            empty_count = len(results) - populated_count
            percentage = (populated_count / len(results)) * 100

            status_icon = "✅" if percentage == 100 else ("⚠️" if percentage > 0 else "❌")
            print(f"     {status_icon} {field:<22} {populated_count}/{len(results)} populated ({percentage:.0f}%)")

            field_stats[field] = {
                "populated_count": populated_count,
                "empty_count": empty_count,
                "percentage": percentage
            }

        verification_results["metadata_quality"] = field_stats
        performance_log["stages"]["verification"] = verification_results

        collection.release()
        connections.disconnect('default')

        return True

    except Exception as e:
        print(f"  ✗ Verification failed: {e}")
        performance_log["stages"]["verification"] = {
            "status": "failed",
            "error": str(e)
        }
        connections.disconnect('default')
        return False

def save_performance_log():
    """Save detailed performance log to file"""
    print_stage("STAGE 6: Saving Performance Log")

    performance_log["test_completed_at"] = datetime.now().isoformat()

    log_file = Path("/Users/rakesh/Desktop/crawlenginepro.mindmate247.com/ingestion_performance_log.json")

    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(performance_log, f, indent=2)

    print(f"  ✓ Performance log saved to: {log_file}")
    print(f"  📄 File size: {log_file.stat().st_size:,} bytes")

    return log_file

def main():
    """Main test execution"""
    print_header("🚀 DETAILED INGESTION TEST - ComprehensiveTestDocument.md")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    overall_start = time.time()

    # Stage 1: Check services
    if not check_service_health():
        print("\n❌ Test aborted: Services not ready")
        sys.exit(1)

    # Stage 2: Check Milvus
    if not check_milvus_connection():
        print("\n❌ Test aborted: Milvus not accessible")
        sys.exit(1)

    # Stage 3: Load document
    content = read_document()
    if not content:
        print("\n❌ Test aborted: Could not load document")
        sys.exit(1)

    # Stage 4: Ingest
    success = ingest_document(content)
    if not success:
        print("\n❌ Test failed: Ingestion error")
        # Save log even on failure
        log_file = save_performance_log()
        print(f"\n📊 Performance log saved despite failure: {log_file}")
        sys.exit(1)

    # Stage 5: Verify
    verify_success = verify_data_in_milvus()

    # Stage 6: Save log
    log_file = save_performance_log()

    overall_elapsed = (time.time() - overall_start)

    # Final summary
    print_header("✅ TEST COMPLETED SUCCESSFULLY")
    print(f"\n  Total test duration: {overall_elapsed:.2f}s")
    print(f"  Performance log: {log_file}")
    print(f"  Collection name: {COLLECTION_NAME}")

    if verify_success:
        print(f"\n  🎉 All stages completed successfully!")
        print(f"  💾 Data is now available in Milvus")
        print(f"  🌐 View in UI: http://localhost:3000/#/databases/default/{COLLECTION_NAME}/data")
    else:
        print(f"\n  ⚠️  Ingestion succeeded but verification had issues")
        print(f"     Check the performance log for details")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
