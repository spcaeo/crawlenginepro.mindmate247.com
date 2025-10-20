#!/usr/bin/env python3
"""
Metadata Extraction Service v1.0.0 - Configuration
7 semantic fields optimized for RAG applications
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from enum import Enum

# Load common .env from PipeLineServices root (4 levels up: v1.0.0 -> metadata -> services -> Ingestion -> PipeLineServices)
env_path = Path(__file__).resolve().parents[4] / ".env"
load_dotenv(env_path)

# Add shared directory to path
SHARED_DIR = env_path.parent / "shared"
sys.path.insert(0, str(SHARED_DIR))

from model_registry import (
    LLMModels,
    get_model_info,
    get_llm_for_task,
    requires_output_cleaning,
    get_cleaning_pattern
)

# ============================================================================
# Version Management
# ============================================================================
API_VERSION = "1.0.0"
SERVICE_NAME = "Metadata Extraction Service"
SERVICE_DESCRIPTION = "Extract semantic metadata from text using LLM (7 fields)"

# ============================================================================
# Server Configuration
# ============================================================================
DEFAULT_HOST = "0.0.0.0"
# Use METADATA_SERVICE_PORT if set, otherwise fall back to PORT
DEFAULT_PORT = int(os.getenv("METADATA_SERVICE_PORT", os.getenv("PORT", "8062")))
DEFAULT_WORKERS = 2

# ============================================================================
# Inter-Service Communication Mode
# ============================================================================
# Set INTERNAL_MODE=true for direct service calls (lower latency)
# Set INTERNAL_MODE=false to route through APISIX (higher security, more logging)
INTERNAL_MODE = os.getenv("INTERNAL_MODE", "true").lower() == "true"

# ============================================================================
# LLM Gateway Configuration (Environment-aware)
# ============================================================================
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if INTERNAL_MODE:
    # Direct internal calls - Environment-aware
    if ENVIRONMENT == "production":
        LLM_GATEWAY_URL = os.getenv("LLM_GATEWAY_URL_PRODUCTION", "http://localhost:8065/v1/chat/completions")
    else:  # development
        LLM_GATEWAY_URL = os.getenv("LLM_GATEWAY_URL_DEVELOPMENT", "http://localhost:8065/v1/chat/completions")
else:
    # Via APISIX gateway (requires API key)
    APISIX_GATEWAY = os.getenv("APISIX_GATEWAY_URL", "http://localhost:9080")
    LLM_GATEWAY_URL = f"{APISIX_GATEWAY}/api/v1/llm/chat/completions"

# Service API key (only used if INTERNAL_MODE=false)
LLM_GATEWAY_API_KEY = os.getenv("LLM_GATEWAY_API_KEY", "dev_crawlenginepro_2025_secret_key_001")

print(f"[CONFIG] Environment: {ENVIRONMENT}")
print(f"[CONFIG] LLM Gateway: {LLM_GATEWAY_URL}")

# ============================================================================
# Model Configuration - using shared registry
# ============================================================================
class ModelType(str, Enum):
    """Supported LLM models for metadata extraction - maps to shared registry"""
    FAST = "32B-fast"
    RECOMMENDED = "32B-fast"
    ADVANCED = "480B"
    BALANCED = "72B"

class FlavorType(str, Enum):
    """Model flavor types - affects latency and pricing"""
    BASE = "base"
    FAST = "fast"

# Model name mappings - using SambaNova models (via shared registry)
MODEL_NAMES = {
    ModelType.FAST: LLMModels.SAMBANOVA_QWEN_32B.value,           # Qwen3-32B (SambaNova)
    ModelType.RECOMMENDED: LLMModels.SAMBANOVA_QWEN_32B.value,    # Qwen3-32B (SambaNova)
    ModelType.ADVANCED: LLMModels.SAMBANOVA_DEEPSEEK_R1.value,    # DeepSeek-R1-0528 (SambaNova)
    ModelType.BALANCED: LLMModels.SAMBANOVA_LLAMA_70B.value       # Meta-Llama-3.3-70B-Instruct (SambaNova)
}

# Default model and flavor
DEFAULT_MODEL = ModelType.FAST  # Using Qwen3-32B for fast reasoning with <think> tags
DEFAULT_FLAVOR = FlavorType.BASE

# Model-specific configurations (increased tokens for LLM reasoning)
# Max tokens for LLM reasoning and field generation
MODEL_CONFIGS = {
    ModelType.FAST: {
        "temperature": 0.1,
        "max_tokens": 2500,  # Increased from 1500 - prevents truncation with <think> tags
        "timeout": 40
    },
    ModelType.RECOMMENDED: {
        "temperature": 0.1,
        "max_tokens": 2500,  # Increased from 1500 - prevents truncation with <think> tags
        "timeout": 40
    },
    ModelType.ADVANCED: {
        "temperature": 0.1,
        "max_tokens": 2500,  # Increased from 1500 - prevents truncation with <think> tags
        "timeout": 70
    },
    ModelType.BALANCED: {
        "temperature": 0.1,
        "max_tokens": 2500,  # Increased from 1500 - prevents truncation with <think> tags
        "timeout": 100
    }
}

# ============================================================================
# Extraction Modes (SIMPLIFIED - BASIC ONLY)
# ============================================================================
class ExtractionMode(str, Enum):
    """Extraction modes for different use cases"""
    BASIC = "basic"        # 7 fields: keywords, topics, questions, summary, semantic_keywords, entity_relationships, attributes (FAST - 2x speed)
    # STANDARD = "standard"  # 20 fields: basic + common fields (BALANCED) - DISABLED
    

# Fields extracted per mode
EXTRACTION_FIELDS = {
    "basic": ["keywords", "topics", "questions", "summary", "semantic_keywords", "entity_relationships", "attributes"],
    # DISABLED - Only BASIC mode supported
    # "standard": [
    #     "keywords", "topics", "questions", "summary", "entities",
    #     "person_names", "organization_names", "location_names", "product_names",
    #     "dates", "language", "sentiment", "document_type",
    #     "brand", "manufacturer", "model", "price", "currency", "year",
    #     "urls", "emails", "phone_numbers", "technical_terms"
    # ],
    # "full": [
    #     "keywords", "topics", "questions", "summary", "entities",
    #     "person_names", "organization_names", "location_names", "product_names",
    #     "dates", "date_earliest", "date_latest", "categories", "language", "sentiment",
    #     "document_type", "brand", "manufacturer", "model", "sku", "price", "currency",
    #     "year", "color", "size", "weight", "dimensions", "specifications",
    #     "vendor_name", "vendor_id", "amount", "tax_amount", "invoice_number",
    #     "transaction_date", "payment_method", "payment_status", "technical_terms",
    #     "key_numbers", "urls", "emails", "phone_numbers", "confidence_score"
    # ]
}

# Mode-specific configurations
MODE_CONFIGS = {
    "basic": {"max_tokens": 1000, "timeout": 20, "temperature": 0.1},  # Increased for 7 fields with semantic expansion
    # DISABLED - Only BASIC mode supported
    # "standard": {"max_tokens": 1200, "timeout": 30, "temperature": 0.1},
    # "full": {"max_tokens": 2500, "timeout": 40, "temperature": 0.1}
}

# ============================================================================
# Metadata Extraction Defaults
# ============================================================================
DEFAULT_EXTRACTION_MODE = ExtractionMode.BASIC  # BASIC mode only (7 fields)
DEFAULT_KEYWORDS_COUNT = "5-10"
DEFAULT_TOPICS_COUNT = "2-5"
DEFAULT_QUESTIONS_COUNT = "2-5"
DEFAULT_SUMMARY_LENGTH = "1-2 sentences"

# ============================================================================
# JSON Schema for Response Format (enforces maxLength)
# ============================================================================
JSON_SCHEMA_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "metadata_extraction",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "string",
                    "description": "Comma-separated keywords (5-10 max)",
                    "maxLength": 150
                },
                "topics": {
                    "type": "string",
                    "description": "Comma-separated topics (2-5 max)",
                    "maxLength": 100
                },
                "questions": {
                    "type": "string",
                    "description": "Question list separated by semicolons (2-5 max)",
                    "maxLength": 300
                },
                "summary": {
                    "type": "string",
                    "description": "Brief summary (1-2 sentences max)",
                    "maxLength": 300
                },
                "semantic_keywords": {
                    "type": "string",
                    "description": "Comma-separated semantic expansion keywords (10-15 max)",
                    "maxLength": 400
                },
                "entity_relationships": {
                    "type": "string",
                    "description": "Entity relationship triplets separated by | (5-10 max)",
                    "maxLength": 500
                },
                "attributes": {
                    "type": "string",
                    "description": "Comma-separated key-value pairs (10-15 max)",
                    "maxLength": 500
                }
            },
            "required": ["keywords", "topics", "questions", "summary", "semantic_keywords", "entity_relationships", "attributes"],
            "additionalProperties": False
        }
    }
}

# ============================================================================
# Validation Limits
# ============================================================================
MIN_TEXT_LENGTH = 10
MAX_TEXT_LENGTH = 10000
MAX_BATCH_SIZE = 50

# ============================================================================
# Retry Configuration
# ============================================================================
# CRITICAL: Nebius has 600 req/min limit - use longer delays to spread requests
# Exponential backoff: 3s, 6s, 9s between retries
MAX_RETRIES = 3
RETRY_DELAY = 3  # Increased from 2 to 3 seconds
RETRY_BACKOFF = True

# ============================================================================
# Response Caching Configuration
# ============================================================================
ENABLE_CACHING = os.getenv("ENABLE_CACHING", "true").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "5000"))  # 5000 entries

# ============================================================================
# Connection Pooling Configuration (OPTIMIZED)
# ============================================================================
# Balanced for high throughput without resource exhaustion
# Reduced from 60/200 to 30/100 (still handles 30-60 parallel requests efficiently)
# httpx default is 10/20 - we use 3x that for better performance
CONNECTION_POOL_SIZE = int(os.getenv("CONNECTION_POOL_SIZE", "30"))
CONNECTION_POOL_MAX = int(os.getenv("CONNECTION_POOL_MAX", "100"))
CONNECTION_TIMEOUT = int(os.getenv("CONNECTION_TIMEOUT", "30"))

# ============================================================================
# Concurrency Control (NEW - Pipeline Optimization)
# ============================================================================
# Limit parallel LLM calls to prevent overwhelming LLM Gateway
# With 20 parallel calls at ~0.2s each (32B-fast), we get ~100 chunks/sec
# This prevents 429 rate limit errors and connection pool exhaustion
MAX_PARALLEL_LLM_CALLS = int(os.getenv("MAX_PARALLEL_LLM_CALLS", "20"))

# ============================================================================
# Prompt Templates - v3.1.0 ENHANCED (Mode-Specific)
# ============================================================================
# BASIC Mode Prompt (7 fields - FAST) - Semantic Expansion with Relationships
METADATA_PROMPT_BASIC = """You must respond with ONLY valid JSON. Do not include any reasoning, thinking, or explanations.

