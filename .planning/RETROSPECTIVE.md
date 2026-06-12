# Retrospective: German Clinical NLP Pipeline

---

## Milestone: v1.0 MVP

**Shipped:** 2026-06-12
**Phases:** 3 | **Plans:** 7 | **Duration:** 1 day

### What Was Built

- FastAPI application with environment-based GGUF model loading, health monitoring endpoints, and 15 synthetic German clinical text samples
- Working end-to-end extraction of dates and length-of-stay indicators with validated JSON output and source span grounding
- Clinical entity extraction (diagnoses + medications) with parallel async execution via asyncio.gather, using plugin pattern for extensibility
- Domain validators that reject future dates and confidence filtering via configurable CONFIDENCE_THRESHOLD environment variable
- Single-stage python:3.11-slim container with non-root user, 8GB memory limit, stdlib urllib healthcheck, one-command docker-compose demo
- Full portfolio README with curl+httpx examples and docs/ARCHITECTURE.md with request flow diagram and extensibility walkthrough
- Hand-crafted representative EntityResponse JSON files covering date/LOS, ICD-coded diagnoses, and medication+LOS extractions

### What Worked

- **Coarse phase granularity** — 3 phases instead of the research-suggested 5 reduced context overhead and allowed each phase to deliver a cohesive vertical slice
- **TDD red→green cycle** — tests written first caught character offset issues with German umlauts early; all 24 tests pass
- **Plugin pattern established early** — adding ClinicalExtractor in Phase 2 Plan 02 required zero changes to core endpoint code; proves EXT-01 satisfactorily
- **Fail-fast env validation** — EnvironmentError at import time surfaced config problems before any request hit the API; saved debugging time
- **asyncio.to_thread wrapper** — minimal change to enable parallel execution of synchronous llama-cpp-python calls; elegant solution for the sync/async boundary

### What Was Inefficient

- **Traceability table not updated during Phase 3** — DEPLOY-01/04 and DOC-03 showed "Pending" at milestone close despite being delivered; required manual correction during archival
- **Synthetic sample generation** — GGPONC HuggingFace API was flagged as a risk in RESEARCH.md but the decision to fall back to synthetic samples only happened during Phase 1 execution; could have been pre-decided
- **Example JSON fallback** — skip-generation path in Phase 3 Plan 03 required a checkpoint; hand-crafting character offsets manually is tedious; real model integration would eliminate this

### Patterns Established

- **@register_extractor decorator pattern** for plugin-based entity type extensibility
- **Source span validation** via `input_text[start:end] == entity.text` for hallucination detection
- **Confidence filtering at endpoint level** (not in extractors) to honor configurable CONFIDENCE_THRESHOLD
- **asyncio.to_thread + asyncio.gather** for parallelizing synchronous LLM calls in FastAPI
- **stdlib urllib healthcheck** instead of curl for minimal slim-image health probing
- **_generated_by disclosure field** in example JSON files for transparency when fallback path is used

### Key Lessons

1. **Mark requirements complete in the traceability table at plan execution time**, not at milestone close — stale "Pending" rows create unnecessary doubt
2. **Pre-decide dataset fallback strategies** during research phase; GGPONC HuggingFace breakage was known risk but not pre-resolved
3. **Keep phase SUMMARY.md one-liners tight** — they're used verbatim in MILESTONES.md and retrospective; vague summaries require rewriting at milestone close
4. **asyncio.to_thread is the right primitive** for wrapping synchronous model inference in FastAPI — document this in ARCHITECTURE.md for future phases

### Cost Observations

- Model mix: Sonnet 4.5/4.6 throughout (no Opus)
- Sessions: approximately 8 (one per plan + setup)
- Notable: Entire portfolio project completed in a single day; coarse phase granularity kept sessions short and focused

---

## Cross-Milestone Trends

*Will populate as additional milestones complete.*

| Milestone | Phases | Plans | Duration | Rework | Test Coverage |
|-----------|--------|-------|----------|--------|---------------|
| v1.0 MVP | 3 | 7 | 1 day | Low | 24 tests |
