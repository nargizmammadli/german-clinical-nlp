"""
Entity extraction endpoint for German Clinical NLP API.

POST /extract accepts German clinical text and returns structured entity data
with confidence scores and validated source spans.

Per D-05: Returns partial results even if some extractions fail.
Per D-08: Detailed errors in errors array.
Per D-12: Parallel async execution via asyncio.gather.
Per API-04: Validates non-empty input text.
"""

import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

from src.schemas.entities import EntityResponse, TemporalEntity, ClinicalEntity
from src.extraction.base import extractor_registry
# Import extractors to ensure they register themselves
from src.extraction import temporal  # noqa: F401
from src.extraction import clinical  # noqa: F401
from src.validation.validators import validate_date_not_future, filter_low_confidence
from src import config

router = APIRouter()


class ExtractionRequest(BaseModel):
    """Request body for POST /extract endpoint."""
    text: str = Field(
        min_length=1,
        description="German clinical text to extract entities from (non-empty)"
    )


@router.post("/extract", response_model=EntityResponse)
async def extract_entities(request_body: ExtractionRequest, request: Request):
    """
    Extract entities from German clinical text.

    Args:
        request_body: JSON with "text" field containing German clinical text
        request: FastAPI request object (for accessing app.state.model)

    Returns:
        EntityResponse with extracted entities, confidence scores, and source spans

    Errors:
        - 503: Model not loaded (service unavailable)
        - 422: Invalid input (empty text, malformed JSON)
        - 200 with errors array: Extraction failures (per D-05, D-08)

    Per D-05: Returns partial results - valid entities even if some failed.
    Per D-08: Detailed error messages in errors array.
    Per API-04: Validates input text is non-empty (Field min_length=1).
    """
    # Check if model is loaded per D-06 pattern from health.py
    if not hasattr(request.app.state, "model") or request.app.state.model is None:
        return JSONResponse(
            status_code=503,
            content={
                "error": "Model not loaded",
                "message": "Entity extraction service is unavailable"
            }
        )

    try:
        # Initialize result structure
        combined_result = {
            "temporal_entities": [],
            "clinical_entities": [],
            "errors": [],
            "low_confidence": []
        }

        # Get extractors from registry per D-09, D-11
        temporal_extractor_cls = extractor_registry.get("temporal")
        clinical_extractor_cls = extractor_registry.get("clinical")

        # Initialize extractors with model per D-11 dependency injection
        extractors = []
        if temporal_extractor_cls is not None:
            temporal_extractor = temporal_extractor_cls(request.app.state.model)
            extractors.append(("temporal", temporal_extractor))
        else:
            combined_result["errors"].append("Temporal extractor not registered")

        if clinical_extractor_cls is not None:
            clinical_extractor = clinical_extractor_cls(request.app.state.model)
            extractors.append(("clinical", clinical_extractor))
        else:
            combined_result["errors"].append("Clinical extractor not registered")

        # Run extractors sequentially — llama-cpp-python is not thread-safe;
        # concurrent calls on the same model instance cause heap corruption.
        if extractors:
            for name, extractor in extractors:
                try:
                    result = await asyncio.to_thread(extractor.extract, request_body.text)
                    combined_result["temporal_entities"].extend(result.get("temporal_entities", []))
                    combined_result["clinical_entities"].extend(result.get("clinical_entities", []))
                    combined_result["errors"].extend(result.get("errors", []))
                except Exception as e:
                    combined_result["errors"].append(f"{name} extraction failed: {str(e)}")
                    # Note: low_confidence from extractors is ignored — filtering done at endpoint level

        # --- Domain Validation (per VAL-02, D-07, D-08) ---
        # Per D-05: deserialize per-entity so a single bad dict doesn't discard all results
        temporal_entities = []
        for e in combined_result["temporal_entities"]:
            try:
                temporal_entities.append(TemporalEntity(**e))
            except (ValidationError, Exception) as err:
                combined_result["errors"].append(f"Entity deserialization failed: {err}")

        clinical_entities = []
        for e in combined_result["clinical_entities"]:
            try:
                clinical_entities.append(ClinicalEntity(**e))
            except (ValidationError, Exception) as err:
                combined_result["errors"].append(f"Entity deserialization failed: {err}")

        # Validate temporal entities: reject impossible future dates per D-07
        validated_temporal = []
        for entity in temporal_entities:
            is_valid, error_msg = validate_date_not_future(entity)
            if is_valid:
                validated_temporal.append(entity)
            else:
                # Per D-08: error message contains entity text and reason only (T-02-07)
                combined_result["errors"].append(error_msg)

        # --- Confidence Threshold Filtering (per D-06) ---
        # Apply configurable threshold from environment variable
        threshold = config.CONFIDENCE_THRESHOLD
        high_conf_temporal, low_conf_temporal = filter_low_confidence(validated_temporal, threshold)
        high_conf_clinical, low_conf_clinical = filter_low_confidence(clinical_entities, threshold)

        # Combine all low-confidence entities into single array for response transparency
        low_confidence_all = low_conf_temporal + low_conf_clinical

        # Return EntityResponse with validated, filtered entities (Pydantic validates structure)
        return EntityResponse(
            temporal_entities=high_conf_temporal,
            clinical_entities=high_conf_clinical,
            errors=combined_result["errors"],
            low_confidence=low_confidence_all
        )

    except ValidationError as e:
        # Pydantic validation error - return as EntityResponse with errors per D-08
        return EntityResponse(
            temporal_entities=[],
            clinical_entities=[],
            errors=[f"Validation error: {str(e)}"]
        )
    except Exception as e:
        # Unexpected error - return as EntityResponse with errors per D-08
        return EntityResponse(
            temporal_entities=[],
            clinical_entities=[],
            errors=[f"Extraction failed: {str(e)}"]
        )
