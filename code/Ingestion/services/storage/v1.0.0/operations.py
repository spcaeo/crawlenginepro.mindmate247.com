"""
Milvus Storage Service v1.0.0 - CRUD Operations
Complete implementation of Create, Read, Update, Delete operations
"""

from pymilvus import connections, Collection, utility
from typing import List, Dict, Any, Optional
import time
import traceback
from datetime import datetime

import config
import schema as milvus_schema
from models import ChunkData

# ============================================================================
# Connection Management
# ============================================================================

def connect_to_milvus():
    """Connect to Milvus server"""
    try:
        connections.connect(
            alias="default",
            host=config.MILVUS_HOST,
            port=config.MILVUS_PORT,
            user=config.MILVUS_USER,
            password=config.MILVUS_PASSWORD,
            timeout=config.REQUEST_TIMEOUT
        )
        print(f"✓ Connected to Milvus at {config.MILVUS_HOST}:{config.MILVUS_PORT}")
        return True
    except Exception as e:
        print(f"✗ Failed to connect to Milvus: {e}")
        return False


def disconnect_from_milvus():
    """Disconnect from Milvus"""
    try:
        connections.disconnect(alias="default")
        print("✓ Disconnected from Milvus")
    except Exception as e:
        print(f"⚠ Warning during disconnect: {e}")


def check_connection() -> bool:
    """Check if Milvus connection is alive"""
    try:
        collections = utility.list_collections()
        return True
    except Exception as e:
        print(f"✗ Milvus connection check failed: {e}")
        return False


# ============================================================================
# Collection Management
# ============================================================================

def create_collection(
    collection_name: str,
    dimension: int = None,
    source_document: str = None,
    preset_name: str = None,
    metadata_model_used: str = None,
    embedding_model_used: str = None
) -> Dict[str, Any]:
    """
    Create new collection with v1.0.0 schema

    Args:
        collection_name: Name of collection to create
        dimension: Dense vector dimension (if None, uses config.DEFAULT_DIMENSION from model registry)
        source_document: Optional source document path/name for description
        preset_name: Optional preset name for description

    Returns:
        Dict with success status and details
    """
    try:
        # Use config default if not specified
        if dimension is None:
            dimension = config.DEFAULT_DIMENSION

        # Check if collection exists
        if utility.has_collection(collection_name):
            return {
                "success": False,
                "error": "Collection already exists",
                "collection_name": collection_name
            }

        # Create schema with rich description
        collection_schema = milvus_schema.create_storage_schema_v1(
            dimension=dimension,
            source_document=source_document,
            preset_name=preset_name,
            metadata_model_used=metadata_model_used,
            embedding_model_used=embedding_model_used
        )

        # Create collection with partition key configuration
        collection = Collection(
            name=collection_name,
            schema=collection_schema,
            using='default',
            num_partitions=config.NUM_PARTITIONS  # 256 partitions for optimal retrieval
        )

        print(f"✓ Collection '{collection_name}' created with {len(collection_schema.fields)} fields ({config.NUM_PARTITIONS} partitions)")

        # Create indexes
        milvus_schema.create_indexes(collection)

        # Load collection
        collection.load()
        print(f"✓ Collection '{collection_name}' loaded")

        return {
            "success": True,
            "collection_name": collection_name,
            "fields_count": len(collection_schema.fields),
            "dimension": dimension
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "collection_name": collection_name
        }


def get_collection(collection_name: str) -> Optional[Collection]:
    """Get collection object"""
    try:
        if not utility.has_collection(collection_name):
            return None
        return Collection(name=collection_name)
    except Exception as e:
        print(f"✗ Failed to get collection '{collection_name}': {e}")
        return None


def delete_collection(collection_name: str) -> Dict[str, Any]:
    """Delete collection"""
    try:
        if not utility.has_collection(collection_name):
            return {
                "success": False,
                "error": "Collection does not exist",
                "collection_name": collection_name
            }

        utility.drop_collection(collection_name)
        print(f"✓ Collection '{collection_name}' deleted")

        return {
            "success": True,
            "collection_name": collection_name,
            "message": "Collection deleted successfully"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "collection_name": collection_name
        }


