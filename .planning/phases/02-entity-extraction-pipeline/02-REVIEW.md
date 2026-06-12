---
phase: 02-entity-extraction-pipeline
reviewed: 2026-06-12T14:05:00Z
depth: standard
files_reviewed: 15
files_reviewed_list:
  - docs/ARCHITECTURE.md
  - docs/__init__.py
  - src/api/extract.py
  - src/config.py
  - src/extraction/base.py
  - src/extraction/clinical.py
  - src/extraction/temporal.py
  - src/main.py
  - src/prompts/clinical_prompt.py
  - src/prompts/temporal_prompt.py
  - src/schemas/entities.py
  - src/validation/__init__.py
  - src/validation/validators.py
  - tests/test_extraction.py
  - tests/test_validation.py
findings:
  critical: 4
  warning: 5
  info: 3
  total: 12
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-06-12T14:05:00Z
**Depth:** standard
**Files Reviewed:** 15
**Status:** issues_found

## Summary

Reviewed the entity extraction pipeline implementation: two LLM-backed extractors (temporal, clinical), a plugin registry, a FastAPI extraction endpoint, Pydantic schemas, domain validators, few-shot prompts, and the test suite.

The core extraction logic is structurally sound. The plugin pattern is clean, the D-05 partial-results contract is attempted throughout, and source span validation (D-14/D-15) is implemented consistently in both extractors. However, four issues require attention before this code is reliable: (1) the few-shot prompt examples contain systematically wrong character offsets that will actively mislead the LLM into returning bad spans, (2) the date validator silently rejects valid short-year dates the prompt advertises it handles, (3) a flaky test has a race condition on concurrent mock access, and (4) the endpoint-level entity re-deserialization is all-or-nothing and can silently drop all results on a validation error — violating D-05.

---

## Critical Issues

### CR-01: Prompt Few-Shot Examples Have Wrong Character Offsets (Temporal Prompt)

**File:** `src/prompts/temporal_prompt.py:40-51`
**Issue:** Example 1 claims the date `"15.03.2025"` in `"Aufnahme am 15.03.2025..."` starts at offset 11, but Python character indexing places it at offset 12. `text[11:21]` returns `" 15.03.202"` (leading space, truncated), not `"15.03.2025"`. The same off-by-one appears in Example 3 for the LOS entity: the prompt claims `"5 Tagen"` spans `[95:102]` but the correct offsets are `[94:101]`.

These wrong offsets are the ground-truth examples fed to the LLM for few-shot learning. The model will learn to systematically offset its predicted spans by -1, causing `source_span_validated` to be `False` for most Date extractions — silently degrading the hallucination-detection feature that is a stated portfolio differentiator.

Independently, `test_extract_response_schema` (test line 131) sets `start=11, end=21` in its mock, replicating this same off-by-one. That test will pass because it does not assert `source_span_validated`, but it demonstrates the error propagated into test fixtures too.

**Fix:**
```python
# temporal_prompt.py Example 1 — correct offsets:
# Input: "Aufnahme am 15.03.2025. ..."
#         0         1         2
#         0123456789012345678901234
# "Aufnahme am " = 12 chars; date starts at 12, ends at 22
"source_span": {
    "start": 12,
    "end": 22,
    "text": "15.03.2025"
}

# Example 3 LOS — correct offsets:
# Input: "Stationäre Aufnahme 28.11.2024 wegen ... nach 5 Tagen."
# "5 Tagen" starts at 94, ends at 101
"source_span": {
    "start": 94,
    "end": 101,
    "text": "5 Tagen"
}
```

---

### CR-02: Prompt Few-Shot Examples Have Wrong Character Offsets (Clinical Prompt)

**File:** `src/prompts/clinical_prompt.py:56-66, 96-114`
**Issue:** Example 1 claims `"Ibuprofen 600mg"` starts at offset 38, but the `I` in `Ibuprofen` appears at index 39 in `"Diagnose: Lumbalgie (M54.5). Therapie: Ibuprofen 600mg 3x täglich."`. `text[38:53]` returns `" Ibuprofen 600m"` — again a leading space and truncated end.

