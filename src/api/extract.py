"""
Entity extraction endpoint for German Clinical NLP API.

POST /extract accepts German clinical text and returns structured entity data
with confidence scores and validated source spans.

Per D-05: Returns partial results even if some extractions fail.
Per D-08: Detailed errors in errors array.
Per API-04: Validates non-empty input text.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

from src.schemas.entities import EntityResponse
from src.extraction.base import extractor_registry
# Import extractors to ensure they register themselves
from src.extraction import temporal  # noqa: F401

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
        # Get temporal extractor from registry per D-09, D-11
        extractor_cls = extractor_registry.get("temporal")
        if extractor_cls is None:
            return EntityResponse(
                temporal_entities=[],
                clinical_entities=[],
                errors=["Temporal extractor not registered"]
            )

        # Initialize extractor with model per D-11 dependency injection
        extractor = extractor_cls(request.app.state.model)

        # Call extraction per D-05, D-08
        result = extractor.extract(request_body.text)

        # Return EntityResponse (Pydantic validates structure)
        return EntityResponse(**result)

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
