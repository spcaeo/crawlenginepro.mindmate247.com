# Deprecated Metadata Endpoints - v1 and v3

**Removed:** 2025-10-20
**Reason:** Only v2 endpoint is used, v1 and v3 were never utilized in production

## What was removed:

### From metadata_api.py:
- `/v1/metadata` endpoint (lines 639-651)
- `/v1/metadata/batch` endpoint (lines 653-693)
- `/v3/metadata` endpoint (lines 699-711)
- `/v3/metadata/batch` endpoint (lines 713-751)
- `extract_enriched_metadata()` function (lines 379-474)
- `extract_enriched_metadata_with_semaphore()` function (lines 374-377)

### From models.py:
- `EnrichedMetadataResponse` model
- `EnrichedBatchMetadataResponse` model

## What remains (active):
- `/v2/metadata` endpoint ✅ (returns 7 fields with semantic expansion)
- `/v2/metadata/batch` endpoint ✅
- `extract_metadata()` function ✅
- `MetadataResponse` model ✅

## Migration:
No migration needed - these endpoints were never used in production.
The system was already using `/v2/metadata` exclusively.