def get_collection_info(collection_name: str) -> Dict[str, Any]:
    """Get collection information"""
    try:
        if not utility.has_collection(collection_name):
            return {
                "success": False,
                "error": "Collection does not exist",
                "collection_name": collection_name
            }

        collection = Collection(name=collection_name)

        # Get schema
        schema_dict = {
            "fields": [
                {
                    "name": field.name,
                    "type": str(field.dtype),
                    "params": field.params
                }
                for field in collection.schema.fields
            ]
        }

        # Get indexes
        indexes = []
        try:
            index_info = collection.indexes
            for idx in index_info:
                indexes.append({
                    "field": idx.field_name,
                    "name": idx.index_name,
                    "params": idx.params
                })
        except Exception:
            indexes = []

        # Get count
        num_entities = collection.num_entities

        return {
            "success": True,
            "collection_name": collection_name,
            "schema": schema_dict,
            "num_entities": num_entities,
            "indexes": indexes
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "collection_name": collection_name
        }


# ============================================================================
# INSERT Operation
# ============================================================================

def insert_chunks(
    collection_name: str,
    chunks: List[ChunkData],
    create_if_not_exists: bool = True,
    source_document: str = None,
    preset_name: str = None,
    metadata_model_used: str = None,
    embedding_model_used: str = None
) -> Dict[str, Any]:
    """
    Insert chunks into collection

    Args:
        collection_name: Target collection name
        chunks: List of ChunkData objects
        create_if_not_exists: Create collection if it doesn't exist
        source_document: Optional source document path/name for collection description
        preset_name: Optional preset name for collection description

    Returns:
        Dict with success status, inserted_count, chunk_ids
    """
    start_time = time.time()

    try:
        # Check/create collection
        if not utility.has_collection(collection_name):
            if create_if_not_exists:
                # Detect dimension from first chunk's dense_vector
                dimension = None
                if chunks and chunks[0].dense_vector:
                    dimension = len(chunks[0].dense_vector)
                    print(f"✓ Detected vector dimension: {dimension} from chunk data")

                # Extract document_id from first chunk if source_document not provided
                if not source_document and chunks and chunks[0].document_id:
                    source_document = chunks[0].document_id

                result = create_collection(
                    collection_name=collection_name,
                    dimension=dimension,
                    source_document=source_document,
                    preset_name=preset_name,
                    metadata_model_used=metadata_model_used,
                    embedding_model_used=embedding_model_used
                )
                if not result["success"]:
                    return result
            else:
                return {
                    "success": False,
                    "error": "Collection does not exist",
                    "collection_name": collection_name
                }

        # Get collection
        collection = Collection(name=collection_name)

        # Prepare data (convert chunks to column format)
        data = prepare_insert_data(chunks)

        # Insert
        insert_result = collection.insert(data)

        # Optional flush to ensure data is immediately visible (controlled by AUTO_FLUSH_AFTER_INSERT config)
        if config.AUTO_FLUSH_AFTER_INSERT:
            flush_start = time.time()
            collection.flush()
            flush_time = (time.time() - flush_start) * 1000
            print(f"✓ Flushed collection '{collection_name}' to disk ({flush_time:.2f}ms)")
        else:
            print(f"⏭️  Skipped flush (AUTO_FLUSH_AFTER_INSERT=false) - data will auto-flush within 1s")

        processing_time = (time.time() - start_time) * 1000

        print(f"✓ Inserted {len(chunks)} chunks into '{collection_name}' ({processing_time:.2f}ms)")

        return {
            "success": True,
            "inserted_count": len(chunks),
            "chunk_ids": [chunk.id for chunk in chunks],
            "collection_name": collection_name,
            "processing_time_ms": processing_time
        }

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        error_details = traceback.format_exc()
        print(f"✗ Insert failed: {e}")
        print(f"Error details:\n{error_details}")
        return {
            "success": False,
            "error": f"{str(e)} | Details: {error_details[:500]}",
            "collection_name": collection_name,
            "processing_time_ms": processing_time
        }


