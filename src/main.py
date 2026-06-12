"""
German Clinical NLP API - Main Application

FastAPI application with lifespan model loading per D-01 (startup init, not lazy).
Exposes health, model metadata, and entity extraction endpoints.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger
from src import config
from src.models.loader import initialize_model
from src.api import health, models, extract


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    STARTUP: Load GGUF model into app.state (per D-01, D-02)
    SHUTDOWN: Clean up model resources
    """
    # STARTUP: Load model
    try:
        # Note: In test environments without llama-cpp-python installed,
        # this will raise ImportError. Tests mock app.state.model instead.
        app.state.model = initialize_model(
            model_path=config.MODEL_PATH,
            n_ctx=8192  # Per MODEL-04: 8K+ context window
        )
    except ImportError:
        # llama-cpp-python not installed (test/dev environment)
        # Tests will mock app.state.model directly
        app.state.model = None
        logger.warning("llama-cpp-python not installed, model not loaded")
    except Exception as e:
        # Model loading failed (per D-06: fail fast)
        logger.error(f"Failed to load model: {e}")
        app.state.model = None
        # Continue startup but mark model as unavailable
        # Health endpoint will return 503

    yield  # Application runs here, handling requests

    # SHUTDOWN: Clean up resources
    app.state.model = None


# Create FastAPI application
app = FastAPI(
    title="German Clinical NLP API",
    version="1.0.0",
    description="Portfolio-focused information extraction pipeline for German clinical text",
    lifespan=lifespan
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(models.router, tags=["models"])
app.include_router(extract.router, tags=["extraction"])
