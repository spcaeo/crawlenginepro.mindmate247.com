"""
Shared utilities for PipeLineServices
Central registry for models, configurations, and common utilities
"""

from .model_registry import (
    # Model enums
    LLMModels,
    EmbeddingModels,
    RerankingModels,

    # Helper functions
    get_llm_for_task,
    get_embedding_model,
    get_reranking_model,
    get_model_info,
    supports_reasoning,
    requires_output_cleaning,
    get_cleaning_pattern,
    estimate_cost,
    get_model_provider,
    is_sambanova_model,
    is_nebius_model,

    # Constants
    DEFAULT_LLM_INTENT,
    DEFAULT_LLM_ANSWER_SIMPLE,
    DEFAULT_LLM_ANSWER_COMPLEX,
    DEFAULT_LLM_COMPRESSION,
    DEFAULT_LLM_METADATA,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_RERANKING_MODEL,
    NEBIUS_PRICING_PER_MILLION_TOKENS
)

from .health_utils import (
    # Health check utilities
    HealthCheckConfig,
    check_service_health,
    check_multiple_services,
    aggregate_health_status,
    create_health_summary,
    test_api_connectivity,
    add_cache_stats_to_health,

    # Constants
    STANDARD_HEALTH_TIMEOUT,
    STANDARD_CONFIG
)

__all__ = [
    # Model enums
    "LLMModels",
    "EmbeddingModels",
    "RerankingModels",

    # Functions
    "get_llm_for_task",
    "get_embedding_model",
    "get_reranking_model",
    "get_model_info",
    "supports_reasoning",
    "requires_output_cleaning",
    "get_cleaning_pattern",
    "estimate_cost",
    "get_model_provider",
    "is_sambanova_model",
    "is_nebius_model",

    # Constants
    "DEFAULT_LLM_INTENT",
    "DEFAULT_LLM_ANSWER_SIMPLE",
    "DEFAULT_LLM_ANSWER_COMPLEX",
    "DEFAULT_LLM_COMPRESSION",
    "DEFAULT_LLM_METADATA",
    "DEFAULT_EMBEDDING_MODEL",
    "DEFAULT_RERANKING_MODEL",
    "NEBIUS_PRICING_PER_MILLION_TOKENS",

    # Health check utilities
    "HealthCheckConfig",
    "check_service_health",
    "check_multiple_services",
    "aggregate_health_status",
    "create_health_summary",
    "test_api_connectivity",
    "add_cache_stats_to_health",
    "STANDARD_HEALTH_TIMEOUT",
    "STANDARD_CONFIG"
]
