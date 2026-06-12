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

from src.schemas.entities import EntityResponse
from src.extraction.base import extractor_registry
# Import extractors to ensure they register themselves
from src.extraction import temporal  # noqa: F401
from src.extraction import clinical  # noqa: F401

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

        # Run extractors in parallel per D-12 using asyncio.gather
        # Use asyncio.to_thread since llama-cpp-python is synchronous
        if extractors:
            tasks = [
                asyncio.to_thread(extractor.extract, request_body.text)
                for name, extractor in extractors
            ]

            # Per D-12: Run both extractors concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Merge results per D-05: preserve partial results even if one extractor fails
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Per D-05, D-08: Capture error but continue processing
                    extractor_name = extractors[i][0]
                    combined_result["errors"].append(f"{extractor_name} extraction failed: {str(result)}")
                elif isinstance(result, dict):
                    # Merge successful results
                    combined_result["temporal_entities"].extend(result.get("temporal_entities", []))
                    combined_result["clinical_entities"].extend(result.get("clinical_entities", []))
                    combined_result["errors"].extend(result.get("errors", []))
                    combined_result["low_confidence"].extend(result.get("low_confidence", []))

        # Return EntityResponse (Pydantic validates structure)
        return EntityResponse(**combined_result)

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