TEXT:
{text}

Extract these 7 fields:
- keywords ({keywords_count}): Extract ONLY literal terms that appear in the text - comma separated
  * REQUIRED: Full product names AS WRITTEN, company names AS WRITTEN, model numbers AS WRITTEN, SKUs AS WRITTEN
  * Dates in ISO 8601 format with context (e.g., "expiration: 2026-12-31", "due: 2024-03-30")
  * Payment/Financial terms as found (e.g., "payment-terms: Net 30", "payment-status: Pending", "invoice: INV-2024-001")
  * Technical terms AS WRITTEN in the text
  * DO NOT extract generic placeholders like "Full product names", "Company names", "Model numbers"
  * DO NOT extract concepts that aren't literally present
- topics ({topics_count}): High-level themes and categories - comma separated
- questions ({questions_count}): Natural questions this text answers (what, why, how, who, when, where) - use " | " to separate (with spaces)
- summary ({summary_length}): Concise overview in complete sentences
- semantic_keywords (10-15): Semantic expansion for better retrieval - comma separated
  * CRITICAL: DO NOT repeat ANY terms from the keywords field above
  * ONLY provide: synonyms, industry terms, related concepts, category expansions
  * Industry/sector synonyms (e.g., "Construction Materials" for "BuildRight Materials & Supply", "restaurant equipment" for kitchen products)
  * Status descriptors (IF payment-status=Pending, add "unpaid, outstanding, awaiting-payment")
  * Relationship descriptors (IF manufacturer≠vendor, add "third-party vendor, distributor, reseller")
  * Natural language equivalents (e.g., "unpaid invoice" for payment-status: Pending)
  * Category expansions (e.g., "building supplies, contractor supplies" for construction vendor)