def prepare_insert_data(chunks: List[ChunkData], dimension: int = None) -> List[List[Any]]:
    """
    Convert list of ChunkData to column format for Milvus insert

    Milvus requires data in column format: [[id1, id2, ...], [text1, text2, ...], ...]

    Args:
        chunks: List of ChunkData objects
        dimension: Dense vector dimension (if None, uses config.DEFAULT_DIMENSION from model registry)
    """
    # Use config default if not specified
    if dimension is None:
        dimension = config.DEFAULT_DIMENSION
    # Get all field names from schema
    all_fields = milvus_schema.get_all_field_names()

    # Initialize columns
    data = {field: [] for field in all_fields}

    # Populate columns
    for chunk in chunks:
        chunk_dict = chunk.model_dump()

        for field in all_fields:
            if field in chunk_dict:
                value = chunk_dict[field]
                data[field].append(value if value is not None else get_default_value(field, dimension))
            else:
                data[field].append(get_default_value(field, dimension))

    # Convert to list of lists (ordered by schema)
    # Debug: Check for empty fields
    for field in all_fields:
        if len(data[field]) == 0:
            print(f"⚠️  WARNING: Field '{field}' has no data! Expected {len(chunks)} values.")
        elif len(data[field]) != len(chunks):
            print(f"⚠️  WARNING: Field '{field}' has {len(data[field])} values, expected {len(chunks)}")

    return [data[field] for field in all_fields]


def get_default_value(field_name: str, dimension: int = None) -> Any:
    """
    Get default value for field based on type

    Args:
        field_name: Name of the field
        dimension: Dense vector dimension (if None, uses config.DEFAULT_DIMENSION from model registry)
    """
    # Use config default if not specified
    if dimension is None:
        dimension = config.DEFAULT_DIMENSION
    if field_name == "dense_vector":
        # Return zero vector of correct dimension
        return [0.0] * dimension
    elif field_name in ["price", "amount", "tax_amount"]:
        return 0.0
    elif field_name in ["year", "chunk_index", "char_count", "token_count"]:
        return 0
    else:
        return ""


# ============================================================================
# UPDATE Operation
# ============================================================================