Example 2 has multiple wrong offsets: the first diagnosis `end` is given as 42 but `text[10:42]` includes the trailing comma (`"Diabetes mellitus Typ 2 (E11.9),"`); the second diagnosis `start=44` clips the leading `a` in `"arterielle"` (`text[44:72]` = `"rterielle Hypertonie (I10). "`); both medications have incorrect starts and ends.

Example 3: diagnosis `start=27` clips the leading `a` in `"akuter"` (`text[27:66]` = `"kuter Exazerbation einer COPD (J44.1). "`); medication `start=92, end=106` gives `text[92:106]` = `"oxicillin 1g 3"`.

All few-shot examples in the clinical prompt are teaching the model incorrect offset arithmetic. The LLM will produce systematically wrong spans, and `source_span_validated` will be `False` for most clinical entities.

**Fix:** Recalculate all offsets in the few-shot examples. Use Python to verify: `assert text[start:end] == expected_text` before committing any prompt change. Correct values for Example 1:
```python
# "Diagnose: Lumbalgie (M54.5). Therapie: Ibuprofen 600mg 3x täglich."
#  0         1         2         3         4         5
# "Diagnose: " = 10 chars; "Lumbalgie (M54.5)" starts at 10, ends at 27
# "Therapie: Ibuprofen" — 'I' in Ibuprofen is at index 39, end=54
"source_span": {"start": 39, "end": 54, "text": "Ibuprofen 600mg"}
```

---

### CR-03: Date Validator Rejects Valid Short-Year Dates Advertised by the Prompt

**File:** `src/validation/validators.py:52`
**Issue:** `validate_date_not_future` uses `datetime.strptime(entity.text, "%d.%m.%Y")` — only the four-digit year format. `temporal_prompt.py` line 13 explicitly tells the LLM to extract `"DD.MM.YY"` (two-digit year) dates. When the LLM correctly extracts `"15.03.25"`, the validator returns `(False, "Invalid date format: 15.03.25")`, moving a legitimate extraction into the errors array. This is a contract violation between the prompt (which invites short-year dates) and the validator (which rejects them as invalid).

**Fix:** Parse both formats, or restrict the prompt to only request `DD.MM.YYYY`:
```python
# Option A: Try both formats
for fmt in ("%d.%m.%Y", "%d.%m.%y"):
    try:
        parsed_date = datetime.strptime(entity.text, fmt)
        break
    except ValueError:
        continue
else:
    return (False, f"Invalid date format: {entity.text}")

# Option B (simpler): Remove "DD.MM.YY, etc." from the prompt's entity type description
# and only advertise DD.MM.YYYY support.
```

---

### CR-04: Flaky Test — Concurrent Mock Access Race Condition

**File:** `tests/test_extraction.py:263-278`
**Issue:** `test_extract_all_entity_types` configures a `side_effect` list on the shared `mock_model` object, assuming the temporal extractor always consumes item 0 and the clinical extractor always consumes item 1. But `extract.py` runs both extractors concurrently via `asyncio.to_thread` (lines 97-104), which dispatches them to OS threads. `MagicMock.side_effect` uses a plain Python iterator internally; iterator `__next__` is not thread-safe under CPython's GIL with multiple threads contending. More fundamentally, the order in which the two threads call `create_chat_completion` is non-deterministic — the clinical extractor may call the mock before the temporal one, receiving the temporal response and vice versa. When that happens, each extractor parses the other extractor's key (`"clinical_entities"` vs `"temporal_entities"`), finds nothing, and the test fails with empty entity lists.

This is a genuine race condition. The test will pass most of the time (threads start in declaration order) but will fail intermittently under load or on slow systems.

