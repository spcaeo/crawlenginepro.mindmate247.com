#!/usr/bin/env python3
"""
Configuration for Intent & Prompt Adaptation Service v1.0.0
Query intent detection and prompt template selection
"""

import os
import sys
from pathlib import Path

# Add shared directory to path FIRST (before any imports that need it)
SHARED_DIR = Path(__file__).resolve().parents[4] / "shared"
sys.path.insert(0, str(SHARED_DIR))

# Import and load environment using config_loader
from config_loader import load_shared_env, get_env

# Load environment configuration (dev/prod/staging)
load_shared_env()

# Import service_registry for environment-aware service URLs
from service_registry import get_registry

from model_registry import get_llm_for_task, LLMModels

# Service metadata
API_VERSION = "1.0.0"
SERVICE_NAME = "Intent & Prompt Adaptation Service"
SERVICE_DESCRIPTION = "Query intent detection and prompt template selection for RAG pipeline"

# Server config
DEFAULT_HOST = os.getenv("HOST", "0.0.0.0")
DEFAULT_PORT = int(os.getenv("INTENT_SERVICE_PORT", "8075"))

# Dependent service URLs - Environment-aware via service_registry
# Note: Service registry returns full URL with /v1/chat/completions, we need base URL
# (intent_api.py adds /health for health checks and /v1/chat/completions for API calls)
registry = get_registry()
LLM_GATEWAY_URL = registry.get_service_url('llm_gateway').replace("/v1/chat/completions", "")

# LLM parameters for intent detection
# Use central model registry for intent detection model
INTENT_DETECTION_MODEL = get_llm_for_task("intent_detection")  # Uses Qwen-32B-fast by default
INTENT_MAX_TOKENS = int(os.getenv("INTENT_MAX_TOKENS", "1024"))  # Increased for full JSON response with reasoning
INTENT_TEMPERATURE = float(os.getenv("INTENT_TEMPERATURE", "0.1"))  # Low for consistent classification

# Performance settings
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))  # seconds
ENABLE_CACHE = False  # Intent detection is fast, no caching needed

# Intent confidence thresholds
CONFIDENCE_THRESHOLD_REJECT = float(os.getenv("CONFIDENCE_THRESHOLD_REJECT", "0.40"))  # Below this: reject request
CONFIDENCE_THRESHOLD_FALLBACK = float(os.getenv("CONFIDENCE_THRESHOLD_FALLBACK", "0.60"))  # Below this: use fallback intent
# Above FALLBACK threshold: use detected intent normally

# Logging configuration
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOW_CONFIDENCE_LOG_FILE = LOG_DIR / "low_confidence_queries.jsonl"  # JSON Lines format
REJECTED_QUERIES_LOG_FILE = LOG_DIR / "rejected_queries.jsonl"
LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", "7"))  # Keep logs for 7 days

# Supported intent types (15-intent comprehensive taxonomy)
SUPPORTED_INTENTS = [
    # GROUP 1: Core Retrieval (5)
    "simple_lookup",
    "list_enumeration",
    "yes_no",
    "definition_explanation",
    "factual_retrieval",
    # GROUP 2: Analytical (5)
    "comparison",
    "aggregation",
    "temporal",
    "relationship_mapping",
    "contextual_explanation",
    # GROUP 3: Advanced Logic (3)
    "negative_logic",
    "cross_reference",
    "synthesis",
    # GROUP 4: Meta/Structural (2)
    "document_navigation",
    "exception_handling"
]

# Supported languages (ISO 639-1 codes)
SUPPORTED_LANGUAGES = ["en", "es", "fr", "de", "it", "pt", "ja", "zh", "ko", "ar", "hi"]

