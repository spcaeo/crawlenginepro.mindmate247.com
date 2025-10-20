#!/usr/bin/env python3
"""
Intent & Prompt Adaptation Service v1.0.0
Detects query intent and selects optimal system prompt for answer generation
"""

import json
import time
import asyncio
import httpx
import uvicorn
import re
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add parent directories to path for shared module access
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))  # PipeLineServices root

from shared import (
    get_llm_for_task,
    requires_output_cleaning,
    get_cleaning_pattern,
    get_model_info
)

import config
import prompt_templates
import query_logger
from models import IntentRequest, IntentResponse, HealthResponse

# Import pattern matching and learning
from pattern_matcher_v2 import get_matcher_v2 as get_matcher
from pattern_learner import get_learner


def detect_output_languages(query: str) -> list[str]:
    """
    Detect which languages the user wants in the OUTPUT/RESPONSE.

    This is separate from the input language detection - it determines which languages
    to include in the answer (e.g., "explain in both French and English").

    Args:
        query: User query string

    Returns:
        List of language codes requested for output: ['en'], ['fr'], ['en', 'fr'], etc.

    Examples:
        >>> detect_output_languages("Explain in French")
        ['fr']
        >>> detect_output_languages("Provide answer in both French and English")
        ['en', 'fr']
        >>> detect_output_languages("What is the price?")
        ['en']  # Default to English only
    """
    query_lower = query.lower()
    languages = []

    # Detect specific language requests
    language_patterns = {
        'fr': [
            r'\b(french|français|en français|in french)\b',
            r'\bfr\b'  # ISO code
        ],
        'es': [
            r'\b(spanish|español|en español|in spanish)\b',
            r'\bes\b'  # ISO code
        ],
        'de': [
            r'\b(german|deutsch|auf deutsch|in german)\b',
            r'\bde\b'  # ISO code
        ],
        'zh': [
            r'\b(chinese|mandarin|中文|in chinese)\b',
            r'\bzh\b'  # ISO code
        ],
        'ja': [
            r'\b(japanese|日本語|in japanese)\b',
            r'\bja\b'  # ISO code
        ]
    }

    # Check for each language
    for lang_code, patterns in language_patterns.items():
        for pattern in patterns:
            if re.search(pattern, query_lower):
                if lang_code not in languages:
                    languages.append(lang_code)
                break

    # Check for "both X and Y" pattern which implies multiple languages
    both_pattern = re.search(r'\b(both|in)\s+(\w+)\s+and\s+(\w+)\b', query_lower)
    if both_pattern:
        # Ensure English is included if not already
        if 'en' not in languages and len(languages) > 0:
            languages.insert(0, 'en')  # English first

    # Default to English if no specific language detected
    if not languages:
        languages = ['en']

    return languages


# Initialize FastAPI app
app = FastAPI(
    title=config.SERVICE_NAME,
    description=config.SERVICE_DESCRIPTION,
    version=config.API_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP client for LLM Gateway
http_client = httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT)

# Initialize pattern matcher and learner
pattern_matcher = get_matcher()
pattern_learner = get_learner(llm_gateway_url=config.LLM_GATEWAY_URL)


async def call_llm_gateway(query: str) -> dict:
    """
    Call LLM Gateway to analyze query intent

    Args:
        query: User query to analyze

    Returns:
        Dict with intent analysis
    """
    # Format the intent detection prompt
    detection_prompt = prompt_templates.INTENT_DETECTION_PROMPT.format(query=query)

    # Prepare LLM request
    payload = {
        "model": config.INTENT_DETECTION_MODEL,
        "messages": [
            {"role": "user", "content": detection_prompt}
        ],
        "max_tokens": config.INTENT_MAX_TOKENS,
        "temperature": config.INTENT_TEMPERATURE
    }

    try:
        # Call LLM Gateway
        llm_start = time.time()
        response = await http_client.post(
            f"{config.LLM_GATEWAY_URL}/v1/chat/completions",
            json=payload
        )
        response.raise_for_status()
        llm_time_ms = (time.time() - llm_start) * 1000

        # Log LLM timing
        print(f"[TIMING] LLM Gateway call: {llm_time_ms:.0f}ms (model: {config.INTENT_DETECTION_MODEL})")

        # Extract LLM response
        llm_data = response.json()
        llm_content = llm_data["choices"][0]["message"]["content"]

        # Clean up response - remove markdown code blocks and thinking tags
        llm_content = llm_content.strip()

        # Remove reasoning tags if model requires it (e.g., <think> tags from Qwen/DeepSeek models)
        if requires_output_cleaning(config.INTENT_DETECTION_MODEL):
            pattern = get_cleaning_pattern(config.INTENT_DETECTION_MODEL)
            if pattern:
                llm_content = re.sub(pattern, '', llm_content, flags=re.DOTALL)

        llm_content = llm_content.strip()

        # Remove markdown code blocks if present
        if llm_content.startswith("```json"):
            llm_content = llm_content[7:]  # Remove ```json
        elif llm_content.startswith("```"):
            llm_content = llm_content[3:]  # Remove ```
        if llm_content.endswith("```"):
            llm_content = llm_content[:-3]  # Remove trailing ```
        llm_content = llm_content.strip()

        # Parse JSON response from LLM
        intent_data = json.loads(llm_content)

        return intent_data

    except json.JSONDecodeError as e:
        # Fallback: Return safe default intent for malformed LLM responses
        import logging
        logging.warning(f"LLM returned invalid JSON for query '{query[:50]}': {str(e)}")
        return {
            "intent": "factual_retrieval",  # Safe fallback
            "language": "en",
            "complexity": "moderate",
            "requires_math": False,
            "confidence": 0.5,  # Low confidence for fallback
            "reasoning": "Fallback due to malformed LLM response"
        }
    except Exception as e:
        # Fallback for any other errors
        import logging
        logging.error(f"LLM Gateway error for query '{query[:50]}': {str(e)}")
        return {
            "intent": "factual_retrieval",
            "language": "en",
            "complexity": "moderate",
            "requires_math": False,
            "confidence": 0.5,
            "reasoning": "Fallback due to LLM Gateway error"
        }