**Fix:** Use separate mock objects for each extractor, or bypass the parallel path by mocking `asyncio.to_thread`:
```python
# Option: Give each extractor its own mock instance
temporal_mock = MagicMock()
clinical_mock = MagicMock()
temporal_mock.create_chat_completion.return_value = {...temporal response...}
clinical_mock.create_chat_completion.return_value = {...clinical response...}

# Patch extractor constructors to inject the correct mock
with patch("src.extraction.temporal.TemporalExtractor.__init__", ...) ...
# Or use a callable side_effect that dispatches by inspecting the messages parameter
```

---

## Warnings

### WR-01: All-or-Nothing Re-Deserialization Violates D-05 Partial-Results Contract

**File:** `src/api/extract.py:121-122`
**Issue:** After merging extractor results, the endpoint re-deserializes entity dicts into Pydantic models using list comprehensions:
```python
temporal_entities = [TemporalEntity(**e) for e in combined_result["temporal_entities"]]
clinical_entities = [ClinicalEntity(**e) for e in combined_result["clinical_entities"]]
```
If any single entity dict fails Pydantic validation here, the entire comprehension raises `ValidationError`, which is caught at line 151 and returns a completely empty `EntityResponse`. Every successfully extracted entity from both extractors is silently discarded. This directly violates D-05 ("Returns partial results even if some failed"). In practice the round-trip through `model_dump()` + Pydantic constructor is safe for well-formed data, but the failure mode is catastrophic when it does occur (all-or-nothing rather than per-entity).

**Fix:** Replace the list comprehensions with per-entity try/except to match the pattern used in the extractors:
```python
temporal_entities = []
for e in combined_result["temporal_entities"]:
    try:
        temporal_entities.append(TemporalEntity(**e))
    except (ValidationError, Exception) as err:
        combined_result["errors"].append(f"Entity deserialization failed: {err}")
```

---

### WR-02: `datetime.now()` Is Timezone-Naive — Future-Date Check Can Misbehave

**File:** `src/validation/validators.py:58`
**Issue:** `today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)` uses the server's local clock with no timezone. When deployed in a Docker container (typically UTC), this is fine for German clinical records. However if the container's timezone is set to anything other than CET/CEST, the "today" boundary shifts by up to ±14 hours. A date that is legitimately "today" in Germany may be flagged as future (or an actual future date may pass) depending on the timezone offset. This is a correctness issue, not just style.

**Fix:** Use `datetime.now(timezone.utc).date()` or, better, `date.today()` and compare `parsed_date.date()`:
```python
from datetime import datetime, date, timezone

parsed_date = datetime.strptime(entity.text, "%d.%m.%Y").date()
today = date.today()
if parsed_date > today:
    return (False, f"Date is in the future: {entity.text}")
```

---

### WR-03: `SourceSpan` Does Not Validate `end <= len(text)` — Unconstrained Upper Bound

**File:** `src/schemas/entities.py:19-27`
**Issue:** `SourceSpan.end` has `ge=0` and the `model_validator` checks `start < end`, but there is no upper bound on `end`. A malformed LLM response with `end=99999` creates a `SourceSpan` that passes Pydantic validation. The extractor's manual bounds check (`if 0 <= start < end <= len(text)`) correctly catches this and sets `source_span_validated=False`, but the unconstrained `SourceSpan` is still stored and returned in the response. A client consuming the API would receive `source_span.end=99999` for a 50-character text with no indication that the span is unusable.

**Fix:** The `SourceSpan` model cannot know `len(text)` (it is not in scope), so the schema itself cannot enforce this. The correct fix is to reject entities with out-of-bounds spans at the extractor level rather than storing them:
```python
if not (0 <= start < end <= len(text)):
    result["errors"].append(
        f"Entity '{entity_data.get('text','?')}' has out-of-bounds span [{start}:{end}] for text of length {len(text)}"
    )
    continue  # Skip this entity instead of storing it with validated=False
```

---

### WR-04: `print()` Used Instead of `loguru` Logger in `src/main.py`

