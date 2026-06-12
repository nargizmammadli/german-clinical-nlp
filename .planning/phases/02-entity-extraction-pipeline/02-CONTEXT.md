# Phase 02: Entity Extraction Pipeline - Context

**Gathered:** 2026-06-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete extraction pipeline that processes German clinical text and returns structured JSON with dates, diagnoses, medications, and length-of-stay indicators. Each entity includes confidence scores, source text spans (evidence grounding), and passes Pydantic validation. The architecture is extensible via plugin pattern, allowing developers to add new entity types without modifying core pipeline code.

</domain>

<decisions>
## Implementation Decisions

### Prompt Engineering
- **D-01:** Use hybrid prompt approach — two specialized prompts: (1) temporal entities (dates + LOS indicators), (2) clinical entities (diagnoses + medications)
- **D-02:** Few-shot learning with 2-3 German clinical examples in each prompt
- **D-03:** Include explicit German medical abbreviation handling in prompt instructions (Pat., OPS, ICD, etc.)
- **D-04:** Enforce required fields with empty arrays in JSON schema — all entity type arrays must be present, can be empty [] if none found

### Validation Strategy
- **D-05:** Allow partial results — return valid entities with 'errors' array for validation failures, don't fail entire extraction
- **D-06:** Filter entities below configurable confidence threshold via environment variable (e.g., CONFIDENCE_THRESHOLD=0.5), move to 'low_confidence' array
- **D-07:** Minimal format validators — dates must be valid ISO + past, confidence 0.0-1.0, source spans must exist in input text
- **D-08:** Detailed validation error responses — return JSON with 'valid_entities', 'invalid_entities' (with reasons), 'errors' array with specific Pydantic messages

### Extractor Plugin Architecture
- **D-09:** Base class with registry pattern — abstract BaseExtractor with extract() method, auto-register via decorator
- **D-10:** Each extractor owns its schema — Pydantic model lives with extraction logic in same file
- **D-11:** Dependency injection via constructor — pipeline passes model instance to extractor.__init__()
- **D-12:** Parallel async execution — use asyncio.gather() to run both extractors concurrently

### Source Span Grounding
- **D-13:** Character offsets representation — zero-based {start, end, text} format per ENTITY-05
- **D-14:** Exact string match validation — verify input_text[start:end] == entity.source_text
- **D-15:** Flag ungrounded entities with warning but include — add source_span_validated: false flag for entities without valid spans
- **D-16:** LLM provides spans directly — include source_span (start, end, text) in JSON schema for structured output

### Claude's Discretion
- Specific German medical abbreviations list to include (beyond common ones mentioned)
- Exact confidence threshold default value (within 0.4-0.6 range)
- BaseExtractor abstract method signatures and registry implementation details
- Error message wording and validation feedback specificity
- How to structure the 'low_confidence' array in responses

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Requirements
- `.planning/REQUIREMENTS.md` — Phase 2 requirements: ENTITY-01 through ENTITY-06, VAL-01 through VAL-03, API-01, API-04, EXT-01, EXT-02
- `.planning/PROJECT.md` — Core value proposition, constraints, target audience (healthcare AI developers, technical recruiters)
- `.planning/ROADMAP.md` — Phase 2 goal and success criteria

### Prior Phase Context
- `.planning/phases/01-foundation-core-infrastructure/01-CONTEXT.md` — Phase 1 decisions: startup model loading (D-01), environment config (D-07, D-08, D-09), error handling (D-05, D-06)

### Technical Stack
- `CLAUDE.md` — Technology stack section: llama-cpp-python structured output, Pydantic v2 validation, FastAPI async patterns

No external specs — requirements fully captured in references above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **FastAPI app structure** (`src/main.py`) — Lifespan manager pattern for startup initialization, router inclusion pattern
- **Config module** (`src/config.py`) — Environment validation with fail-fast, relative path resolution, security validation (path traversal prevention)
- **Model loader** (`src/models/loader.py`) — Llama initialization with context window, error handling, timing instrumentation
- **Health endpoint pattern** (`src/api/health.py`) — Model readiness check with 503 responses, timestamp inclusion

### Established Patterns
- **Environment-based configuration** — All settings via environment variables, validated at startup per D-07, D-08, D-09
- **Fail-fast validation** — Invalid config raises clear errors before app starts per D-09
- **Router organization** — Endpoints grouped in `src/api/` with router includes per domain

### Integration Points
- **app.state.model** — Model instance accessible via request.app.state.model in all endpoints
- **Router registration** — New /extract endpoint will be added via router include in main.py
- **Pydantic response models** — FastAPI automatic validation and OpenAPI doc generation (API-05)
- **Startup lifespan** — Model and extractors can be initialized in lifespan context manager

</code_context>

<specifics>
## Specific Ideas

**Hybrid Prompt Design:**
- Temporal prompt: Extract dates (admission, discharge, procedure dates) + LOS indicators (Verweildauer, Aufenthaltsdauer) together since they're often contextually related
- Clinical prompt: Extract diagnoses (ICD codes, condition names) + medications (prescriptions, dosages) together for better clinical context understanding

**German Medical Abbreviations to Handle Explicitly:**
- Common: Pat. (Patient), Diag. (Diagnose), Med. (Medikament), OP (Operation)
- Codes: ICD (diagnosis classification), OPS (procedure codes), ATC (medication codes)
- Time: Aufnahme (admission), Entlassung (discharge), Verweildauer (length of stay)

**Few-Shot Example Structure:**
- Include 2-3 annotated GGPONC samples in each prompt showing expected entity structure
- Examples should demonstrate confidence scoring and proper source span extraction
- Cover edge cases: negated diagnoses, relative dates, medication dosages

**Confidence Threshold Implementation:**
- Default CONFIDENCE_THRESHOLD=0.5 if not set
- Entities below threshold go to 'low_confidence' array in response (not filtered entirely)
- Portfolio reviewers can experiment with threshold adjustment via environment variable

**Source Span Validation Flow:**
1. LLM returns entity with source_span {start, end, text}
2. Validate: input_text[start:end] == entity.source_span.text
3. If match: source_span_validated = true
4. If no match: source_span_validated = false, flag as potentially hallucinated but still include

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-Entity Extraction Pipeline*
*Context gathered: 2026-06-12*
