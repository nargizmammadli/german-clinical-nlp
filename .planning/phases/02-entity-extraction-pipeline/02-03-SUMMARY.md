---
phase: 02-entity-extraction-pipeline
plan: 03
subsystem: validation
tags: [validation, confidence-filtering, date-validation, german-nlp, tdd]
dependency_graph:
  requires: [02-01, 02-02]
  provides: [domain-validators, confidence-threshold-config, validated-extraction-endpoint]
  affects: [src/api/extract.py, src/validation/validators.py, src/config.py]
tech_stack:
  added: [datetime.strptime, DD.MM.YYYY date parsing]
  patterns: [tdd-red-green, fail-fast-validation, partial-results-per-D05]
key_files:
  created:
    - src/validation/validators.py
    - src/validation/__init__.py
    - tests/test_validation.py
  modified:
    - src/api/extract.py
    - src/config.py
    - src/extraction/temporal.py
    - src/extraction/clinical.py
decisions:
  - "D-20: Confidence filtering delegated to endpoint level (not extractors) to respect configurable CONFIDENCE_THRESHOLD env var"
  - "D-21: validate_date_not_future returns (bool, str|None) tuple for clean caller integration"
metrics:
  duration_seconds: 336
  tasks_completed: 3
  commits: 5
  files_created: 3
  files_modified: 4
  tests_added: 11
  completed_date: "2026-06-12"
---

# Phase 02 Plan 03: Validation and Confidence Filtering Summary

**One-liner:** Domain validators reject future dates and confidence filtering via configurable `CONFIDENCE_THRESHOLD` environment variable, with validation integrated into the extraction endpoint returning structured error arrays.

## What Was Built

Production-ready validation layer that enforces clinical domain rules on extracted entities. Impossible values (future dates) are rejected per VAL-02 with specific error messages per D-08. Low-confidence entities are separated into a dedicated `low_confidence` array per D-06, controlled by a configurable environment variable. The extraction endpoint now returns complete structured feedback for all failure modes.

### Task 1: Domain Validation Functions (TDD)

**Commits:** bb4a272 (RED), e149424 (GREEN)

Created `src/validation/validators.py` with two core functions:

- **validate_date_not_future(entity: TemporalEntity) -> tuple[bool, str | None]:**
  - Parses DD.MM.YYYY German date format (matching GGPONC corpus sample data)
  - Returns `(True, None)` for past dates and non-Date entities (LOS skip)
  - Returns `(False, "Date is in the future: {text}")` for future dates per D-08
  - Returns `(False, "Invalid date format: {text}")` for unparseable dates
  - T-02-07 mitigation: error messages expose only entity text and reason

- **filter_low_confidence(entities: list, threshold: float) -> tuple[list, list]:**
  - Splits entities into (high_confidence, low_confidence) by `confidence >= threshold`
  - Preserves original entity objects unchanged
  - Returns `([], [])` for empty input

9 tests written covering past dates, future dates, LOS skip, invalid format, threshold splitting, empty input, object preservation, all-above, all-below.

### Task 2: Confidence Threshold Configuration (TDD)

**Commit:** 2423139

Extended `src/config.py` following the established fail-fast pattern:

- `CONFIDENCE_THRESHOLD_RAW = os.getenv("CONFIDENCE_THRESHOLD", "0.5")` — default 0.5 per D-06
- Type conversion with `float()` and explicit ValueError for non-numeric values
- Range validation: raises `ValueError` if not 0.0 <= CONFIDENCE_THRESHOLD <= 1.0
- Validation happens at module import (fail-fast per D-09)
- `.env.example` updated with `CONFIDENCE_THRESHOLD=0.5` entry and explanation comment for portfolio reviewers

### Task 3: Integrate Validation into Extraction Endpoint (TDD)

**Commits:** b0f04fd (RED), eda0141 (GREEN)

Updated `src/api/extract.py` to integrate validation after extraction:

