# Phase 1: Foundation & Core Infrastructure - Context

**Gathered:** 2026-06-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Local LLM deployment infrastructure that loads GGUF models via llama-cpp-python, exposes health and metadata endpoints via FastAPI, and provides access to German clinical sample data from GGPONC dataset.

</domain>

<decisions>
## Implementation Decisions

### Model Loading Strategy
- **D-01:** Initialize model at startup (slower startup, faster first request) — not lazy-load on first request
- **D-02:** Single model instance — no hot-swapping support

### Sample Data Structure
- **D-03:** Package GGPONC samples as static JSON files (not runtime HuggingFace datasets loading)
- **D-04:** Include 10-20 sample German clinical texts

### API Error Handling
- **D-05:** Sanitized error responses in production (not full stack traces)
- **D-06:** Model loading failures return HTTP 503 (service unavailable), not 500

### Configuration Approach
- **D-07:** Environment variables only — no config files (YAML/TOML)
- **D-08:** Relative paths for model locations
- **D-09:** Fail fast with clear error messages if required config is missing

### Claude's Discretion
- Logging strategy (format, levels, destinations)
- Model metadata fields to expose via GET /models endpoint
- Startup sequence and initialization order
- Health check implementation details (what constitutes "healthy")

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Requirements
- `.planning/REQUIREMENTS.md` — v1 requirements with Phase 1 scope: MODEL-01, MODEL-02, MODEL-03, MODEL-04, API-02, API-03, API-05, DATA-01, DATA-02, DATA-03
- `.planning/PROJECT.md` — Core value proposition, constraints, key decisions
- `.planning/ROADMAP.md` — Phase 1 goal and success criteria

### Technical Stack Reference
- `CLAUDE.md` — Technology stack section defines llama-cpp-python + FastAPI + Pydantic v2 choices with rationale

No external specs — requirements fully captured in references above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
None — empty codebase (Phase 1 is foundation)

### Established Patterns
None — Phase 1 establishes initial patterns

### Integration Points
None — Phase 1 creates the initial integration points that Phase 2 will build upon

</code_context>

<specifics>
## Specific Ideas

**GGPONC Dataset Source:**
- Use HuggingFace datasets library to extract sample data from `bigbio/ggponc2`
- Extract during development, commit as static JSON (not runtime dependency)
- Samples should demonstrate German clinical text variety (oncology guidelines)

**Model Configuration:**
- Environment variable: `MODEL_PATH` for GGUF file location (relative path)
- Environment variable: `MODEL_NAME` or similar for metadata tracking
- Default to Llama 3.3 70B Instruct Q4_K_M quantization per CLAUDE.md

**FastAPI Startup:**
- Model loading happens in FastAPI startup event handler
- If model fails to load, application refuses to start (fail fast principle)
- Health endpoint checks model readiness state

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 1-Foundation & Core Infrastructure*
*Context gathered: 2026-06-11*
