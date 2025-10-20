async def extract_enriched_metadata_with_semaphore(request: MetadataRequest) -> dict:
    """Extract enriched metadata with semaphore control (for batch processing)"""
    async with llm_semaphore:
        return await extract_enriched_metadata(request)

async def extract_enriched_metadata(request: MetadataRequest) -> dict:
    """Extract metadata (BASIC mode - 4 fields only) from text with caching support (v3.0.0)"""

    # Sanitize text to remove control characters that break JSON parsing
    sanitized_text = sanitize_text_for_llm(request.text)

    # FORCE BASIC MODE ONLY - ignore requested mode
    extraction_mode = "basic"

    # Check cache first - CRITICAL: Include extraction_mode in cache key
    if ENABLE_CACHING:
        cached_metadata = metadata_cache.get(
            text=sanitized_text,
            keywords_count=request.keywords_count,
            topics_count=request.topics_count,
            questions_count=request.questions_count,
            summary_length=request.summary_length,
            model=request.model.value,
            flavor=request.flavor.value,
            extraction_mode=extraction_mode
        )

        if cached_metadata:
            # Return cached result - BASIC mode only (4 fields)
            return {
                # Core metadata (BASIC mode - 4 fields only)
                "keywords": cached_metadata.get("keywords", ""),
                "topics": cached_metadata.get("topics", ""),
                "questions": cached_metadata.get("questions", ""),
                "summary": cached_metadata.get("summary", ""),

                # Processing metadata
                "chunk_id": request.chunk_id,
                "model_used": f"{request.model.value}-{request.flavor.value}",
                "processing_time_ms": 0,  # From cache
                "api_version": API_VERSION,
                "cached": True,
                "cache_age_seconds": cached_metadata.get("cache_age_seconds", 0),
                "extraction_mode": extraction_mode
            }

    # Cache miss - generate enriched metadata
    # Get mode-specific prompt and config (NEW in v3.1.0)
    prompt_template = get_prompt_for_mode(extraction_mode)
    mode_config = get_config_for_mode(extraction_mode, request.model)

    prompt = prompt_template.format(
        text=sanitized_text,
        keywords_count=request.keywords_count,
        topics_count=request.topics_count,
        questions_count=request.questions_count,
        summary_length=request.summary_length
    )

    start_time = time.time()
    # Use mode-specific timeout and max_tokens
    metadata = await call_llm_gateway(
        prompt,
        request.model,
        request.flavor,
        max_tokens=mode_config["max_tokens"],
        timeout=mode_config["timeout"]
    )
    processing_time = (time.time() - start_time) * 1000

    result = {
        # Core metadata - BASIC mode only (4 fields)
        "keywords": metadata.get("keywords", ""),
        "topics": metadata.get("topics", ""),
        "questions": metadata.get("questions", ""),
        "summary": metadata.get("summary", ""),

        # Processing metadata
        "chunk_id": request.chunk_id,
        "model_used": f"{request.model.value}-{request.flavor.value}",
        "processing_time_ms": processing_time,
        "api_version": API_VERSION,
        "cached": False,
        "extraction_mode": extraction_mode
    }

    # Cache the result (full enriched metadata)
    if ENABLE_CACHING:
        metadata_cache.set(
            text=sanitized_text,
            keywords_count=request.keywords_count,
            topics_count=request.topics_count,
            questions_count=request.questions_count,
            summary_length=request.summary_length,
            model=request.model.value,
            flavor=request.flavor.value,
            metadata=result,
            extraction_mode=extraction_mode
        )

    return result