- entity_relationships (5-10): Entity pairs and their relationships - IMPORTANT: separate each relationship with " | " (pipe with spaces on both sides)
  * Format: entity1 → relationship → entity2 | entity3 → relationship → entity4
  * CRITICAL: Use " | " (space-pipe-space) between relationships, NOT "|" without spaces
  * Examples: "Hobart → manufacturer-of → Commercial Dishwasher | ChefPro → distributor-of → Hobart products | VitaLife Laboratories → manufacturer-of → CardioHealth Plus | BuildRight Materials & Supply → vendor-of → Lumber"
- attributes (10-15): Structured key-value pairs for filtering - comma separated
  * Format: key: value
  * Include: payment-status, payment-due, manufacturer, vendor, product-category, invoice-type, industry, brand, model, price, currency
  * Examples: "payment-status: Pending, manufacturer: Hobart, vendor: ChefPro, industry: Restaurant Equipment, product-category: Commercial Dishwasher"

CRITICAL RULES FOR KEYWORDS (Enterprise SaaS - Multi-Industry):
1. FULL ENTITY NAMES FIRST: Always include complete product names, company names, and organization names before abbreviations or components
2. PRESERVE EXACT NAMES: Use entity names EXACTLY as written in text (e.g., "CardioHealth Plus Daily Supplement", NOT "Omega-3 Supplement")
3. LEGAL PRECISION: Include legal suffixes (Inc., LLC, Corp., Ltd.) for companies
4. CERTIFICATION BODIES: Include full certification organization names (e.g., "NSF International", "USP Verified", NOT just "NSF")
5. DISTINGUISH ENTITIES: Separate brand (VitaLife Sciences) from manufacturer (VitaLife Laboratories Inc.) from product (CardioHealth Plus)
6. DATE STANDARDIZATION (CRITICAL):
   - Extract dates in ISO 8601 format (YYYY-MM-DD) as primary format
   - Include date context as keywords: "expiration: 2026-12-31", "manufactured: 2024-01-15", "best-before: 2026-12-31", "due: 2024-03-30", "transaction: 2024-02-28"
   - Extract date ranges: "valid: 2024-01-15 to 2026-12-31"
   - Include temporal keywords: "expiration", "manufacturing", "best-before", "warranty", "valid-until", "due-date", "transaction-date"
   - Examples: "2026-12-31, expiration, best-before" NOT just "December 2026"

