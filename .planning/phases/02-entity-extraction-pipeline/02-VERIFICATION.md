---
phase: 02-entity-extraction-pipeline
verified: 2026-06-12T12:30:00Z
status: human_needed
score: 5/5 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Run server with a real GGUF model and POST German clinical text"
    expected: "Response contains temporal_entities (dates + LOS), clinical_entities (diagnoses + medications), source_span offsets in each entity, errors array empty for valid input"
    why_human: "All extraction tests use mocked LLM. Real inference from llama-cpp-python with a GGUF model cannot be verified without downloading and running the ~40GB model. Structured output quality, German prompt effectiveness, and actual source span accuracy require live model testing."
  - test: "Verify /docs (OpenAPI) reflects complete EntityResponse schema including all four entity type arrays"
    expected: "FastAPI Swagger UI shows POST /extract with EntityResponse schema showing temporal_entities, clinical_entities, errors, low_confidence arrays with nested SourceSpan and entity fields"
    why_human: "OpenAPI doc rendering requires a running server; cannot be verified via static analysis."
  - test: "Set CONFIDENCE_THRESHOLD=0.3 and POST text to /extract, observe low_confidence array populated"
    expected: "Entities with confidence between 0.3 and 0.5 appear in low_confidence array, not in main entity arrays"
    why_human: "Environment variable override behavior requires a live server run; unit tests mock the config value but do not test the .env loading path end-to-end."
---

# Phase 02: Entity Extraction Pipeline — Verification Report

**Phase Goal:** Complete extraction pipeline that extracts all entity types from German clinical text with validated JSON output  
**Stated Goal (per prompt):** Working local LLM deployment with health monitoring and German clinical sample data — plus a complete extraction pipeline with all four entity types (dates, diagnoses, medications, length-of-stay) running in parallel, with production-ready validation that rejects impossible values and provides detailed error feedback.  
**Verified:** 2026-06-12T12:30:00Z  
**Status:** human_needed  
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can POST German clinical text to /extract and receive JSON with dates, diagnoses, medications, and length-of-stay indicators | VERIFIED | `src/api/extract.py`: POST /extract registered via `extract.router`; `test_extract_all_entity_types` passes with all 4 entity types in response; parallel extraction via `asyncio.gather` confirmed. |
| 2 | Each extracted entity includes confidence score and source text span (evidence grounding) | VERIFIED | `src/schemas/entities.py`: `TemporalEntity` and `ClinicalEntity` both have `confidence: float = Field(ge=0.0, le=1.0)` and `source_span: SourceSpan` (required, no default). `SourceSpan` has `start`, `end`, `text` fields with `start < end` enforced by `@model_validator`. |
| 3 | Pydantic validation rejects impossible values (future dates, invalid formats, hallucinated entities without source spans) | VERIFIED | `src/validation/validators.py`: `validate_date_not_future` rejects future dates returning `(False, "Date is in the future: {text}")`. `SourceSpan.validate_span_order` rejects `start >= end`. `source_span` is a required field — entities without spans fail Pydantic validation. All 9 validation tests pass. |
| 4 | API returns meaningful error messages for invalid requests (empty text, unsupported formats, validation failures) | VERIFIED | `ExtractionRequest.text = Field(min_length=1)` returns 422 for empty text (confirmed by `test_extract_empty_text_error`). Future date rejection returns `"Date is in the future: {text}"` in errors array. Extractor failures return structured `"{name} extraction failed: {msg}"` messages. No stack traces exposed. |
| 5 | Developer can add a new entity type by creating a single extractor plugin without modifying core pipeline code | VERIFIED | `src/extraction/base.py`: `extractor_registry`, `register_extractor` decorator, `BaseExtractor` ABC all present and substantive (70 lines). `@register_extractor("temporal")` and `@register_extractor("clinical")` prove the pattern. `docs/ARCHITECTURE.md` has "Adding a New Entity Type" section with 7-step guide and complete `SymptomExtractor` example. |