# ============================================================================
# Dynamic Model Recommendation for Answer Generation
# ============================================================================
def recommend_answer_model(intent: str) -> str:
    """
    Recommend which LLM model Answer Generation should use based on intent complexity

    Simple intents (fast model - Llama-8B-fast):
    - simple_lookup, yes_no, list_enumeration
    - comparison (most comparisons are straightforward)
    - definition_explanation, factual_retrieval
    - document_navigation

    Complex intents (reasoning model - Qwen-32B-fast):
    - cross_reference (systematic comparison across sets)
    - synthesis (multi-source integration)
    - negative_logic (NOT/absence detection)
    - relationship_mapping (entity relationships)
    - aggregation (mathematical operations)
    - temporal (date arithmetic)
    - contextual_explanation (deep "why" reasoning)
    - exception_handling (policy violations)

    Args:
        intent: Detected intent type

    Returns:
        Model ID (full model name)
    """
    # Complex intents that need strong reasoning (32B model)
    complex_intents = {
        "cross_reference",      # Needs systematic comparison across sets
        "synthesis",            # Needs multi-source integration and analysis
        "negative_logic",       # Needs NOT/absence detection logic
        "relationship_mapping", # Needs entity relationship graph understanding
        "aggregation",          # Needs mathematical operations and calculations
        "temporal",             # Needs date arithmetic and timeline reasoning
        "contextual_explanation", # Needs deep reasoning about "why" questions
        "exception_handling"    # Needs understanding of policy violations
    }

    if intent in complex_intents:
        result = get_llm_for_task("answer_generation", complexity="complex", intent=intent)
        print(f"[CONFIG DEBUG] Intent '{intent}' is COMPLEX. get_llm_for_task returned: {result}")
        return result
    else:
        result = get_llm_for_task("answer_generation", complexity="simple", intent=intent)
        print(f"[CONFIG DEBUG] Intent '{intent}' is SIMPLE. get_llm_for_task returned: {result}")
        return result

def recommend_max_tokens(intent: str) -> int:
    """
    Recommend max_tokens for answer generation based on intent type

    Token allocation strategy:
    - Short answers (512 tokens): yes_no, simple_lookup
    - Medium answers (1024 tokens): definition, factual_retrieval, document_navigation, temporal, exception_handling, negative_logic
    - Long answers (2048 tokens): aggregation, synthesis, comparison, cross_reference
    - Very long answers (3072 tokens): list_enumeration (comprehensive lists)

    Args:
        intent: Detected intent type

    Returns:
        Recommended max_tokens value
    """
    # Very long answers - comprehensive lists or detailed enumerations
    if intent in ["list_enumeration"]:
        return 3072

    # Long answers - detailed analysis, specifications, multi-source synthesis
    if intent in [
        "aggregation",          # Needs to list multiple items with specs (e.g., highest-priced product with full technical specifications)
        "synthesis",            # Needs to integrate multiple sources comprehensively
        "comparison",           # Needs side-by-side detailed comparison with technical details
        "cross_reference",      # Needs comprehensive cross-document analysis with context
        "contextual_explanation", # Needs deep explanatory content with examples
        "relationship_mapping"  # Needs detailed relationship descriptions across entities
    ]:
        return 2048

    # Medium answers - standard factual responses
    if intent in [
        "definition_explanation",
        "factual_retrieval",
        "document_navigation",
        "temporal",
        "exception_handling",
        "negative_logic"        # Reduced from 2048 to 1024 - using Llama-70B (no <think> tags, more token-efficient)
    ]:
        return 1024

    # Short answers - yes/no, simple lookups
    if intent in ["yes_no", "simple_lookup"]:
        return 512

    # Default fallback for any unknown intents
    return 1536

