# Phase 02: Entity Extraction Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-12
**Phase:** 02-entity-extraction-pipeline
**Areas discussed:** Prompt engineering approach, Validation strategy, Extractor plugin architecture, Source span grounding

---

## Prompt Engineering Approach

### Question 1: Unified vs Separate Prompts

| Option | Description | Selected |
|--------|-------------|----------|
| Single unified prompt | One prompt extracts all entities in a single LLM call. Faster (one inference), entities share context, consistent JSON structure. Risk: longer output, more complex schema validation. | |
| Separate prompts per entity type | Four separate LLM calls (dates, diagnoses, medications, LOS). Simpler validation per entity, easier to debug, can optimize each prompt. Slower (4x inference time), loses cross-entity context. | |
| Hybrid: clinical entities unified, temporal separate | Two prompts: (1) dates + LOS indicators together (temporal), (2) diagnoses + medications together (clinical). Balances performance and maintainability. | ✓ |

**User's choice:** Hybrid: clinical entities unified, temporal separate
**Notes:** Balances the benefits of context sharing within related entity types while keeping prompts manageable.

### Question 2: Few-shot vs Zero-shot

| Option | Description | Selected |
|--------|-------------|----------|
| Few-shot with German clinical examples | Include 2-3 example German clinical texts with annotated entity extractions in the prompt. Better accuracy for domain-specific patterns, helps with German medical terminology. Uses more context window tokens. | ✓ |
| Zero-shot instructions only | Rely on model's pre-trained knowledge with clear instructions. Faster, less context usage, easier to update. May miss German clinical nuances or edge cases. | |
| You decide | Claude picks based on model performance during implementation. | |

**User's choice:** Few-shot with German clinical examples (Recommended)
**Notes:** Prioritizes accuracy for domain-specific German clinical patterns over context window efficiency.

### Question 3: German Medical Abbreviations

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit abbreviation handling | Include common German medical abbreviations in prompt instructions (z.B., Pat. = Patient, OPS = operation code, ICD = diagnosis code, etc.). More explicit guidance for the model. | ✓ |
| Trust model's medical knowledge | Rely on Llama 3.3's pre-trained medical knowledge without explicit abbreviation lists. Simpler prompts, but may miss domain-specific German abbreviations. | |
| You decide | Claude chooses based on observed accuracy during implementation. | |

**User's choice:** Explicit abbreviation handling
**Notes:** Ensures consistent handling of German medical abbreviations specific to clinical documentation.

### Question 4: JSON Schema Strictness

| Option | Description | Selected |
|--------|-------------|----------|
| Required fields with empty arrays | All entity type arrays are required in the output, but can be empty [] if no entities found. Predictable response structure, easier validation. Model must always return complete schema. | ✓ |
| Optional fields for sparse documents | Entity type arrays are optional in the schema. If no dates found, dates field can be omitted. More flexible for documents that lack certain entity types. Validation must handle missing fields. | |
| You decide | Claude chooses based on llama-cpp-python JSON schema capabilities and validation simplicity. | |

**User's choice:** Required fields with empty arrays
**Notes:** Ensures predictable, consistent response structure for easier validation and client code.

---

## Validation Strategy

### Question 1: Handling Invalid Entities

| Option | Description | Selected |
|--------|-------------|----------|
| Fail entire extraction on first invalid entity | Strict validation: one bad entity fails the whole response with HTTP 400. Forces model to produce only valid outputs. Risk: lose all valid entities due to one mistake. Better for critical healthcare applications. | |
| Allow partial results, flag invalid entities | Return valid entities, include an 'errors' array with validation failures for invalid ones. User gets usable data plus awareness of what failed. More forgiving for portfolio demo purposes. | ✓ |
| Filter out invalid entities silently | Remove invalid entities, return only valid ones without error notification. Cleanest output, but user doesn't know what was filtered. Could hide model hallucinations. | |

**User's choice:** Allow partial results, flag invalid entities (Recommended)
**Notes:** Portfolio demo prioritizes usability and transparency over strict validation.

### Question 2: Confidence Threshold Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Include all entities regardless of confidence | Every extracted entity is returned with its confidence score. User decides what threshold to apply. Maximizes information available for portfolio demo. Requires user to filter. | |
| Filter entities below configurable threshold | Environment variable sets minimum confidence (e.g., CONFIDENCE_THRESHOLD=0.5). Entities below threshold are excluded or moved to a 'low_confidence' array. Balances quality and transparency. | ✓ |
| Hard-coded threshold of 0.7 | Fixed threshold removes low-confidence entities. Simpler implementation, but less flexible for demo/testing different scenarios. | |