**Score:** 5/5 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/schemas/entities.py` | Pydantic models for entity extraction | VERIFIED | 91 lines (min: 60). Exports `SourceSpan`, `TemporalEntity`, `ClinicalEntity`, `EntityResponse`. `start < end` constraint active. `confidence` ge=0.0 le=1.0. |
| `src/extraction/base.py` | BaseExtractor abstract class with registry | VERIFIED | 70 lines (min: 40). `extractor_registry: Dict[str, Type[BaseExtractor]] = {}`, `register_extractor` decorator, `BaseExtractor(ABC)` with abstract `extract()`. |
| `src/extraction/temporal.py` | Temporal entity extractor (dates + LOS) | VERIFIED | 130 lines (min: 80). `@register_extractor("temporal")`, calls `self.model.create_chat_completion`, validates source spans, sets `source_span_validated` boolean. |
| `src/extraction/clinical.py` | Clinical entity extractor (diagnoses + medications) | VERIFIED | 130 lines (min: 80). `@register_extractor("clinical")`, same span validation pattern as temporal extractor. |
| `src/api/extract.py` | POST /extract endpoint | VERIFIED | 164 lines (min: 50). `response_model=EntityResponse`, `ExtractionRequest.text` with `min_length=1`, asyncio.gather parallel execution, validation integration. |
| `src/validation/validators.py` | Domain validators for impossible values | VERIFIED | 105 lines (min: 50). Exports `validate_date_not_future`, `filter_low_confidence`. Both substantive with real logic. |
| `src/prompts/temporal_prompt.py` | German temporal extraction prompt | VERIFIED | 125 lines. `TEMPORAL_EXTRACTION_PROMPT` with system message, 3 German few-shot examples from GGPONC patterns, abbreviation glossary, JSON schema instructions. |
| `src/prompts/clinical_prompt.py` | German clinical entity extraction prompt | VERIFIED | 152 lines (min: 40). `CLINICAL_EXTRACTION_PROMPT` with ICD-10 examples (Lumbalgie M54.5), medication dosage examples (Ibuprofen 600mg). |
| `tests/test_extraction.py` | End-to-end extraction tests | VERIFIED | 404 lines (min: 100). 9 tests covering all entity types, parallel extraction, future date rejection, confidence filtering. All pass. |
| `tests/test_validation.py` | Validation logic tests | VERIFIED | 128 lines (min: 80). 9 tests covering past/future dates, LOS skip, invalid format, threshold filtering, edge cases. All pass. |
| `docs/ARCHITECTURE.md` | Plugin pattern documentation (EXT-02) | VERIFIED | 405 lines. Contains "Adding a New Entity Type" (7-step guide), `SymptomExtractor` concrete example, Plugin Pattern section, Existing Extractors section. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `src/api/extract.py` | `src/extraction/base.py` | `extractor_registry.get("temporal")` | WIRED | `from src.extraction.base import extractor_registry` present; `extractor_registry.get("temporal")` and `.get("clinical")` both used at lines 78-79. |
| `src/api/extract.py` | `src/extraction/clinical.py` | `extractor_registry["clinical"]` | WIRED | `from src.extraction import clinical` import ensures decorator fires; `extractor_registry.get("clinical")` used. |
| `src/api/extract.py` | asyncio | `asyncio.gather(*tasks, return_exceptions=True)` | WIRED | `import asyncio` present; `asyncio.to_thread(extractor.extract, text)` wraps both extractors; `await asyncio.gather(*tasks, return_exceptions=True)` on line 104. |
| `src/api/extract.py` | `src/schemas/entities.py` | `response_model=EntityResponse` | WIRED | `@router.post("/extract", response_model=EntityResponse)` confirmed. |
| `src/api/extract.py` | `src/validation/validators.py` | `validate_date_not_future`, `filter_low_confidence` | WIRED | Both imported and called in `extract_entities`; `config.CONFIDENCE_THRESHOLD` used as threshold. |
| `src/extraction/temporal.py` | `request.app.state.model` | `self.model.create_chat_completion` | WIRED | Model injected via constructor (`self.model = model` in `BaseExtractor.__init__`); `self.model.create_chat_completion(...)` called in `extract()`. |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `src/api/extract.py` → `EntityResponse` | `high_conf_temporal`, `high_conf_clinical` | `asyncio.gather` results → `validate_date_not_future` → `filter_low_confidence` | Yes — extraction results from `extractor.extract()` calls flow through validation and filtering to `EntityResponse`. No hardcoded empty values in the success path. | FLOWING |
| `src/extraction/temporal.py` | `result["temporal_entities"]` | `self.model.create_chat_completion(...)` → `json.loads(content)` → entity validation loop | Yes — LLM response parsed, entities validated, appended to result dict (requires real model at runtime) | FLOWING (mocked in tests) |
| `src/extraction/clinical.py` | `result["clinical_entities"]` | `self.model.create_chat_completion(...)` → `json.loads(content)` → entity validation loop | Yes — identical pattern to temporal extractor | FLOWING (mocked in tests) |

Note: Real data flow from LLM to response is wired correctly at the code level. Actual inference requires a GGUF model — see Human Verification section.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Pydantic schema validation | `python -c "from src.schemas.entities import ..."` | `SCHEMA_VALID: Date`, `SPAN_VALIDATION: PASS`, `CONFIDENCE_VALIDATION: PASS` | PASS |
| Extractor registry populated | `python -c "from src.extraction.temporal import ...; assert 'temporal' in extractor_registry"` | `REGISTRY: PASS - both extractors registered` | PASS |
| Domain validator: future date rejection | `python -c "validate_date_not_future(entity_future)"` | `(False, "Date is in the future: 15.03.2027")` | PASS |
| Domain validator: confidence filtering | `python -c "filter_low_confidence([0.3, 0.5, 0.7], 0.5)"` | `2 high, 1 low` | PASS |
| All key patterns in extract.py | Static grep | `asyncio imported`, `asyncio.gather used`, `asyncio.to_thread used`, `return_exceptions=True set`, `extractor_registry used`, `validate_date_not_future`, `filter_low_confidence`, `config.CONFIDENCE_THRESHOLD`, `response_model=EntityResponse` — all PASS | PASS |
| Extraction test suite | `pytest tests/test_extraction.py -v` | 9/9 passed, 0 failures | PASS |
| Validation test suite | `pytest tests/test_validation.py -v` | 9/9 passed, 0 failures | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|------------|-------------|-------------|--------|----------|
| ENTITY-01 | 02-01 | Extracts dates from German clinical text with confidence scores | SATISFIED | `TemporalExtractor` with `type="Date"`, `confidence` field; `test_extract_temporal_entities_dates` passes |
| ENTITY-02 | 02-02 | Extracts diagnoses with confidence scores | SATISFIED | `ClinicalExtractor` with `type="Diagnosis"`; `test_extract_clinical_entities_diagnosis` passes |
| ENTITY-03 | 02-02 | Extracts medications with confidence scores | SATISFIED | `ClinicalExtractor` with `type="Medication"`; `test_extract_clinical_entities_medication` passes |
| ENTITY-04 | 02-01 | Extracts length-of-stay indicators with confidence scores | SATISFIED | `TemporalExtractor` with `type="LOS"`; `test_extract_temporal_entities_los` passes |
| ENTITY-05 | 02-01 | Each entity includes source text span | SATISFIED | `source_span: SourceSpan` required field in both entity models; no default value |
| ENTITY-06 | 02-01 | Extraction output is validated JSON conforming to Pydantic schemas | SATISFIED | `response_model=EntityResponse` on endpoint; all entities deserialized through Pydantic validators |
| VAL-01 | 02-01 | Pydantic schema validation enforces entity structure | SATISFIED | `SourceSpan.validate_span_order` rejects `start >= end`; `confidence` range 0.0-1.0 enforced |
| VAL-02 | 02-03 | Domain validators reject impossible values (future dates, invalid formats) | SATISFIED | `validate_date_not_future` rejects future dates and unparseable formats; integrated into endpoint |
| VAL-03 | 02-01 | Confidence scores included for each extracted entity | SATISFIED | `confidence: float = Field(ge=0.0, le=1.0)` in both `TemporalEntity` and `ClinicalEntity` |
| API-01 | 02-01 | POST /extract endpoint accepts German clinical text and returns extracted entities | SATISFIED | `@router.post("/extract", response_model=EntityResponse)` in `src/api/extract.py`; included in `src/main.py` |
| API-04 | 02-01/03 | Meaningful error responses for invalid requests | SATISFIED | Empty text → 422 (Pydantic min_length); future dates → `"Date is in the future: {text}"`; extraction failure → `"{name} extraction failed: {msg}"` |
| EXT-01 | 02-01/02 | Entity extraction follows plugin pattern | SATISFIED | `extractor_registry`, `@register_extractor`, `BaseExtractor(ABC)` working; both extractors registered; `test_extract_all_entity_types` passes |
| EXT-02 | 02-02 | Documentation demonstrates how to add a new entity type | SATISFIED | `docs/ARCHITECTURE.md` has 7-step guide and complete `SymptomExtractor` example |

All 13 requirements assigned to Phase 2 are SATISFIED.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/config.py` | 53 | `raise FileNotFoundError` at module import — config fails when MODEL_PATH points to nonexistent file | INFO | Expected behavior (fail-fast per D-09). Test imports of modules that transitively import `src.config` will fail without a `.env` file or `MODEL_PATH` env var. Tests in `test_extraction.py` bypass this by importing `src.main` and mocking `app.state.model` after the app is constructed. No blocker. |

