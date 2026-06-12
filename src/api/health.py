"""
Health check endpoint for German Clinical NLP API.

Returns service status including model readiness.
Per D-06: Returns 503 (Service Unavailable) when model fails to load.
"""

from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health")
async def health_check(request: Request):
    """
    Health check endpoint.

    Returns:
        - 200 OK with model_loaded: true if model is ready
        - 503 Service Unavailable if model is not loaded

    Response includes timestamp for monitoring.
    """
    # Check if model is loaded in app state
    if not hasattr(request.app.state, "model") or request.app.state.model is None:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "reason": "Model not loaded",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )

    return {
        "status": "healthy",
        "model_loaded": True,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