**User's choice:** Filter entities below configurable threshold (Recommended)
**Notes:** Flexibility for portfolio reviewers to experiment with different threshold values.

### Question 3: Domain Validators

| Option | Description | Selected |
|--------|-------------|----------|
| Strict medical validators | Dates must be past (no future), diagnosis codes match ICD-10-GM format, medication names against common German medication list, LOS must be positive integer. Thorough but might reject valid edge cases. | |
| Minimal format validators | Dates must be valid ISO format and past, confidence 0.0-1.0, source spans must exist in input text. Catch obvious hallucinations without over-constraining. Matches portfolio demo scope. | ✓ |
| You decide based on VAL-02 requirement | Claude implements domain validators that 'reject impossible values' per REQUIREMENTS.md VAL-02, choosing appropriate strictness level. | |

**User's choice:** Minimal format validators (Recommended)
**Notes:** Appropriate for portfolio scope — catches hallucinations without over-constraining valid medical variations.

### Question 4: API Error Response Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Detailed validation errors | Return JSON with 'valid_entities' (passed validation), 'invalid_entities' (with reasons), 'errors' array (specific Pydantic validation messages). Developer-friendly for debugging, good for portfolio showcase. | ✓ |
| Simple error message | HTTP 400 with 'Validation failed: {count} invalid entities'. Clean but less informative. Hides what went wrong. | |
| Standard FastAPI validation response | Let FastAPI's default Pydantic validation error format handle it. Automatic but generic (not optimized for clinical entity context). | |

**User's choice:** Detailed validation errors (Recommended)
**Notes:** Showcases developer-friendly API design for portfolio reviewers.

---

## Extractor Plugin Architecture

### Question 1: Plugin Pattern Implementation

| Option | Description | Selected |
|--------|-------------|----------|
| Base class with registry pattern | Abstract BaseExtractor class with extract() method. Extractors auto-register via decorator or metaclass. Pipeline discovers and runs all registered extractors. Clean separation, easy to add by creating new extractor file. | ✓ |
| Configuration-driven plugins | YAML/JSON config defines available extractors and their settings. Pipeline loads extractors based on config. More flexible but adds config complexity. May be overkill for 4 entity types. | |
| Simple module import pattern | Each extractor is a module in src/extractors/. Pipeline imports all and calls their extract() function. Simpler, no fancy patterns, but requires manual imports in pipeline code. | |

**User's choice:** Base class with registry pattern (Recommended)
**Notes:** Demonstrates architectural thinking and extensibility per EXT-01 requirement.

### Question 2: Schema Organization

| Option | Description | Selected |
|--------|-------------|----------|
| Each extractor owns its schema | Extractor class includes both extraction logic and Pydantic model. Cohesive: schema lives with the code that produces it. Easy to add new entity type (one file has everything). Matches plugin architecture well. | ✓ |
| Centralized schemas module | All Pydantic models in src/schemas/ directory. Extractors import schemas. Easier to see all schemas in one place. Requires two-file edit to add new entity type (schema + extractor). | |
| Hybrid: base schema, extractor-specific extensions | Base entity schema (source_span, confidence) in schemas module. Each extractor extends with domain-specific fields. More complex but enforces consistency. | |

**User's choice:** Each extractor owns its schema (Recommended)
**Notes:** Cohesive design — adding a new entity type is truly a single-file operation.

### Question 3: Model Instance Injection

| Option | Description | Selected |
|--------|-------------|----------|
| Dependency injection via constructor | Pipeline passes model instance to each extractor's __init__(). Testable (easy to mock model), explicit dependencies, follows SOLID principles. Standard Python pattern. | ✓ |
| Shared app state (FastAPI request.app.state) | Extractors access model via request.app.state.model. Simpler (no DI needed), but tighter coupling to FastAPI. Harder to test extractors independently. | |
| Global model singleton | Model loaded as module-level global in src/models/. All extractors import it. Simplest but harder to test, violates dependency inversion. | |

**User's choice:** Dependency injection via constructor (Recommended)
**Notes:** Showcases SOLID principles and testable architecture design.