No `TBD`, `FIXME`, or `XXX` markers found in any modified file. No unreferenced stubs.

---

### Human Verification Required

#### 1. Live LLM Inference — German Extraction Quality

**Test:** Set up `.env` with a valid GGUF model path, start server with `uvicorn src.main:app --reload`, then POST:
```
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "Aufnahme am 15.03.2025. Diagnose: Lumbalgie (M54.5). Therapie: Ibuprofen 600mg. Verweildauer: 4 Tage."}'
```
**Expected:** Response JSON with `temporal_entities` containing a Date entity (`15.03.2025`) and LOS entity (`4 Tage`); `clinical_entities` containing a Diagnosis entity (`Lumbalgie`) and Medication entity (`Ibuprofen 600mg`); `source_span` offsets that correctly index into the input string; `errors` array empty.  
**Why human:** All test coverage uses mocked `model.create_chat_completion`. Real GGUF model inference quality (German prompt effectiveness, source span accuracy, ICD code extraction) cannot be verified via static analysis or unit tests.

#### 2. OpenAPI Documentation Completeness

**Test:** Navigate to `http://localhost:8000/docs` with a running server.  
**Expected:** POST /extract appears with full `EntityResponse` schema showing `temporal_entities` (array of `TemporalEntity`), `clinical_entities` (array of `ClinicalEntity`), `errors` (string array), `low_confidence` (union array). Entity schemas show nested `SourceSpan` with `start`, `end`, `text`. FastAPI auto-generates this — verify it renders correctly and all types are shown.  
**Why human:** Requires a running server. FastAPI docs rendering and display correctness is a visual/functional check.