1. Deserialize extractor output dicts back to Pydantic models (`TemporalEntity`, `ClinicalEntity`)
2. Validate temporal entities with `validate_date_not_future` — future dates moved to `errors` array
3. Apply `filter_low_confidence` with `config.CONFIDENCE_THRESHOLD` to both temporal and clinical entities
4. Return `EntityResponse` with separated high/low confidence arrays and detailed errors

**Rule 1 fix (auto-fix):** Removed hardcoded `0.5` threshold from `temporal.py` and `clinical.py` extractors (lines that duplicated confidence filtering logic). Those extractors were adding entities to `low_confidence` with a hardcoded threshold that ignored the `CONFIDENCE_THRESHOLD` env var. The fix consolidates filtering at the endpoint level where the configurable value is used.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed hardcoded confidence filtering from extractors**
- **Found during:** Task 3 implementation (debugging why test_extract_filters_low_confidence unexpectedly passed RED)
- **Issue:** `temporal.py` and `clinical.py` each had `if entity.confidence < 0.5: result["low_confidence"].append(...)` — hardcoded threshold that ignored `CONFIDENCE_THRESHOLD` env var and caused entities to appear in BOTH `temporal_entities` and `low_confidence`
- **Fix:** Removed hardcoded filtering from both extractors; filtering delegated entirely to endpoint level using `config.CONFIDENCE_THRESHOLD`
- **Files modified:** `src/extraction/temporal.py`, `src/extraction/clinical.py`
- **Commit:** eda0141

**2. [Rule 1 - Bug] Fixed test_extract_filters_low_confidence to properly test RED phase**
- **Found during:** Task 3 RED phase — test passed before implementation (wrong reason)
- **Issue:** Original test didn't assert that low-confidence entity was absent from `temporal_entities` — it only asserted it appeared in `low_confidence` (which the hardcoded extractor provided)
- **Fix:** Added `assert "10.01.2023" not in high_conf_texts` assertion to properly test endpoint-level filtering
- **Files modified:** `tests/test_extraction.py`
- **Commit:** b0f04fd

## Decisions Made

**D-20: Confidence filtering delegated entirely to endpoint level**
- **Context:** Both extractors had hardcoded `confidence < 0.5` checks, duplicating logic with wrong boundary
- **Decision:** Remove extractor-level filtering; all confidence filtering happens in `extract.py` using `config.CONFIDENCE_THRESHOLD`
- **Rationale:** Single responsibility — extractors do extraction and source span validation only. Filtering is a business rule applied at the API boundary where the configurable value is available.

**D-21: validate_date_not_future returns (bool, str | None) tuple**
- **Context:** Plan specified this signature; alternatives considered (raise exception, return None/error)
- **Decision:** Tuple return for clean integration — callers can check `is_valid` and append `error_msg` to errors array without try/except
- **Rationale:** Consistent with D-05 (partial results) — no validation failure throws, all failures are captured as error messages

## Test Results

All 24 tests pass:

**New in this plan (11 tests):**
- `test_validate_date_not_future_accepts_past` — past date returns (True, None)
- `test_validate_date_not_future_rejects_future` — future date returns (False, error)
- `test_validate_date_not_future_ignores_los` — LOS entity skips validation
- `test_validate_date_not_future_invalid_format` — unparseable date returns error
- `test_filter_low_confidence_threshold_50` — 4 entities split at 0.5
- `test_filter_low_confidence_empty_input` — returns ([], [])
- `test_filter_low_confidence_preserves_entities` — objects unchanged
- `test_filter_low_confidence_all_above_threshold` — all in high_conf
- `test_filter_low_confidence_all_below_threshold` — all in low_conf
- `test_extract_rejects_future_dates` — future date in errors, not temporal_entities
- `test_extract_filters_low_confidence` — low-conf entity not in temporal_entities

**Regression check:** All 13 pre-existing tests continue to pass.

## Validation Accuracy on Sample Data

