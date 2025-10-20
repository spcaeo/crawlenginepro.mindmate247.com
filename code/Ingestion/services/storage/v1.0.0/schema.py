"""
Milvus Storage Service v1.0.0 - Minimal Schema Definition
17-field schema with multi-tenancy support (base metadata only)
"""

from pymilvus import CollectionSchema, FieldSchema, DataType
from typing import List, Optional
from datetime import datetime
import config
import sys
from pathlib import Path

# Add shared directory to path for model registry
SHARED_DIR = Path(__file__).resolve().parents[4] / "code" / "shared"
sys.path.insert(0, str(SHARED_DIR))

try:
    from model_registry import (
        ACTIVE_PRESET,
        get_embedding_model,
        get_embedding_dimension,
        get_model_provider
    )
except ImportError:
    # Fallback if model_registry not available
    ACTIVE_PRESET = None

def generate_collection_description(
    dimension: int,
    source_document: Optional[str] = None,
    preset_name: Optional[str] = None,
    metadata_model_used: Optional[str] = None,
    embedding_model_used: Optional[str] = None
) -> str:
    """
    Generate rich collection description with model metadata

    Args:
        dimension: Vector dimension
        source_document: Optional source document path/name
        preset_name: Optional preset name override
        metadata_model_used: Optional actual metadata model used (overrides preset)
        embedding_model_used: Optional actual embedding model used (overrides preset)

    Returns:
        Formatted description string
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Build description
    desc_parts = [
        "Milvus Storage v1.0.0 - Multi-tenant dense vector search",
        f"Created: {timestamp}",
        f"Vector Dimension: {dimension}"
    ]

    # Add model information
    # Priority: actual models used > preset > unknown
    if metadata_model_used or embedding_model_used or ACTIVE_PRESET:
        try:
            if preset_name:
                desc_parts.append(f"Preset: {preset_name}")

            # Embedding model: use actual if provided, otherwise preset
            embedding = embedding_model_used or (ACTIVE_PRESET.get('embedding') if ACTIVE_PRESET else None)
            if embedding:
                desc_parts.append(f"Embedding: {embedding}")

            # Metadata LLM: use actual if provided, otherwise preset with warning
            if metadata_model_used:
                desc_parts.append(f"Metadata LLM: {metadata_model_used}")
            elif ACTIVE_PRESET and ACTIVE_PRESET.get('metadata'):
                # Warn that this is from preset, not necessarily what was used
                desc_parts.append(f"Metadata LLM (preset): {ACTIVE_PRESET.get('metadata')}")

            # Provider
            if ACTIVE_PRESET and ACTIVE_PRESET.get('provider'):
                desc_parts.append(f"Provider: {ACTIVE_PRESET.get('provider')}")

        except Exception as e:
            desc_parts.append(f"Model info: unavailable ({str(e)[:50]})")

    # Add source document if provided
    if source_document:
        # Extract just the filename if it's a path
        if '/' in source_document:
            source_document = source_document.split('/')[-1]
        desc_parts.append(f"Source: {source_document}")

    # Add metadata fields info
    desc_parts.append("Metadata: 7 fields (keywords, topics, questions, summary, semantic_keywords, entity_relationships, attributes)")

    return " | ".join(desc_parts)


def create_storage_schema_v1(
    dimension: int = None,
    source_document: Optional[str] = None,
    preset_name: Optional[str] = None,
    metadata_model_used: Optional[str] = None,
    embedding_model_used: Optional[str] = None
) -> CollectionSchema:
    """
    Create Milvus schema v1.0.0 with 17 fields (minimal/base metadata)

    Supports:
    - Multi-tenancy (tenant_id field with index)
    - Dense vector search only (no sparse vectors)
    - Base metadata (7 fields: keywords, topics, questions, summary, semantic_keywords, entity_relationships, attributes)

    Args:
        dimension: Dense vector dimension (if None, uses config.DEFAULT_DIMENSION from model registry)

    Returns:
        CollectionSchema ready for collection creation
    """
    # Use config default if not specified (dynamically set from model registry)
    if dimension is None:
        dimension = config.DEFAULT_DIMENSION

    fields: List[FieldSchema] = [
        # ============================================================
        # CORE FIELDS (9 fields)
        # ============================================================
        FieldSchema(
            name="id",
            dtype=DataType.VARCHAR,
            is_primary=True,
            max_length=100,
            description="Unique chunk ID"
        ),
        FieldSchema(
            name="document_id",
            dtype=DataType.VARCHAR,
            max_length=100,
            description="Parent document ID"
        ),
        FieldSchema(
            name="chunk_index",
            dtype=DataType.INT64,
            description="Chunk position in document"
        ),
        FieldSchema(
            name="text",
            dtype=DataType.VARCHAR,
            max_length=config.MAX_VARCHAR_LENGTH,
            description="Chunk text content"
        ),
        FieldSchema(
            name="tenant_id",
            dtype=DataType.VARCHAR,
            max_length=100,
            is_partition_key=True,  # Enable automatic partition management
            description="Tenant/client ID for multi-tenancy (partition key)"
        ),
        FieldSchema(
            name="created_at",
            dtype=DataType.VARCHAR,
            max_length=50,
            description="Creation timestamp (ISO 8601)"
        ),
        FieldSchema(
            name="updated_at",
            dtype=DataType.VARCHAR,
            max_length=50,
            description="Last update timestamp (ISO 8601)"
        ),
        FieldSchema(
            name="char_count",
            dtype=DataType.INT64,
            description="Character count"
        ),
        FieldSchema(
            name="token_count",
            dtype=DataType.INT64,
            description="Token count"
        ),

        # ============================================================
        # VECTOR FIELDS (1 field - dense only)
        # ============================================================
        FieldSchema(
            name="dense_vector",
            dtype=DataType.FLOAT_VECTOR,
            dim=dimension,
            description="Dense semantic vector"
        ),

        # ============================================================
        # BASE METADATA (7 fields - minimal schema with semantic expansion, relationships, and attributes)
        # ============================================================
        FieldSchema(name="keywords", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="topics", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="questions", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="summary", dtype=DataType.VARCHAR, max_length=1000),
        FieldSchema(name="semantic_keywords", dtype=DataType.VARCHAR, max_length=800),
        FieldSchema(name="entity_relationships", dtype=DataType.VARCHAR, max_length=1000),
        FieldSchema(name="attributes", dtype=DataType.VARCHAR, max_length=1000),
    ]

    # Generate rich description with model metadata
    description = generate_collection_description(
        dimension=dimension,
        source_document=source_document,
        preset_name=preset_name,
        metadata_model_used=metadata_model_used,
        embedding_model_used=embedding_model_used
    )

    schema = CollectionSchema(
        fields=fields,
        description=description
    )

    return schema


def create_indexes(collection):
    """
    Create indexes for vector search and filtering

    Indexes:
    1. Dense vector index (HNSW for scalable semantic search)
    2. Scalar index on document_id (tenant_id is partition key, auto-indexed)
    """

    # Dense vector index (semantic search)
    # Build params based on index type
    if config.DENSE_INDEX_TYPE == "HNSW":
        index_params = {
            "M": config.HNSW_M,
            "efConstruction": config.HNSW_EF_CONSTRUCTION
        }
    elif config.DENSE_INDEX_TYPE in ["IVF_FLAT", "IVF_SQ8", "IVF_PQ"]:
        index_params = {"nlist": config.DENSE_NLIST}
    else:  # FLAT or others
        index_params = {"nlist": config.DENSE_NLIST}  # FLAT doesn't use nlist, but include for compatibility

    dense_index_params = {
        "index_type": config.DENSE_INDEX_TYPE,
        "metric_type": config.DENSE_METRIC_TYPE,
        "params": index_params
    }
    collection.create_index(
        field_name="dense_vector",
        index_params=dense_index_params,
        index_name="dense_index"
    )
    print(f"✓ Created dense vector index ({config.DENSE_INDEX_TYPE}, {config.DENSE_METRIC_TYPE})")
    if config.DENSE_INDEX_TYPE == "HNSW":
        print(f"  HNSW params: M={config.HNSW_M}, efConstruction={config.HNSW_EF_CONSTRUCTION}")

    # Scalar index for document filtering
    # Note: tenant_id is partition_key, automatically indexed by Milvus
    try:
        collection.create_index(field_name="document_id", index_name="document_id_index")
        print(f"✓ Created scalar index on 'document_id'")
    except Exception as e:
        print(f"⚠ Warning: Could not create index on 'document_id': {e}")

    print(f"\n✅ All indexes created successfully")


def get_all_field_names() -> List[str]:
    """Get list of all field names in schema (for output_fields)"""
    schema = create_storage_schema_v1()
    return [field.name for field in schema.fields]


def get_required_fields() -> List[str]:
    """Get list of required fields for insert"""
    return [
        "id", "document_id", "chunk_index", "text", "tenant_id",
        "dense_vector", "created_at", "updated_at"
    ]


def get_metadata_fields() -> List[str]:
    """Get list of metadata fields (base mode: 7 fields)"""
    return [
        "keywords", "topics", "questions", "summary", "semantic_keywords", "entity_relationships", "attributes"
    ]
