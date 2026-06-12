"""
Model metadata endpoint for German Clinical NLP API.

Returns information about the currently loaded model.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from src import config

router = APIRouter()


@router.get("/models")
async def get_model_metadata(request: Request):
    """
    Get metadata about the currently loaded model.

    Returns:
        - 200 OK with model metadata if model is loaded
        - 503 Service Unavailable if model is not loaded

    Response includes:
        - model_name: Display name of the model
        - model_path: Path to the GGUF model file
        - context_length: Maximum context window size
    """
    # Check if model is loaded
    if not hasattr(request.app.state, "model") or request.app.state.model is None:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "reason": "Model not loaded"
            }
        )

    return {
        "model_name": config.MODEL_NAME,
        "model_path": str(config.MODEL_PATH),
        "context_length": 8192  # Per MODEL-04
    }