7. FINANCIAL/INVOICE DATA (CRITICAL):
   - Payment Terms: Extract as "payment-terms: Net 30" or "payment-terms: Net 60" or "payment-terms: Due Upon Receipt"
   - Payment Status: Extract as "payment-status: Pending" or "payment-status: Paid" or "payment-status: Overdue"
   - Payment Method: Extract as "payment-method: Credit Card" or "payment-method: Purchase Order" or "payment-method: Wire Transfer"
   - Invoice/Order Numbers: Extract as "invoice: INV-2024-001" or "order: PO-2024-567"
   - Always distinguish between Payment Terms (HOW LONG to pay) vs Payment Status (WHETHER paid)
   - Examples: "payment-terms: Net 30, payment-status: Pending, due: 2024-03-30, invoice: MED-INV-2024-1523"

INDUSTRY EXAMPLES:
- E-commerce: "iPhone 15 Pro Max, Apple Inc., A17 Pro chip, iOS 17" (NOT "iPhone, Apple, chip")
- Healthcare: "CardioHealth Plus Daily Supplement, VitaLife Laboratories Inc., NSF International, expiration: 2026-12-31, manufactured: 2024-01-15, Omega-3" (NOT "Omega-3, NSF, supplement" - MUST include dates!)
- Invoices/Financial: "MedTech Equipment Supply, invoice: MED-INV-2024-1523, transaction: 2024-02-28, due: 2024-03-30, payment-terms: Net 30, payment-status: Pending, payment-method: Purchase Order" (NOT just "invoice, medical equipment" - MUST include structured payment data!)
- Automotive: "Michelin Pilot Sport 4S Tire, Michelin Corporation, ZP run-flat technology" (NOT "Michelin tire, run-flat")
- Legal: "Meta Platforms Inc., Facebook Ireland Limited" (NOT "Facebook, Meta")

