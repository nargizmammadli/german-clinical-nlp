# Roadmap: German Clinical NLP Pipeline

**Project:** German Clinical NLP Information Extraction Pipeline  
**Core Value:** Demonstrates production-ready clinical NLP with local LLM deployment, structured output validation, and explicit hallucination handling — all with German medical text.  
**Granularity:** coarse  
**Mode:** mvp  
**Created:** 2026-06-11

## Phases

- [x] **Phase 1: Foundation & Core Infrastructure** - Establish model deployment, API scaffold, and sample data (completed 2026-06-12)
- [ ] **Phase 2: Entity Extraction Pipeline** - Build complete extraction with all entity types and validation
- [ ] **Phase 3: Deployment & Documentation** - Package as portfolio-ready Docker demo

## Phase Details

### Phase 1: Foundation & Core Infrastructure

**Goal:** Working local LLM deployment with health monitoring and German clinical sample data
**Mode:** mvp
**Depends on:** Nothing (first phase)
**Requirements:** MODEL-01, MODEL-02, MODEL-03, MODEL-04, API-02, API-03, API-05, DATA-01, DATA-02, DATA-03
**Success Criteria** (what must be TRUE):

  1. System loads GGUF model via llama-cpp-python with environment-based configuration
  2. GET /health endpoint returns service status including model readiness
  3. GET /models endpoint returns active model metadata (name, quantization, context length)
  4. Sample German clinical text from GGPONC dataset is accessible and parseable
  5. API generates OpenAPI documentation accessible via /docs

**Plans:** 1/1 plans complete

---

### Phase 2: Entity Extraction Pipeline

**Goal:** Complete extraction pipeline that extracts all entity types from German clinical text with validated JSON output
**Mode:** mvp
**Depends on:** Phase 1
**Requirements:** ENTITY-01, ENTITY-02, ENTITY-03, ENTITY-04, ENTITY-05, ENTITY-06, VAL-01, VAL-02, VAL-03, API-01, API-04, EXT-01, EXT-02
**Success Criteria** (what must be TRUE):

  1. User can POST German clinical text to /extract and receive JSON with dates, diagnoses, medications, and length-of-stay indicators
  2. Each extracted entity includes confidence score and source text span (evidence grounding)
  3. Pydantic validation rejects impossible values (future dates, invalid formats, hallucinated entities without source spans)
  4. API returns meaningful error messages for invalid requests (empty text, unsupported formats, validation failures)
  5. Developer can add a new entity type by creating a single extractor plugin without modifying core pipeline code

**Plans:** 3 plans

Plans:
- [x] 02-01-PLAN.md — Temporal entity extraction with plugin pattern foundation (completed 2026-06-12)
- [x] 02-02-PLAN.md — Clinical entity extraction with parallel execution (completed 2026-06-12)
- [ ] 02-03-PLAN.md — Validation logic and confidence filtering
---

### Phase 3: Deployment & Documentation

**Goal:** Portfolio-ready containerized demo with comprehensive setup and usage documentation
**Mode:** mvp
**Depends on:** Phase 2
**Requirements:** DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-04, DOC-01, DOC-02, DOC-03, DOC-04
**Success Criteria** (what must be TRUE):

  1. User can run `docker-compose up` and have working extraction API within 5 minutes
  2. Docker container respects explicit memory limits and includes health checks
  3. README includes setup instructions, API usage examples (curl and Python), and example extraction output
  4. Architecture documentation explains component design, extensibility pattern, and how to add new entity types
  5. Portfolio reviewer can test all extraction endpoints and verify output quality against documented examples

**Plans:** TBD

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Core Infrastructure | 1/1 | Complete    | 2026-06-12 |
| 2. Entity Extraction Pipeline | 2/3 | Executing | - |
| 3. Deployment & Documentation | 0/0 | Not started | - |

---
*Last updated: 2026-06-12*