The `ggponc_samples.json` sample data uses DD.MM.YYYY format (e.g., "15.03.2025", "22.01.2025", "18.01.2025"). The `validate_date_not_future` parser handles this exact format. Sample dates are all in 2025 — currently past — so they would pass validation correctly. Future dates are impossible for historical clinical records, making this a reliable signal for LLM hallucination detection.

## Confidence Threshold Impact

With default `CONFIDENCE_THRESHOLD=0.5`:
- Entities confidence >= 0.5 appear in `temporal_entities` / `clinical_entities` (primary results)
- Entities confidence < 0.5 appear in `low_confidence` (secondary results for portfolio inspection)
- Portfolio reviewers can set `CONFIDENCE_THRESHOLD=0.3` to include more entities or `CONFIDENCE_THRESHOLD=0.8` for higher precision

## Error Message Clarity

Per D-08 and T-02-07, error messages are designed for portfolio reviewers:
- Future date: `"Date is in the future: 15.03.2027"` — clear, actionable
- Invalid format: `"Invalid date format: not-a-date"` — identifies the problematic text
- Extraction failure: `"temporal extraction failed: {exception}"` — identifies the extractor

No internal state, stack traces, or model implementation details are exposed in error messages.

## Known Stubs

None — all features fully implemented with real logic.

## Threat Flags

None — no new security-relevant surface introduced beyond plan's threat model. T-02-07 (validation error information disclosure) is mitigated: error messages expose only entity text and failure reason.

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| src/validation/validators.py | Domain validation functions | 90 |
| src/validation/__init__.py | Validation package marker | 0 |
| tests/test_validation.py | Validation logic tests (9 tests) | 128 |

## Files Modified

| File | Changes | Reason |
|------|---------|--------|
| src/api/extract.py | Added validation loop + confidence filtering | Task 3: integrate validation |
| src/config.py | Added CONFIDENCE_THRESHOLD env var with validation | Task 2: configurable threshold |
| src/extraction/temporal.py | Removed hardcoded confidence filtering | Rule 1 fix: defer to endpoint |
| src/extraction/clinical.py | Removed hardcoded confidence filtering | Rule 1 fix: defer to endpoint |

## Requirements Satisfied

- **VAL-02:** Domain validators reject impossible values (future dates) ✓
- **API-04:** Meaningful error messages for all failure modes ✓
- **ENTITY-05:** Entities include confidence scores (now properly filtered) ✓
- **ENTITY-06:** Confidence threshold filtering via `low_confidence` array ✓

## Success Criteria Met

1. ✓ Future dates rejected with specific error message per VAL-02 ("Date is in the future: {text}")
2. ✓ Confidence threshold filters entities into high_confidence and low_confidence arrays per D-06
3. ✓ CONFIDENCE_THRESHOLD configurable via environment variable with default 0.5
4. ✓ Validation errors returned in structured errors array per D-08, API-04
5. ✓ Partial results preserved — one entity's validation failure doesn't block others per D-05
6. ✓ All 24 tests pass (9 new validation tests + 2 new extraction tests + 13 regression)
7. ✓ Empty text input returns 422 with meaningful error (FastAPI Pydantic validation per API-04)

## Self-Check

### Created Files Verification

```
FOUND: src/validation/validators.py
FOUND: src/validation/__init__.py
FOUND: tests/test_validation.py
```

### Commits Verification

```
FOUND: bb4a272 (test: add failing tests for domain validation functions)
FOUND: e149424 (feat: implement domain validation functions)
FOUND: 2423139 (feat: add CONFIDENCE_THRESHOLD config)
FOUND: b0f04fd (test: add failing tests for validation integration)
FOUND: eda0141 (feat: integrate validation and confidence filtering)
```

## Self-Check: PASSED

All created files exist on disk. All commits exist in git history. All 24 tests pass.

---

**Plan Duration:** 336 seconds (6 minutes)  
**Completed:** 2026-06-12  
**Executor Model:** claude-sonnet-4-6
