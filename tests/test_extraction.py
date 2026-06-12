"""
End-to-end tests for entity extraction endpoint.

Tests POST /extract endpoint with German clinical text for temporal entities
(dates and length-of-stay indicators). Tests validate response structure,
entity fields, and error handling.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock


def test_extract_temporal_entities_dates():
    """Test extraction of date entities from German clinical text."""
    from src.main import app
    from src.schemas.entities import EntityResponse, TemporalEntity

    # Mock app state with loaded model
    mock_model = MagicMock()
    # Mock model response with temporal entity (correct offsets for "Aufnahme am 15.03.2025...")
    mock_model.create_chat_completion.return_value = {
        "choices": [{
            "message": {
                "content": '{"temporal_entities": [{"type": "Date", "text": "15.03.2025", "confidence": 0.95, "source_span": {"start": 12, "end": 22, "text": "15.03.2025"}, "source_span_validated": true}]}'
            }
        }]
    }
    app.state.model = mock_model

    client = TestClient(app)
    response = client.post(
        "/extract",
        json={"text": "Aufnahme am 15.03.2025. Patient wurde untersucht."}
    )

    assert response.status_code == 200
    data = response.json()

    # Validate response structure
    assert "temporal_entities" in data
    assert isinstance(data["temporal_entities"], list)
    assert len(data["temporal_entities"]) > 0

    # Validate first entity
    entity = data["temporal_entities"][0]
    assert entity["type"] == "Date"
    assert entity["text"] == "15.03.2025"
    assert "confidence" in entity
    assert 0.0 <= entity["confidence"] <= 1.0

    # Validate source span
    assert "source_span" in entity
    span = entity["source_span"]
    assert span["start"] == 12
    assert span["end"] == 22
    assert span["text"] == "15.03.2025"

    # Verify source span matches input text slice
    input_text = "Aufnahme am 15.03.2025. Patient wurde untersucht."
    assert input_text[span["start"]:span["end"]] == span["text"]


def test_extract_temporal_entities_los():
    """Test extraction of length-of-stay entities from German clinical text."""
    from src.main import app

    # Mock app state with loaded model
    mock_model = MagicMock()
    # Mock model response with LOS entity
    mock_model.create_chat_completion.return_value = {
        "choices": [{
            "message": {
                "content": '{"temporal_entities": [{"type": "LOS", "text": "4 Tage", "confidence": 0.90, "source_span": {"start": 14, "end": 20, "text": "4 Tage"}, "source_span_validated": true}]}'
            }
        }]
    }
    app.state.model = mock_model

    client = TestClient(app)
    response = client.post(
        "/extract",
        json={"text": "Verweildauer: 4 Tage"}
    )

    assert response.status_code == 200
    data = response.json()

    # Validate response structure
    assert "temporal_entities" in data
    assert isinstance(data["temporal_entities"], list)
    assert len(data["temporal_entities"]) > 0

    # Validate LOS entity
    entity = data["temporal_entities"][0]
    assert entity["type"] == "LOS"
    assert entity["text"] == "4 Tage"
    assert "confidence" in entity
    assert 0.0 <= entity["confidence"] <= 1.0


def test_extract_empty_text_error():
    """Test that empty text returns 400 Bad Request."""
    from src.main import app

    # Mock app state with loaded model
    app.state.model = MagicMock()

    client = TestClient(app)
    response = client.post(
        "/extract",
        json={"text": ""}
    )

    assert response.status_code == 422  # FastAPI Pydantic validation returns 422
    data = response.json()
    assert "detail" in data


def test_extract_response_schema():
    """Test that response conforms to EntityResponse Pydantic schema."""
    from src.main import app
    from src.schemas.entities import EntityResponse

    # Mock app state with loaded model
    mock_model = MagicMock()
    # Mock model response with complete schema
    mock_model.create_chat_completion.return_value = {
        "choices": [{
            "message": {
                "content": '{"temporal_entities": [{"type": "Date", "text": "15.03.2025", "confidence": 0.95, "source_span": {"start": 11, "end": 21, "text": "15.03.2025"}, "source_span_validated": true}]}'
            }
        }]
    }
    app.state.model = mock_model

    client = TestClient(app)
    response = client.post(
        "/extract",
        json={"text": "Aufnahme am 15.03.2025. Patient wurde untersucht."}
    )

    assert response.status_code == 200
    data = response.json()

    # Validate all required fields in EntityResponse schema
    assert "temporal_entities" in data
    assert "clinical_entities" in data
    assert "errors" in data

    # Validate arrays are lists
    assert isinstance(data["temporal_entities"], list)
    assert isinstance(data["clinical_entities"], list)
    assert isinstance(data["errors"], list)


def test_extract_clinical_entities_diagnosis():
    """Test extraction of diagnosis entities from German clinical text (TDD RED)."""
    from src.main import app

    # Mock app state with loaded model
    mock_model = MagicMock()
    # Mock model response with diagnosis entity
    mock_model.create_chat_completion.return_value = {
        "choices": [{
            "message": {
                "content": '{"clinical_entities": [{"type": "Diagnosis", "text": "Lumbalgie (M54.5)", "confidence": 0.92, "source_span": {"start": 10, "end": 27, "text": "Lumbalgie (M54.5)"}, "source_span_validated": true}]}'
            }
        }]
    }
    app.state.model = mock_model

    client = TestClient(app)
    response = client.post(
        "/extract",
        json={"text": "Diagnose: Lumbalgie (M54.5). Therapie empfohlen."}
    )

    assert response.status_code == 200
    data = response.json()

    # Validate response has clinical_entities
    assert "clinical_entities" in data
    assert isinstance(data["clinical_entities"], list)
    assert len(data["clinical_entities"]) > 0

    # Validate diagnosis entity
    entity = data["clinical_entities"][0]
    assert entity["type"] == "Diagnosis"
    assert "Lumbalgie" in entity["text"]
    assert "confidence" in entity
    assert 0.0 <= entity["confidence"] <= 1.0

    # Validate source span
    assert "source_span" in entity
    span = entity["source_span"]
    assert "start" in span
    assert "end" in span
    assert "text" in span


def test_extract_clinical_entities_medication():
    """Test extraction of medication entities from German clinical text (TDD RED)."""
    from src.main import app

    # Mock app state with loaded model
    mock_model = MagicMock()
    # Mock model response with medication entity
    mock_model.create_chat_completion.return_value = {
        "choices": [{
            "message": {
                "content": '{"clinical_entities": [{"type": "Medication", "text": "Ibuprofen 600mg", "confidence": 0.95, "source_span": {"start": 9, "end": 24, "text": "Ibuprofen 600mg"}, "source_span_validated": true}]}'
            }
        }]
    }
    app.state.model = mock_model

    client = TestClient(app)
    response = client.post(
        "/extract",
        json={"text": "Therapie: Ibuprofen 600mg 3x täglich."}
    )

    assert response.status_code == 200
    data = response.json()

    # Validate response has clinical_entities
    assert "clinical_entities" in data
    assert isinstance(data["clinical_entities"], list)
    assert len(data["clinical_entities"]) > 0

    # Validate medication entity
    entity = data["clinical_entities"][0]
    assert entity["type"] == "Medication"
    assert "Ibuprofen" in entity["text"]
    assert "600mg" in entity["text"]
    assert "confidence" in entity
    assert 0.0 <= entity["confidence"] <= 1.0

    # Validate source span
    assert "source_span" in entity
    span = entity["source_span"]
    assert "start" in span
    assert "end" in span
    assert "text" in span
