"""
API integration tests for German Clinical NLP Pipeline.

Tests health endpoint, model metadata endpoint, and OpenAPI documentation.
Uses mocked model state to avoid slow model loading in unit tests.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock


def test_health_endpoint_model_not_loaded():
    """Test /health returns 503 when model is not loaded."""
    from src.main import app

    # Mock app state with no model
    app.state.model = None

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unavailable"
    assert "model not loaded" in data["reason"].lower()
    assert "timestamp" in data


def test_health_endpoint_model_loaded():
    """Test /health returns 200 when model is loaded."""
    from src.main import app

    # Mock app state with loaded model
    app.state.model = MagicMock()

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert "timestamp" in data


def test_models_endpoint():
    """Test /models returns model metadata."""
    from src.main import app

    # Mock app state with loaded model
    app.state.model = MagicMock()

    client = TestClient(app)
    response = client.get("/models")

    assert response.status_code == 200
    data = response.json()
    assert "model_name" in data
    assert "model_path" in data
    assert "context_length" in data
    assert data["context_length"] == 8192


def test_models_endpoint_model_not_loaded():
    """Test /models returns 503 when model is not loaded."""
    from src.main import app

    # Mock app state with no model
    app.state.model = None

    client = TestClient(app)
    response = client.get("/models")

    assert response.status_code == 503


def test_openapi_docs_endpoint():
    """Test /docs endpoint is accessible."""
    from src.main import app

    client = TestClient(app)
    response = client.get("/docs")

    assert response.status_code == 200
    # OpenAPI UI returns HTML
    assert "text/html" in response.headers.get("content-type", "").lower()


def test_openapi_json_endpoint():
    """Test /openapi.json returns API schema."""
    from src.main import app

    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert data["info"]["title"] == "German Clinical NLP API"
