# ============================================================================
# v1 Endpoints (Primary - Standardized)
# ============================================================================

@app.post("/v1/metadata", response_model=EnrichedMetadataResponse)
async def extract_metadata_v1(request: MetadataRequest):
    """v1 endpoint - Extract metadata (4 basic fields)"""
    try:
        result = await extract_enriched_metadata(request)
        return EnrichedMetadataResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Metadata extraction failed: {str(e)}"
        )

@app.post("/v1/metadata/batch", response_model=EnrichedBatchMetadataResponse)
async def extract_metadata_v1_batch(batch_request: BatchMetadataRequest):
    """v1 batch endpoint - Extract metadata from multiple chunks (4 basic fields each)"""
    start_time = time.time()

    # Process all chunks in parallel with semaphore control (max 20 concurrent LLM calls)
    tasks = [extract_enriched_metadata_with_semaphore(chunk_request) for chunk_request in batch_request.chunks]
    results_data = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    successful = 0
    failed = 0

    for i, result_data in enumerate(results_data):
        if isinstance(result_data, Exception):
            # Exception occurred
            failed += 1
            results.append(EnrichedMetadataResponse(
                keywords="",
                topics="",
                questions="",
                summary=f"Error: {str(result_data)}",
                chunk_id=batch_request.chunks[i].chunk_id,
                model_used=batch_request.chunks[i].model.value,
                processing_time_ms=0,
                api_version=API_VERSION
            ))
        else:
            # Success
            successful += 1
            results.append(EnrichedMetadataResponse(**result_data))

    total_time = (time.time() - start_time) * 1000

    return EnrichedBatchMetadataResponse(
        results=results,
        total_chunks=len(batch_request.chunks),
        successful=successful,
        failed=failed,
        total_processing_time_ms=total_time
    )

# ============================================================================
# v3.0.0 Enriched Metadata Endpoints (DEPRECATED - use /v1 instead)
# ============================================================================

@app.post("/v3/metadata", response_model=EnrichedMetadataResponse)
async def extract_enriched_metadata_endpoint(request: MetadataRequest):
    """Extract enriched metadata (45 fields) from a single text chunk"""
    try:
        result = await extract_enriched_metadata(request)
        return EnrichedMetadataResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Enriched metadata extraction failed: {str(e)}"
        )

@app.post("/v3/metadata/batch", response_model=EnrichedBatchMetadataResponse)
async def extract_enriched_metadata_batch(batch_request: BatchMetadataRequest):
    """Extract enriched metadata (45 fields) from multiple text chunks in parallel (with concurrency control)"""
    start_time = time.time()

    # Process all chunks in parallel with semaphore control (max 20 concurrent LLM calls)
    # This prevents overwhelming the LLM Gateway and hitting rate limits
    tasks = [extract_enriched_metadata_with_semaphore(chunk_request) for chunk_request in batch_request.chunks]
    results_data = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    successful = 0
    failed = 0

    for i, result_data in enumerate(results_data):
        if isinstance(result_data, Exception):
            # Exception occurred - return empty enriched response
            failed += 1
            results.append(EnrichedMetadataResponse(
                # Core metadata (required)
                keywords="",
                topics="",
                questions="",
                summary=f"Error: {str(result_data)}",

                # Processing metadata
                chunk_id=batch_request.chunks[i].chunk_id,
                model_used=batch_request.chunks[i].model.value,
                processing_time_ms=0,
                api_version=API_VERSION
            ))
        else:
            # Success
            successful += 1
            results.append(EnrichedMetadataResponse(**result_data))

    total_time = (time.time() - start_time) * 1000

    return EnrichedBatchMetadataResponse(
        results=results,
        total_chunks=len(batch_request.chunks),
        successful=successful,
        failed=failed,
        total_processing_time_ms=total_time