#### 3. CONFIDENCE_THRESHOLD Environment Variable End-to-End

**Test:** In `.env`, set `CONFIDENCE_THRESHOLD=0.8`. Start server, POST text and observe `low_confidence` array.  
**Expected:** Entities with confidence between 0.5 and 0.8 appear in `low_confidence` instead of `temporal_entities`/`clinical_entities`. Changing to `CONFIDENCE_THRESHOLD=0.3` should move those entities back to the main arrays.  
**Why human:** Unit tests mock `src.config.CONFIDENCE_THRESHOLD` directly (via `unittest.mock.patch`). The actual `.env` loading path — `load_dotenv()` → `os.getenv("CONFIDENCE_THRESHOLD", "0.5")` → float conversion — is not exercised by the test suite.

---

### Gaps Summary

No gaps found. All 5 roadmap success criteria are verified in the codebase. All 13 Phase 2 requirements are satisfied by the implemented code. All 18 tests (9 extraction + 9 validation) pass. No debt markers present in modified files.

The phase goal is achieved: a complete extraction pipeline with all four entity types (dates, diagnoses, medications, length-of-stay), parallel execution via `asyncio.gather`, production-ready Pydantic validation rejecting future dates and invalid spans, configurable confidence threshold filtering, and a plugin pattern that allows adding new entity types without modifying core code.

The three human verification items are runtime/quality checks requiring a live GGUF model or running server — they do not indicate code defects but are necessary to confirm real-world extraction quality.

---

_Verified: 2026-06-12T12:30:00Z_  
_Verifier: Claude (gsd-verifier)_