def recommend_response_style(intent: str) -> str:
    """
    Recommend default response style based on intent type (Hybrid Approach)

    Style allocation strategy:
    - Concise (2-4 bullet points): simple_lookup, yes_no, negative_logic, list_enumeration (simple lists)
    - Balanced (organized, moderate detail): comparison, factual_retrieval, definition_explanation, temporal, document_navigation
    - Comprehensive (full analysis with tables/sections): aggregation, synthesis, cross_reference, relationship_mapping, contextual_explanation, exception_handling

    Args:
        intent: Detected intent type

    Returns:
        Recommended response_style ("concise", "balanced", or "comprehensive")
    """
    # Concise answers - direct, minimal formatting
    if intent in ["simple_lookup", "yes_no", "negative_logic"]:
        return "concise"

    # Balanced answers - organized but not excessive
    if intent in [
        "comparison",           # Side-by-side comparison without excessive tables
        "factual_retrieval",    # Organized facts without too much detail
        "definition_explanation", # Clear explanations without verbosity
        "temporal",             # Chronological info without excessive formatting
        "document_navigation",  # Simple location guidance
        "list_enumeration"      # Simple lists without elaborate descriptions
    ]:
        return "balanced"

    # Comprehensive answers - full analysis with rich formatting
    if intent in [
        "aggregation",          # Needs detailed calculations, specs, and breakdowns
        "synthesis",            # Needs multi-source integration with full context
        "cross_reference",      # Needs comprehensive cross-document analysis
        "relationship_mapping", # Needs detailed relationship diagrams and explanations
        "contextual_explanation", # Needs deep reasoning with examples
        "exception_handling"    # Needs thorough policy/compliance analysis
    ]:
        return "comprehensive"

    # Default fallback for unknown intents
    return "balanced"

def validate_response_style(intent: str, requested_style: str) -> tuple[bool, str, str]:
    """
    Validate if the requested response_style is appropriate for the detected intent.

    Returns a tuple of (is_valid, final_style, warning_message).

    Rules:
    1. NEVER allow "concise" for complex analytical intents (cross_reference, synthesis, aggregation, etc.)
       → Auto-upgrade to "balanced" with warning
    2. Allow "balanced" for any intent (it's the safe middle ground)
    3. Allow "comprehensive" for any intent (more detail is always safe, just slower)
    4. Warn when downgrading from recommended comprehensive → balanced

    Args:
        intent: Detected intent type
        requested_style: User's requested response_style override

    Returns:
        Tuple of (is_override_allowed, final_style_to_use, warning_message)
    """
    # Get the recommended style for this intent
    recommended_style = recommend_response_style(intent)

    # Define intents that REQUIRE comprehensive analysis (cannot use concise)
    REQUIRES_COMPREHENSIVE_OR_BALANCED = {
        "aggregation",          # Multi-item analysis with calculations
        "synthesis",            # Multi-source integration
        "cross_reference",      # Cross-document/entity matching
        "relationship_mapping", # Entity relationship graphs
        "contextual_explanation", # Deep "why" reasoning
        "exception_handling"    # Policy violation detection
    }

    # RULE 1: Block "concise" for complex analytical intents
    if intent in REQUIRES_COMPREHENSIVE_OR_BALANCED and requested_style == "concise":
        warning = (
            f"⚠️  RESPONSE STYLE OVERRIDE REJECTED: Intent '{intent}' requires detailed analysis. "
            f"'concise' mode produces incomplete/incorrect results. "
            f"Auto-upgraded to 'balanced' (recommended: '{recommended_style}'). "
            f"Use 'balanced' or 'comprehensive' for accurate answers."
        )
        return False, "balanced", warning  # Auto-upgrade to balanced

    # RULE 2: Warn when downgrading comprehensive → balanced (allowed but risky)
    if recommended_style == "comprehensive" and requested_style == "balanced":
        warning = (
            f"⚠️  RESPONSE STYLE OVERRIDE: Intent '{intent}' recommends 'comprehensive', "
            f"but you requested 'balanced'. This may result in less detailed analysis. "
            f"Proceeding with 'balanced' as requested."
        )
        return True, requested_style, warning  # Allow but warn

    # RULE 3: Warn when upgrading unnecessarily (balanced/concise → comprehensive)
    if recommended_style in ["concise", "balanced"] and requested_style == "comprehensive":
        warning = (
            f"ℹ️  RESPONSE STYLE OVERRIDE: Intent '{intent}' recommends '{recommended_style}', "
            f"but you requested 'comprehensive'. This will be slower but more detailed. "
            f"Proceeding with 'comprehensive' as requested."
        )
        return True, requested_style, warning  # Allow with info

    # RULE 4: No issues - use requested style
    if requested_style == recommended_style:
        return True, requested_style, ""  # Perfect match, no warning

    # Default: allow the override (it's reasonably safe)
    return True, requested_style, ""
