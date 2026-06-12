"""
Pydantic models for entity extraction responses.

Defines schemas for temporal entities (dates, length-of-stay), clinical entities
(diagnoses, medications), and source span validation per D-13, D-14, D-15, D-16.
"""

from typing import Literal
from pydantic import BaseModel, Field, model_validator


class SourceSpan(BaseModel):
    """
    Character offset span for entity grounding.

    Per D-13: Zero-based character offsets [start, end).
    Per D-14: Validated by checking input_text[start:end] == text.
    """
    start: int = Field(ge=0, description="Zero-based start character offset")
    end: int = Field(ge=0, description="Zero-based end character offset (exclusive)")
    text: str = Field(description="Exact text from input at [start:end)")

    @model_validator(mode='after')
    def validate_span_order(self) -> 'SourceSpan':
        """Validate that start < end."""
        if self.start >= self.end:
            raise ValueError(f"start ({self.start}) must be less than end ({self.end})")
        return self


class TemporalEntity(BaseModel):
    """
    Temporal entity (date or length-of-stay indicator).

    Per ENTITY-04: Extracts dates and LOS indicators from German clinical text.
    Per VAL-03: Confidence score between 0.0 and 1.0.
    Per D-15: source_span_validated flag indicates grounding verification.
    """
    type: Literal["Date", "LOS"] = Field(description="Entity type: Date or length-of-stay")
    text: str = Field(description="Extracted entity text")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence score")
    source_span: SourceSpan = Field(description="Character offset span in input text")
    source_span_validated: bool = Field(
        default=False,
        description="True if source_span.text matches input_text[start:end] per D-14"
    )


class ClinicalEntity(BaseModel):
    """
    Clinical entity (diagnosis or medication).

    Per ENTITY-05, ENTITY-06: Extracts diagnoses and medications from German clinical text.
    Per VAL-03: Confidence score between 0.0 and 1.0.
    Per D-15: source_span_validated flag indicates grounding verification.
    """
    type: Literal["Diagnosis", "Medication"] = Field(description="Entity type")
    text: str = Field(description="Extracted entity text")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence score")
    source_span: SourceSpan = Field(description="Character offset span in input text")
    source_span_validated: bool = Field(
        default=False,
        description="True if source_span.text matches input_text[start:end] per D-14"
    )


class EntityResponse(BaseModel):
    """
    Complete entity extraction response.

    Per D-04: All arrays must be present (use default []).
    Per D-05: Partial results allowed - valid entities returned even if some failed.
    Per D-06: Low confidence entities flagged separately.
    Per D-08: Detailed errors array for validation failures.
    """
    temporal_entities: list[TemporalEntity] = Field(
        default=[],
        description="Extracted temporal entities (dates, LOS indicators)"
    )
    clinical_entities: list[ClinicalEntity] = Field(
        default=[],
        description="Extracted clinical entities (diagnoses, medications)"
    )
    errors: list[str] = Field(
        default=[],
        description="Extraction or validation error messages per D-08"
    )
    low_confidence: list[TemporalEntity | ClinicalEntity] = Field(
        default=[],
        description="Entities with confidence below threshold per D-06"
    )