Output format (respond with ONLY this JSON, nothing else):
{{"keywords": "term1, term2", "topics": "theme1, theme2", "questions": "question1 | question2 | question3", "summary": "brief overview", "semantic_keywords": "synonym1, industry-term1, status-descriptor1", "entity_relationships": "entity1 → relationship → entity2 | entity3 → relationship → entity4", "attributes": "key1: value1, key2: value2"}}"""

# ============================================================================
# DISABLED - STANDARD Mode Prompt (20 fields - BALANCED)
# ============================================================================
# METADATA_PROMPT_STANDARD = """Extract standard metadata from this text:
#
# EXTRACT THESE 20 FIELDS:
# ... (DISABLED - Only BASIC mode supported)
# """

# ============================================================================

# ============================================================================
# METADATA_PROMPT_FULL = """Extract detailed metadata... (DISABLED - Only BASIC mode supported)"""

def get_model_name_with_flavor(model: ModelType, flavor: FlavorType) -> str:
    """Get full model name with flavor suffix

    Important: For Nebius, the -fast suffix is part of the MODEL name itself,
    not a separate flavor parameter. Models come in two versions:
    - Base model: e.g., "Qwen/Qwen2.5-Coder-7B-Instruct"
    - Fast model: e.g., "Qwen/Qwen2.5-Coder-7B-Instruct-fast"

    The 'flavor' parameter controls latency optimization on the server side,
    not the model selection. Both flavors use the same model name.
    """
    base_name = MODEL_NAMES[model]

    # For Nebius, flavor is a server-side optimization, not a model suffix
    # Always return the model name as-is from MODEL_NAMES
    return base_name

def sanitize_text_for_llm(text: str) -> str:
    """
    Remove control characters that break JSON parsing

    The LLM returns JSON, but control characters (newlines, tabs, etc.)
    in the INPUT text can cause "Invalid control character" errors when
    the LLM includes them in the JSON response.

    This function cleans the text BEFORE sending to LLM.
    """
    import re

    # Replace tabs and newlines with spaces
    text = text.replace('\t', ' ')
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')

    # Remove other control characters (ASCII 0-31, 127)
    cleaned = ''.join(char for char in text if ord(char) >= 32 and ord(char) != 127)

    # Collapse multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return cleaned

def get_prompt_for_mode(mode: str) -> str:
    """Get the appropriate prompt template for extraction mode - BASIC ONLY"""
    # Only BASIC mode supported
    return METADATA_PROMPT_BASIC

def get_config_for_mode(mode: str, model: ModelType) -> dict:
    """Get configuration (max_tokens, timeout) for extraction mode - BASIC ONLY"""
    # Only BASIC mode supported - always return basic config
    mode_config = MODE_CONFIGS["basic"]
    model_config = MODEL_CONFIGS.get(model, MODEL_CONFIGS[ModelType.RECOMMENDED])

    # Merge configs: mode-specific overrides model defaults
    return {
        "temperature": mode_config.get("temperature", model_config["temperature"]),
        "max_tokens": mode_config.get("max_tokens", model_config["max_tokens"]),
        "timeout": mode_config.get("timeout", model_config["timeout"])
    }

def get_fields_for_mode(mode: str) -> list:
    """Get list of fields to extract for given mode - BASIC ONLY"""
    # Only BASIC mode supported - always return basic fields
    return EXTRACTION_FIELDS["basic"]

def get_version_info():
    """Get version information"""
    return {
        "version": API_VERSION,
        "service": SERVICE_NAME,
        "description": SERVICE_DESCRIPTION,
        "supported_models": [m.value for m in ModelType],
        "default_model": DEFAULT_MODEL.value,
        "supported_flavors": [f.value for f in FlavorType],
        "default_flavor": DEFAULT_FLAVOR.value,
        "extraction_modes": [m.value for m in ExtractionMode],
        "default_mode": DEFAULT_EXTRACTION_MODE.value
    }
