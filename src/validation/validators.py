"""
Domain validation functions for clinical entity extraction.

Implements validators per D-06, D-07, D-08:
  - D-06: filter_low_confidence splits entities by configurable threshold
  - D-07: validate_date_not_future rejects impossible future dates
  - D-08: detailed validation error messages contain entity text and failure reason

Per T-02-07 (threat mitigation): error messages expose only entity text and
validation failure reason — no internal state, model details, or stack traces.
"""

from datetime import datetime, date

from src.schemas.entities import TemporalEntity


def validate_date_not_future(entity: TemporalEntity) -> tuple[bool, str | None]:
    """
    Validate that a temporal date entity is not in the future.

    Per D-07: Only validates entities of type "Date". LOS (length-of-stay)
    entities are not dates and pass validation unconditionally.

    Per D-08: Returns specific error message containing the entity text
    so callers can populate the errors array with actionable context.

    Args:
        entity: TemporalEntity with type ("Date" or "LOS") and text field.

    Returns:
        (True, None) if entity is valid (past/today date or non-Date type).
        (False, error_message) if date is in the future or unparseable.

    Examples:
        >>> # Past date accepted
        >>> entity = TemporalEntity(type="Date", text="15.03.2023", ...)
        >>> validate_date_not_future(entity)
        (True, None)

        >>> # Future date rejected
        >>> entity = TemporalEntity(type="Date", text="15.03.2027", ...)
        >>> validate_date_not_future(entity)
        (False, "Date is in the future: 15.03.2027")
    """
    # Per D-07: Only validate Date entities; LOS indicators are not calendar dates
    if entity.type != "Date":
        return (True, None)

    # Parse German date formats DD.MM.YYYY and DD.MM.YY (both advertised by the prompt)
    parsed_date = None
    for fmt in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            parsed_date = datetime.strptime(entity.text, fmt).date()
            break
        except ValueError:
            continue
    if parsed_date is None:
        # Per D-08: include entity text in error message for actionable context
        return (False, f"Invalid date format: {entity.text}")

    # Use date.today() for timezone-safe comparison (no clock/TZ dependency)
    if parsed_date > date.today():
        return (False, f"Date is in the future: {entity.text}")

    return (True, None)


def filter_low_confidence(
    entities: list,
    threshold: float
) -> tuple[list, list]:
    """
    Split entities into high-confidence and low-confidence lists by threshold.

    Per D-06: Entities with confidence >= threshold go to the high-confidence
    list (returned in main temporal_entities / clinical_entities arrays).
    Entities with confidence < threshold go to the low-confidence list
    (returned in the low_confidence array in EntityResponse).

    Entities are NOT filtered out — they are preserved in the appropriate
    array so portfolio reviewers can inspect the full extraction output
    and adjust the CONFIDENCE_THRESHOLD environment variable to experiment.

    Args:
        entities: List of TemporalEntity or ClinicalEntity objects.
        threshold: Float 0.0-1.0 boundary value. Entities >= threshold are
                   considered high-confidence.

    Returns:
        (high_confidence_entities, low_confidence_entities) tuple.
        Both lists preserve the original entity objects unchanged.
        If input is empty, returns ([], []).

    Examples:
        >>> entities = [entity_0_3, entity_0_5, entity_0_7, entity_0_9]
        >>> high, low = filter_low_confidence(entities, threshold=0.5)
        >>> len(high)  # 0.5, 0.7, 0.9
        3
        >>> len(low)   # 0.3
        1
    """
    if not entities:
        return ([], [])

    high_confidence = [e for e in entities if e.confidence >= threshold]
    low_confidence = [e for e in entities if e.confidence < threshold]

    return (high_confidence, low_confidence)