**File:** `src/main.py:35, 38`
**Issue:** CLAUDE.md specifies `loguru` as the project logger ("Production logging with JSON output, rotation, async support"). The startup/shutdown lifecycle handler uses `print()` for both informational messages and errors. This means model loading failures produce unstructured console output that is invisible to any log aggregation, rotation, or filtering configured via loguru.

**Fix:**
```python
from loguru import logger

# Replace:
print("Warning: llama-cpp-python not installed, model not loaded")
# With:
logger.warning("llama-cpp-python not installed, model not loaded")

# Replace:
print(f"ERROR: Failed to load model: {e}")
# With:
logger.error(f"Failed to load model: {e}")
```

---

### WR-05: Off-by-One in `test_extract_response_schema` Mock Produces Silent False Negatives

**File:** `tests/test_extraction.py:131`
**Issue:** The mock for `test_extract_response_schema` returns `start=11, end=21` for the text `"Aufnahme am 15.03.2025. Patient wurde untersucht."`. The correct offsets are `start=12, end=22` (`text[12:22] == "15.03.2025"`). With the wrong offsets, `source_span_validated` will be `False` on the returned entity. The test does not assert `source_span_validated`, so it passes regardless. This means the test provides no coverage for the span validation path and will not catch future regressions in span grounding logic.

**Fix:**
```python
# Correct the mock offsets:
"source_span": {"start": 12, "end": 22, "text": "15.03.2025"}

# Add assertion to actually test the validated flag:
assert entity.get("source_span_validated") is True, (
    "source_span_validated should be True when offsets correctly point to entity text"
)
```

---

## Info

### IN-01: `low_confidence` Key in Extractor Result Dict Is Dead Code

**File:** `src/extraction/temporal.py:51`, `src/extraction/clinical.py:51`
**Issue:** Both extractors initialize `result["low_confidence"] = []` and never populate it (a comment on line 113 of each file explicitly says filtering is done at endpoint level). The endpoint also ignores this key (line 117 in `extract.py` says `"low_confidence from extractors is ignored"`). The key exists in the dict, is allocated, and is silently dropped. This adds confusion when reading the extractors, because a reader must trace through to the endpoint to understand why the key is initialized but unused.

**Fix:** Remove `"low_confidence": []` from both extractor `result` dicts. The key is not part of the contract between extractor and endpoint — the comment on line 117 of `extract.py` confirms this.

---

### IN-02: Unused Variable `name` in List Comprehension

**File:** `src/api/extract.py:99`
**Issue:** The comprehension `[asyncio.to_thread(extractor.extract, request_body.text) for name, extractor in extractors]` unpacks `name` but never uses it inside the comprehension. The name is later retrieved via `extractors[i][0]` at line 111. Convention is to use `_` for intentionally unused loop variables.

**Fix:**
```python
tasks = [
    asyncio.to_thread(extractor.extract, request_body.text)
    for _, extractor in extractors
]
```

---

### IN-03: No `conftest.py` — Tests Depend on `.env` File Existence at Import Time

**File:** `src/config.py:20-25` (imported by `src/main.py`)
**Issue:** `src/config.py` validates `MODEL_PATH` and verifies the model file exists at module import time. `src/main.py` imports `src/config`, so every test that does `from src.main import app` will fail with `EnvironmentError` or `FileNotFoundError` if `.env` is absent or `MODEL_PATH` points to a nonexistent file. The project relies on a checked-in `models/test.gguf` placeholder file and a `.env` file (not checked in) to make tests runnable. There is no `conftest.py` to set up the environment programmatically, making the test suite fragile in CI/CD environments without `.env`.

**Fix:** Add a `tests/conftest.py` that sets the minimum required environment variables before any imports occur:
```python
# tests/conftest.py
import os
from pathlib import Path

# Set test environment before src.config is imported
os.environ.setdefault("MODEL_PATH", "models/test.gguf")
os.environ.setdefault("CONFIDENCE_THRESHOLD", "0.5")
```

---

_Reviewed: 2026-06-12T14:05:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