def update_chunks(
    collection_name: str,
    filter_expr: str,
    updates: Dict[str, Any],
    tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update chunks matching filter

    NOTE: Milvus doesn't support direct UPDATE. We must:
    1. Query matching entities
    2. Modify fields
    3. Delete old entities
    4. Insert updated entities

    Args:
        collection_name: Target collection
        filter_expr: Filter expression (e.g., 'id in ["chunk1", "chunk2"]')
        updates: Dict of fields to update
        tenant_id: Optional tenant filter for multi-tenancy

    Returns:
        Dict with success status and updated_count
    """
    start_time = time.time()

    try:
        collection = get_collection(collection_name)
        if not collection:
            return {"success": False, "error": "Collection not found"}

        # Add tenant filter if provided
        if tenant_id:
            filter_expr = f"({filter_expr}) and tenant_id == '{tenant_id}'"

        # Query entities to update
        collection.load()
        results = collection.query(
            expr=filter_expr,
            output_fields=["*"]
        )

        if not results:
            return {
                "success": True,
                "updated_count": 0,
                "message": "No entities matched filter",
                "processing_time_ms": (time.time() - start_time) * 1000
            }

        # Update fields
        updated_at = datetime.utcnow().isoformat()
        for entity in results:
            for field, value in updates.items():
                entity[field] = value
            entity["updated_at"] = updated_at

        # Delete old entities
        ids_to_delete = [entity["id"] for entity in results]
        collection.delete(f"id in {ids_to_delete}")

        # Insert updated entities (convert back to ChunkData format)
        chunks = [ChunkData(**entity) for entity in results]
        insert_result = insert_chunks(collection_name, chunks, create_if_not_exists=False)

        if not insert_result["success"]:
            return insert_result

        processing_time = (time.time() - start_time) * 1000

        return {
            "success": True,
            "updated_count": len(results),
            "collection_name": collection_name,
            "processing_time_ms": processing_time
        }

    except Exception as e:
        error_details = traceback.format_exc()
        print(f"✗ Update failed: {e}")
        print(f"Error details:\n{error_details}")
        return {
            "success": False,
            "error": f"{str(e)} | Details: {error_details[:500]}",
            "collection_name": collection_name,
            "processing_time_ms": (time.time() - start_time) * 1000
        }


# ============================================================================
# DELETE Operation
# ============================================================================

def delete_chunks(
    collection_name: str,
    filter_expr: str,
    tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete chunks matching filter

    Args:
        collection_name: Target collection
        filter_expr: Filter expression (e.g., 'document_id == "doc123"')
        tenant_id: Optional tenant filter for multi-tenancy

    Returns:
        Dict with success status and deleted_count
    """
    start_time = time.time()

    try:
        collection = get_collection(collection_name)
        if not collection:
            return {"success": False, "error": "Collection not found"}

        # Add tenant filter if provided
        if tenant_id:
            filter_expr = f"({filter_expr}) and tenant_id == '{tenant_id}'"

        # Query to count before delete
        collection.load()
        results = collection.query(
            expr=filter_expr,
            output_fields=["id"],
            limit=10000
        )
        count_before = len(results)

        # Delete
        collection.delete(filter_expr)
        collection.flush()

        processing_time = (time.time() - start_time) * 1000

        print(f"✓ Deleted {count_before} chunks from '{collection_name}' ({processing_time:.2f}ms)")

        return {
            "success": True,
            "deleted_count": count_before,
            "collection_name": collection_name,
            "processing_time_ms": processing_time
        }

    except Exception as e:
        error_details = traceback.format_exc()
        print(f"✗ Delete failed: {e}")
        print(f"Error details:\n{error_details}")
        return {
            "success": False,
            "error": f"{str(e)} | Details: {error_details[:500]}",
            "collection_name": collection_name,
            "processing_time_ms": (time.time() - start_time) * 1000
        }


# ============================================================================
# SEARCH Operation
# ============================================================================

def hybrid_search(
    collection_name: str,
    query_dense: List[float] = None,
    query_sparse: Dict[int, float] = None,
    filter_expr: str = None,
    tenant_id: Optional[str] = None,
    limit: int = 20,
    output_fields: List[str] = None,
    search_mode: str = "dense"
) -> Dict[str, Any]:
    """
    Hybrid search (dense vector search with optional filtering)
    
    Args:
        collection_name: Target collection
        query_dense: Dense query vector
        query_sparse: Sparse query vector (not used in v1.0.0)
        filter_expr: Optional filter expression
        tenant_id: Optional tenant filter
        limit: Number of results
        output_fields: Fields to return
        search_mode: "dense", "sparse", or "hybrid" (only dense supported in v1.0.0)
    
    Returns:
        Dict with success status and search results
    """
    start_time = time.time()
    
    try:
        collection = get_collection(collection_name)
        if not collection:
            return {"success": False, "error": "Collection not found"}
        
        # Load collection
        collection.load()
        
        # Add tenant filter if provided
        if tenant_id and filter_expr:
            filter_expr = f"({filter_expr}) and tenant_id == '{tenant_id}'"
        elif tenant_id:
            filter_expr = f"tenant_id == '{tenant_id}'"
        
        # Default output fields if not specified
        if not output_fields:
            output_fields = ["id", "text", "document_id", "chunk_index", 
                           "keywords", "topics", "questions", "summary"]
        
        # Perform dense vector search
        if search_mode in ["dense", "hybrid"] and query_dense:
            search_params = {"metric_type": "IP", "params": {}}
            
            results = collection.search(
                data=[query_dense],
                anns_field="dense_vector",
                param=search_params,
                limit=limit,
                expr=filter_expr,
                output_fields=output_fields
            )
            
            # Convert results to list of dicts
            formatted_results = []
            for hits in results:
                for hit in hits:
                    result_dict = {
                        "id": hit.entity.get("id"),
                        "score": hit.score,
                        "text": hit.entity.get("text"),
                        "document_id": hit.entity.get("document_id"),
                        "chunk_index": hit.entity.get("chunk_index"),
                        "keywords": hit.entity.get("keywords") or "",
                        "topics": hit.entity.get("topics") or "",
                        "questions": hit.entity.get("questions") or "",
                        "summary": hit.entity.get("summary") or ""
                    }
                    formatted_results.append(result_dict)
            
            processing_time = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "results": formatted_results,
                "total_results": len(formatted_results),
                "collection_name": collection_name,
                "search_mode": "dense",
                "processing_time_ms": processing_time
            }
        else:
            return {
                "success": False,
                "error": "No query vector provided or unsupported search mode"
            }
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"✗ Search failed: {e}")
        print(f"Error details:\n{error_details}")
        return {
            "success": False,
            "error": f"{str(e)} | Details: {error_details[:500]}",
            "collection_name": collection_name,
            "processing_time_ms": (time.time() - start_time) * 1000
        }
