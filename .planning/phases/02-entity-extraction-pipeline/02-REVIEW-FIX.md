---
phase: 02-entity-extraction-pipeline
fixed_at: 2026-06-12T15:00:00Z
fix_scope: critical_warning
findings_in_scope: 9
fixed: 9
skipped: 0
iteration: 1
status: all_fixed
---

# Phase 02: Code Review Fix Report

**Fixed:** 2026-06-12T15:00:00Z
**Scope:** Critical + Warning (9 findings)
**Status:** all_fixed

---

## Fixes Applied

### CR-01 — Temporal Prompt: Wrong Character Offsets

**File:** `src/prompts/temporal_prompt.py`
**Commit:** `fix(02): correct character offsets in temporal prompt few-shot examples`

All four span offsets were wrong, causing the LLM to learn incorrect offset arithmetic. Fixed:

| Example | Entity | Before | After |
|---------|--------|--------|-------|
| 1 | "15.03.2025" (Date) | start=11, end=21 | **start=12, end=22** |
| 2 | "18.01.2025" (Date) | start=59, end=69 | **start=58, end=68** |
| 2 | "4 Tage" (LOS) | start=127, end=133 | **start=122, end=128** |
| 3 | "5 Tagen" (LOS) | start=95, end=102 | **start=94, end=101** |

Verification: `text[start:end] == span_text` holds for all corrected offsets.

---

### CR-02 — Clinical Prompt: Wrong Character Offsets

**File:** `src/prompts/clinical_prompt.py`
**Commit:** `fix(02): correct character offsets in clinical prompt few-shot examples`

Seven span offsets were wrong across all three examples. Fixed:

| Example | Entity | Before | After |
|---------|--------|--------|-------|
| 1 | "Ibuprofen 600mg" (Medication) | start=38, end=53 | **start=39, end=54** |
| 2 | "Diabetes mellitus Typ 2 (E11.9)" (Diagnosis) | start=10, end=42 | **start=10, end=41** |
| 2 | "arterielle Hypertonie (I10)" (Diagnosis) | start=44, end=72 | **start=43, end=70** |
| 2 | "Metformin 1000mg" (Medication) | start=86, end=102 | **start=84, end=100** |
| 2 | "Ramipril 5mg" (Medication) | start=116, end=128 | **start=113, end=125** |
| 3 | "akuter Exazerbation einer COPD (J44.1)" (Diagnosis) | start=27, end=66 | **start=26, end=64** |
| 3 | "Amoxicillin 1g" (Medication) | start=92, end=106 | **start=90, end=104** |

---

### CR-03 — Date Validator Rejects Valid Short-Year Dates

**File:** `src/validation/validators.py`
**Commit:** `fix(02): accept DD.MM.YY dates and use date.today() for future-date check`

Added `%d.%m.%y` to the format loop so short-year dates advertised by the prompt are accepted:

```python
for fmt in ("%d.%m.%Y", "%d.%m.%y"):
    try:
        parsed_date = datetime.strptime(entity.text, fmt).date()
        break
    except ValueError:
        continue
```

---

### CR-04 — Flaky Test: Concurrent Mock Access Race Condition

**File:** `tests/test_extraction.py`
**Commit:** `fix(02): eliminate race condition in test_extract_all_entity_types`

Replaced the positional `side_effect` list with a callable that dispatches on the system-prompt content. The callable is deterministic regardless of thread scheduling order:

```python
def dispatch_by_prompt(messages=None, **kwargs):
    content = str(messages)
    if "temporal_entities" in content:
        return temporal_response
    return clinical_response
```

---

### WR-01 — All-or-Nothing Re-Deserialization Violates D-05

**File:** `src/api/extract.py`
**Commit:** `fix(02): per-entity deserialization to preserve partial results per D-05`

Replaced the list comprehensions with per-entity `try/except` blocks so a single bad entity dict logs an error without discarding all successfully extracted entities.

---

### WR-02 — `datetime.now()` Timezone-Naive

**File:** `src/validation/validators.py`
**Commit:** `fix(02): accept DD.MM.YY dates and use date.today() for future-date check` (combined with CR-03)

Replaced `datetime.now().replace(...)` with `date.today()`, removing the hidden TZ dependency in Docker deployments.

---

### WR-03 — Out-of-Bounds Span Entities Stored with `validated=False`

**Files:** `src/extraction/temporal.py`, `src/extraction/clinical.py`
**Commit:** `fix(02): reject entities with out-of-bounds spans instead of storing them`

Added `continue` after logging the out-of-bounds error so malformed LLM spans (e.g. `end=99999`) are dropped rather than stored with an unusable span value in the response.

---

### WR-04 — `print()` Used Instead of `loguru` Logger

**File:** `src/main.py`
**Commit:** `fix(02): replace print() with loguru logger in startup/shutdown handler`

Replaced two `print()` calls in the lifespan handler with `logger.warning()` and `logger.error()` per CLAUDE.md project standard.

---

### WR-05 — Off-by-One in `test_extract_response_schema` Mock

**File:** `tests/test_extraction.py`
**Commit:** `fix(02): correct off-by-one in test_extract_response_schema mock and add span assertion`

Corrected mock offsets from `start=11, end=21` to `start=12, end=22` and added a `source_span_validated` assertion so future regressions in span grounding are caught.

---

## Commits

```
eb585a7 fix(02): correct off-by-one in test_extract_response_schema mock and add span assertion
2bc61af fix(02): replace print() with loguru logger in startup/shutdown handler
3c38463 fix(02): reject entities with out-of-bounds spans instead of storing them
12775e5 fix(02): per-entity deserialization to preserve partial results per D-05
b76adec fix(02): eliminate race condition in test_extract_all_entity_types
ed27326 fix(02): accept DD.MM.YY dates and use date.today() for future-date check
6564b02 fix(02): correct character offsets in clinical prompt few-shot examples
decdf5d fix(02): correct character offsets in temporal prompt few-shot examples
```

---

_Fixed: 2026-06-12T15:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Scope: critical_warning_
