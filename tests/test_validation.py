"""
Tests for domain validation functions.

Tests validate_date_not_future and filter_low_confidence functions
that enforce business rules on extracted entities per D-06, D-07, D-08.
"""

import pytest
from unittest.mock import MagicMock


def make_temporal_entity(type_="Date", text="15.03.2023", confidence=0.9):
    """Helper to create TemporalEntity-like mock for testing."""
    from src.schemas.entities import TemporalEntity, SourceSpan
    return TemporalEntity(
        type=type_,
        text=text,
        confidence=confidence,
        source_span=SourceSpan(start=0, end=len(text), text=text),
        source_span_validated=True
    )


def make_clinical_entity(type_="Diagnosis", text="Lumbalgie", confidence=0.9):
    """Helper to create ClinicalEntity-like mock for testing."""
    from src.schemas.entities import ClinicalEntity, SourceSpan
    return ClinicalEntity(
        type=type_,
        text=text,
        confidence=confidence,
        source_span=SourceSpan(start=0, end=len(text), text=text),
        source_span_validated=True
    )


def test_validate_date_not_future_accepts_past():
    """Test that a past date is accepted with no error."""
    from src.validation.validators import validate_date_not_future
    entity = make_temporal_entity(type_="Date", text="15.03.2023")
    is_valid, error_msg = validate_date_not_future(entity)
    assert is_valid is True
    assert error_msg is None


def test_validate_date_not_future_rejects_future():
    """Test that a future date is rejected with specific error message."""
    from src.validation.validators import validate_date_not_future
    entity = make_temporal_entity(type_="Date", text="15.03.2027")
    is_valid, error_msg = validate_date_not_future(entity)
    assert is_valid is False
    assert error_msg == "Date is in the future: 15.03.2027"


def test_validate_date_not_future_ignores_los():
    """Test that LOS (length-of-stay) entities skip date validation."""
    from src.validation.validators import validate_date_not_future
    entity = make_temporal_entity(type_="LOS", text="4 Tage", confidence=0.9)
    is_valid, error_msg = validate_date_not_future(entity)
    assert is_valid is True
    assert error_msg is None


def test_validate_date_not_future_invalid_format():
    """Test that an unparseable date text returns a validation error."""
    from src.validation.validators import validate_date_not_future
    entity = make_temporal_entity(type_="Date", text="not-a-date")
    is_valid, error_msg = validate_date_not_future(entity)
    assert is_valid is False
    assert "Invalid date format" in error_msg


def test_filter_low_confidence_threshold_50():
    """Test that confidence filtering splits entities at threshold=0.5."""
    from src.validation.validators import filter_low_confidence
    entities = [
        make_temporal_entity(confidence=0.3),
        make_temporal_entity(confidence=0.5),
        make_temporal_entity(confidence=0.7),
        make_temporal_entity(confidence=0.9),
    ]
    high_conf, low_conf = filter_low_confidence(entities, threshold=0.5)
    # Entities >= 0.5 go to high_conf (0.5, 0.7, 0.9 = 3 items)
    assert len(high_conf) == 3
    # Entities < 0.5 go to low_conf (0.3 = 1 item)
    assert len(low_conf) == 1
    assert low_conf[0].confidence == 0.3


def test_filter_low_confidence_empty_input():
    """Test that empty input returns two empty lists."""
    from src.validation.validators import filter_low_confidence
    high_conf, low_conf = filter_low_confidence([], threshold=0.5)
    assert high_conf == []
    assert low_conf == []


def test_filter_low_confidence_preserves_entities():
    """Test that filter_low_confidence returns original entity objects unchanged."""
    from src.validation.validators import filter_low_confidence
    entity_high = make_temporal_entity(confidence=0.8)
    entity_low = make_clinical_entity(confidence=0.2)
    high_conf, low_conf = filter_low_confidence([entity_high, entity_low], threshold=0.5)
    assert entity_high in high_conf
    assert entity_low in low_conf


def test_filter_low_confidence_all_above_threshold():
    """Test that all entities above threshold go to high_conf."""
    from src.validation.validators import filter_low_confidence
    entities = [
        make_temporal_entity(confidence=0.6),
        make_temporal_entity(confidence=0.9),
    ]
    high_conf, low_conf = filter_low_confidence(entities, threshold=0.5)
    assert len(high_conf) == 2
    assert len(low_conf) == 0


def test_filter_low_confidence_all_below_threshold():
    """Test that all entities below threshold go to low_conf."""
    from src.validation.validators import filter_low_confidence
    entities = [
        make_temporal_entity(confidence=0.1),
        make_temporal_entity(confidence=0.4),
    ]
    high_conf, low_conf = filter_low_confidence(entities, threshold=0.5)
    assert len(high_conf) == 0
    assert len(low_conf) == 2