@app.post("/v1/analyze", response_model=IntentResponse)
async def analyze_intent(request: IntentRequest) -> IntentResponse:
    """
    Analyze query intent and return adapted system prompt

    HYBRID APPROACH:
    1. Try fast pattern match (0-5ms)
    2. If high confidence (>90%), use pattern result
    3. If medium confidence (70-90%), verify with LLM
    4. If low/no confidence, use full LLM classification
    5. Log mismatches for background learning

    Args:
        request: IntentRequest with query

    Returns:
        IntentResponse with intent type and adapted prompt
    """
    start_time = time.time()
    intent = None
    language = "en"
    complexity = "moderate"
    requires_math = False
    confidence = 0.0
    used_pattern = False

    try:
        # STEP 1: Try fast pattern match (v2.0 with multi-dimensional scoring)
        pattern_result = pattern_matcher.match(request.query)

        if pattern_result:
            pattern_intent, pattern_confidence, pattern_metadata = pattern_result
            confidence_level = pattern_matcher.get_confidence_level(pattern_confidence)

            if confidence_level == "high":
                # HIGH CONFIDENCE: Use pattern result directly (FAST PATH)
                intent = pattern_intent
                confidence = pattern_confidence
                used_pattern = True
                import logging
                logging.info(f"⚡ Pattern match (high confidence {confidence:.0%}): '{request.query[:50]}' → {intent}")

            elif confidence_level == "medium":
                # MEDIUM CONFIDENCE: Verify with LLM but use simplified classification
                import logging
                logging.info(f"🔍 Pattern match (medium confidence {confidence:.0%}): '{request.query[:50]}' → {pattern_intent}, verifying with LLM...")

                # Call LLM for verification
                intent_data = await call_llm_gateway(request.query)
                llm_intent = intent_data.get("intent", "factual_retrieval")
                llm_confidence = intent_data.get("confidence", 0.9)

                # Check if LLM agrees with pattern
                if llm_intent == pattern_intent:
                    # LLM confirmed pattern
                    intent = pattern_intent
                    confidence = max(pattern_confidence, llm_confidence)  # Use higher confidence
                    logging.info(f"✅ LLM confirmed pattern match: {intent}")
                else:
                    # LLM disagreed - use LLM result
                    intent = llm_intent
                    confidence = llm_confidence
                    logging.warning(f"❌ LLM disagreed with pattern: {pattern_intent} → {llm_intent}")

                    # Add to learning queue for pattern improvement
                    await pattern_learner.add_to_queue(
                        query=request.query,
                        llm_intent=llm_intent,
                        llm_confidence=llm_confidence,
                        pattern_intent=pattern_intent,
                        pattern_confidence=pattern_confidence
                    )

                # Extract other fields from LLM response
                language = intent_data.get("language", "en")
                complexity = intent_data.get("complexity", "moderate")
                requires_math = intent_data.get("requires_math", False)

            else:
                # LOW CONFIDENCE: Fall through to full LLM classification
                pass

        # STEP 2: If no high/medium confidence pattern, use full LLM
        if intent is None:
            # Call LLM Gateway for intent detection
            intent_data = await call_llm_gateway(request.query)

            # Extract results
            intent = intent_data.get("intent", "factual_retrieval")
            language = intent_data.get("language", "en")
            complexity = intent_data.get("complexity", "moderate")
            requires_math = intent_data.get("requires_math", False)
            confidence = intent_data.get("confidence", 0.9)

            # Add to learning queue (no pattern matched)
            await pattern_learner.add_to_queue(
                query=request.query,
                llm_intent=intent,
                llm_confidence=confidence,
                pattern_intent=None,
                pattern_confidence=None
            )

        # CONFIDENCE THRESHOLD ENFORCEMENT
        import logging

        # Reject query if confidence is too low
        if confidence < config.CONFIDENCE_THRESHOLD_REJECT:
            logging.warning(f"Query rejected - confidence {confidence:.0%} below threshold {config.CONFIDENCE_THRESHOLD_REJECT:.0%}: '{request.query[:50]}'")

            # Log rejected query
            query_logger.log_query_event(
                query=request.query,
                intent=intent,
                confidence=confidence,
                language=language,
                complexity=complexity,
                event_type="rejected",
                reasoning=intent_data.get("reasoning"),
                error_message=f"Confidence {confidence:.0%} below threshold {config.CONFIDENCE_THRESHOLD_REJECT:.0%}"
            )

            raise HTTPException(
                status_code=400,
                detail=f"Query intent unclear (confidence: {confidence:.0%}). Please rephrase your question more clearly."
            )

        # Use fallback intent if confidence is medium-low
        if confidence < config.CONFIDENCE_THRESHOLD_FALLBACK:
            logging.info(f"Using fallback intent - confidence {confidence:.0%} below threshold {config.CONFIDENCE_THRESHOLD_FALLBACK:.0%}: '{request.query[:50]}'")

            # Log low-confidence query
            query_logger.log_query_event(
                query=request.query,
                intent=intent,
                confidence=confidence,
                language=language,
                complexity=complexity,
                event_type="low_confidence",
                reasoning=intent_data.get("reasoning")
            )

            intent = "factual_retrieval"  # Safe fallback
            complexity = "moderate"

        # Validate intent type
        if intent not in config.SUPPORTED_INTENTS:
            logging.warning(f"Unknown intent '{intent}', using fallback")
            intent = "factual_retrieval"  # Fallback to default

        # Determine response_style with validation
        if request.response_style:
            # User provided explicit override - validate it
            is_valid, final_response_style, validation_warning = config.validate_response_style(
                intent=intent,
                requested_style=request.response_style
            )

            if validation_warning:
                logging.warning(validation_warning)
                print(f"[RESPONSE STYLE] {validation_warning}")

            if not is_valid:
                logging.warning(f"Response style override rejected: '{request.response_style}' → '{final_response_style}'")
        else:
            # No override - use auto-detection
            final_response_style = config.recommend_response_style(intent)

        # Detect output language requirements (e.g., "in both French and English")
        output_languages = detect_output_languages(request.query)
        if len(output_languages) > 1 or (len(output_languages) == 1 and output_languages[0] != 'en'):
            print(f"[LANGUAGE DETECTION] Multi-language output requested: {output_languages}")

        # Get adapted prompt template with all customizations
        system_prompt = prompt_templates.get_prompt_template(
            intent=intent,
            language=language,
            complexity=complexity,
            enable_citations=request.enable_citations,
            response_style=final_response_style,
            response_format=request.response_format,
            output_languages=output_languages  # Pass detected output languages
        )

        # Get recommended model for Answer Generation based on intent complexity
        recommended_model = config.recommend_answer_model(intent)
        print(f"[DEBUG] Intent: {intent}, Recommended Model: {recommended_model}")

        # Calculate analysis time
        analysis_time_ms = (time.time() - start_time) * 1000

        # Log total timing breakdown
        print(f"[TIMING] Intent analysis complete: {analysis_time_ms:.0f}ms total (method: {'pattern' if used_pattern else 'llm'}, intent: {intent})")

        # Build metadata
        metadata = {
            "used_pattern": used_pattern,
            "analysis_method": "pattern_match" if used_pattern else "llm_classification"
        }

        # Add v2.0 pattern scoring metadata if available
        if used_pattern and pattern_result:
            _, _, pattern_metadata = pattern_result
            metadata["pattern_scoring"] = {
                "version": pattern_metadata.get("scoring_version", "2.0"),
                "all_scores": pattern_metadata.get("all_scores", {}),
                "runner_up": pattern_metadata.get("runner_up"),
                "runner_up_score": pattern_metadata.get("runner_up_score", 0.0),
                "confidence_gap": pattern_metadata.get("confidence_gap", 0.0),
                "multi_intent": pattern_metadata.get("multi_intent", False),
                "multi_intent_candidates": pattern_metadata.get("multi_intent_candidates", [])
            }

        # Add response_style validation info to metadata if there was an override
        if request.response_style:
            is_valid, _, validation_warning = config.validate_response_style(intent, request.response_style)
            metadata["response_style_override"] = {
                "requested": request.response_style,
                "final": final_response_style,
                "was_modified": not is_valid,
                "warning": validation_warning if validation_warning else None
            }

        return IntentResponse(
            intent=intent,
            language=language,
            complexity=complexity,
            requires_math=requires_math,
            system_prompt=system_prompt,
            confidence=confidence,
            analysis_time_ms=analysis_time_ms,
            recommended_model=recommended_model,
            recommended_max_tokens=config.recommend_max_tokens(intent),
            metadata=metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Intent analysis failed: {str(e)}"
        )


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint with LLM Gateway connectivity test"""
    # Test LLM Gateway connection (FIXED: was always returning "healthy")
    llm_connected = False
    try:
        response = await http_client.get(
            config.LLM_GATEWAY_URL.replace("/v1/chat/completions", "") + "/health",
            timeout=2.0  # Standardized timeout
        )
        llm_connected = response.status_code == 200
    except Exception:
        pass

    status = "healthy" if llm_connected else "degraded"

    return HealthResponse(
        status=status,
        service=config.SERVICE_NAME,
        version=config.API_VERSION,
        llm_gateway_connected=llm_connected
    )


@app.get("/v1/stats")
async def get_query_stats(hours: int = 168):  # 7 days = 168 hours
    """
    Get statistics for rejected and low-confidence queries

    Args:
        hours: Number of hours to analyze (default: 168 = 7 days)

    Returns:
        Statistics for both log files
    """
    days = hours / 24
    return {
        "time_window_hours": hours,
        "time_window_days": round(days, 1),
        "rejected_queries": query_logger.get_query_stats(config.REJECTED_QUERIES_LOG_FILE, hours),
        "low_confidence_queries": query_logger.get_query_stats(config.LOW_CONFIDENCE_LOG_FILE, hours),
        "pattern_matcher_stats": pattern_matcher.get_stats()
    }


async def wait_for_dependency(service_name: str, url: str, max_retries: int = 5) -> bool:
    """
    Wait for a dependency service to be healthy

    Args:
        service_name: Name of the service
        url: Health check URL
        max_retries: Maximum number of retries

    Returns:
        True if service is healthy, False otherwise
    """
    for attempt in range(max_retries):
        try:
            # Use the global http_client directly, don't wrap with "async with"
            response = await http_client.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {service_name} is healthy")
                return True
        except:
            pass

        wait_time = 2 ** attempt
        print(f"  ⏳ Waiting for {service_name}... (attempt {attempt + 1}/{max_retries}, retry in {wait_time}s)")
        await asyncio.sleep(wait_time)

    print(f"  ❌ ERROR: {service_name} not available at {url}")
    return False

@app.on_event("startup")
async def startup_event():
    """Print startup information, check dependencies, and cleanup old logs"""
    # Cleanup old log entries
    rejected_removed = query_logger.cleanup_old_logs(
        config.REJECTED_QUERIES_LOG_FILE,
        config.LOG_RETENTION_DAYS
    )
    low_conf_removed = query_logger.cleanup_old_logs(
        config.LOW_CONFIDENCE_LOG_FILE,
        config.LOG_RETENTION_DAYS
    )

    print("\n" + "="*60)
    print(f"🧠 {config.SERVICE_NAME} v{config.API_VERSION}")
    print("="*60)
    print(f"Port: {config.DEFAULT_PORT}")
    print(f"LLM Gateway: {config.LLM_GATEWAY_URL}")
    print(f"Model: {config.INTENT_DETECTION_MODEL}")
    print(f"Supported Intents: {', '.join(config.SUPPORTED_INTENTS)}")
    print(f"Caching: {'Enabled' if config.ENABLE_CACHE else 'Disabled'}")
    print(f"Confidence Thresholds: Reject<{config.CONFIDENCE_THRESHOLD_REJECT:.0%}, Fallback<{config.CONFIDENCE_THRESHOLD_FALLBACK:.0%}")
    print(f"Log Retention: {config.LOG_RETENTION_DAYS} days")
    if rejected_removed > 0 or low_conf_removed > 0:
        print(f"Cleaned up: {rejected_removed} rejected, {low_conf_removed} low-confidence entries")
    print("="*60)

    # Check dependencies before starting
    print("\n🔍 Checking dependencies...")
    llm_ok = await wait_for_dependency("LLM Gateway", config.LLM_GATEWAY_URL + "/health")

    if not llm_ok:
        print("\n❌ STARTUP FAILED: Required dependencies not available")
        print("Please ensure the following services are running:")
        print(f"  - LLM Gateway Service (port 8065)")
        print("\nExiting...")
        import sys
        sys.exit(1)

    print("\n✅ All dependencies healthy - starting Intent Service")
    print("="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await http_client.aclose()


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=config.DEFAULT_HOST,
        port=config.DEFAULT_PORT,
        log_level="info"
    )