### Question 4: Extractor Execution Model

| Option | Description | Selected |
|--------|-------------|----------|
| Sequential execution | Run temporal extractor, then clinical extractor in order. Simpler implementation, predictable. Given we have 2 extractors (hybrid approach), sequential is fast enough for portfolio demo. | |
| Parallel async execution | Use asyncio.gather() to run both extractors concurrently. Faster for multiple extractors, showcases async Python skills. More impressive for portfolio even with just 2 extractors. | ✓ |
| You decide based on performance needs | Claude chooses based on whether parallelization provides meaningful speedup given the hybrid prompt approach. | |

**User's choice:** Parallel async execution (Recommended)
**Notes:** Showcases async Python proficiency for portfolio even with just 2 extractors.

---

## Source Span Grounding

### Question 1: Span Representation Format

| Option | Description | Selected |
|--------|-------------|----------|
| Character offsets (start, end) | Store zero-based character positions: {"start": 45, "end": 67, "text": "Diagnose: Diabetes mellitus"}. Standard approach, easy to validate against input, works well with Python string slicing. Industry standard for NLP. | ✓ |
| Token positions | Store token indices instead of character positions. More aligned with how LLMs process text, but requires tokenization step. Adds complexity for validation. | |
| Line and column positions | Store {"line": 3, "column": 12} style positions. Human-readable but harder to validate, less standard for NLP pipelines. | |

**User's choice:** Character offsets (start, end) (Recommended)
**Notes:** Industry-standard NLP approach, straightforward validation with Python string slicing.

### Question 2: Span Validation Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Exact string match validation | Verify input_text[start:end] == entity.source_text exactly. Strict validation catches hallucinations. If span doesn't match, mark entity as invalid. Clear and unambiguous. | ✓ |
| Fuzzy matching with similarity threshold | Allow minor differences (whitespace, punctuation) using string similarity. More forgiving of LLM output variations. Risk: might accept hallucinations with partial overlap. | |
| Presence check only | Just verify entity.source_text appears somewhere in input (substring search). Lenient but doesn't validate position accuracy. Could miss duplicate text issues. | |

**User's choice:** Exact string match validation (Recommended)
**Notes:** Strict anti-hallucination measure appropriate for clinical domain.

### Question 3: Handling Ungrounded Entities

| Option | Description | Selected |
|--------|-------------|----------|
| Reject as invalid entity | Treat missing/invalid source span as validation failure. Entity goes to 'invalid_entities' array with error reason. Strict anti-hallucination measure. Aligns with 'reject impossible values' per VAL-02. | |
| Flag with warning but include | Include entity with a 'source_span_validated: false' flag. User sees extraction but knows it's ungrounded. More informative but could mislead if user ignores the flag. | ✓ |
| Auto-search for best match | Attempt to find the entity text in input using fuzzy search, assign those offsets. Helpful but could assign wrong spans for repeated text. | |

**User's choice:** Flag with warning but include
**Notes:** Transparency approach — user sees all extractions with explicit grounding validation status.

### Question 4: Span Extraction Method

| Option | Description | Selected |
|--------|-------------|----------|
| Prompt LLM to provide spans | Include source_span (start, end, text) in JSON schema. LLM extracts positions directly. More accurate since model knows where it found the entity. Leverages llama-cpp-python structured output. | ✓ |
| Post-process: search for entity text | LLM returns only entity values. Python code searches input for entity text and assigns offsets. Simpler prompt but risks wrong matches (duplicates, similar text). Less accurate. | |
| Hybrid: LLM provides text, we validate positions | LLM returns source_text field (not positions). Python finds that text in input and computes offsets. Validates LLM didn't hallucinate while computing precise positions. | |

**User's choice:** Prompt LLM to provide spans (Recommended)
**Notes:** Leverages llama-cpp-python's structured output capabilities for most accurate span extraction.

---

## Claude's Discretion

- Specific German medical abbreviations list to include (beyond common ones: Pat., OPS, ICD, Diag., Med., Aufnahme, Entlassung, Verweildauer)
- Exact confidence threshold default value (within 0.4-0.6 range, suggested 0.5)
- BaseExtractor abstract method signatures and registry implementation details
- Error message wording and validation feedback specificity
- How to structure the 'low_confidence' array in responses

## Deferred Ideas

None — all discussion remained within Phase 2 scope
