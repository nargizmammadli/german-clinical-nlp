# German Clinical NLP Pipeline

## What This Is

A portfolio-focused information extraction pipeline for German clinical text. Takes German clinical notes as input and extracts structured medical entities (dates, diagnoses, length-of-stay indicators, medications) as validated JSON. Built to showcase healthcare NLP, LLM engineering, and production API skills to recruiters and potential employers. Deployed via Docker with a one-command demo and full portfolio documentation.

## Core Value

Demonstrates production-ready clinical NLP with local LLM deployment, structured output validation, and explicit hallucination handling — all with German medical text.

## Requirements

### Validated

- ✓ Pipeline extracts dates from German clinical text with confidence scores — v1.0
- ✓ Pipeline extracts diagnoses from German clinical text with confidence scores — v1.0
- ✓ Pipeline extracts medications from German clinical text with confidence scores — v1.0
- ✓ Pipeline extracts length-of-stay indicators with confidence scores — v1.0
- ✓ Each extracted entity includes source text span (evidence grounding) — v1.0
- ✓ Extraction output is validated JSON with Pydantic schemas — v1.0
- ✓ System uses llama-cpp-python to load GGUF models — v1.0
- ✓ Model selection is configurable via environment variables — v1.0
- ✓ System works with local GGUF models (no cloud API dependencies) — v1.0
- ✓ System handles context window appropriately (n_ctx=8192) — v1.0
- ✓ POST /extract endpoint accepts German clinical text and returns extracted entities — v1.0
- ✓ GET /health endpoint returns service health status — v1.0
- ✓ GET /models endpoint returns active model metadata — v1.0
- ✓ API provides meaningful error responses for invalid requests — v1.0
- ✓ API automatically generates OpenAPI documentation — v1.0
- ✓ Pydantic schema validation enforces entity structure — v1.0
- ✓ Domain validators reject impossible values (future dates) — v1.0
- ✓ Confidence scores included and configurable via CONFIDENCE_THRESHOLD — v1.0
- ✓ 15 synthetic German clinical text samples covering all entity types — v1.0
- ✓ Dockerfile enables local development deployment — v1.0
- ✓ docker-compose.yml provides one-command working demo — v1.0
- ✓ Docker configuration includes explicit memory limits (8g) — v1.0
- ✓ Container includes health checks (stdlib urllib, 60s start_period) — v1.0
- ✓ README with setup instructions and curl/Python usage examples — v1.0
- ✓ Pre-committed example extraction JSON files in data/examples/ — v1.0
- ✓ Architecture documentation with plugin pattern and request flow diagram — v1.0
- ✓ Plugin pattern for extensible entity type addition — v1.0

### Active

- [ ] Assertion status detection (confirmed vs negated vs hypothetical) — v2.0
- [ ] German medical abbreviation expansion — v2.0
- [ ] Confidence score calibration on a validation set — v2.0
- [ ] Comprehensive automated test suite — v2.0
- [ ] Structured JSON logging with loguru — v2.0

### Out of Scope

- Web UI — API-only; recruiters test via curl/Postman; keeps scope on backend skills
- Production cloud deployment — local Docker sufficient for portfolio demonstration
- Database persistence — JSON responses sufficient
- Multiple language support — German-only focus demonstrates domain depth
- Real patient data — GDPR risk; synthetic/public datasets only
- Real-time streaming — batch processing sufficient for demo
- Entity relationship extraction — high complexity, deferred to v2+
- Custom model fine-tuning — focus is engineering patterns, not ML research

## Context

**Shipped:** v1.0 MVP (2026-06-12) — 3 phases, 7 plans, ~14,000 LOC, 1 day

**Tech stack:** Python 3.11, llama-cpp-python 0.3.28, FastAPI 0.136.3, Pydantic v2.13.4, Docker/docker-compose

**Source files:** `src/config.py`, `src/main.py`, `src/models/loader.py`, `src/api/health.py`, `src/api/models.py`, `src/api/extract.py`, `src/schemas/entities.py`, `src/extraction/base.py`, `src/extraction/temporal.py`, `src/extraction/clinical.py`, `src/prompts/temporal_prompt.py`, `src/prompts/clinical_prompt.py`, `src/validation/validators.py`

**Tests:** 24 passing (6 API integration + 4 temporal extraction + 7 clinical/parallel extraction + 9 validation domain)

**Known limitations:**
- llama-cpp-python requires C++ toolchain; tests use mocked model on Windows
- Example JSON files are hand-crafted (model not available at generation time); _generated_by disclosure in each file
- GGPONC HuggingFace corpus unavailable (datasets 3.0+ breaking change); synthetic samples used

## Constraints

- **Language**: German clinical text only
- **Model**: Local GGUF models via llama-cpp-python (no cloud API dependencies)
- **Deployment**: Docker-based local development (no cloud infra required)
- **Data privacy**: No real patient data — synthetic/public datasets only
- **Scope**: Portfolio showcase — production hardening deferred

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| llama-cpp-python over cloud APIs | Demonstrates local model deployment skills, no API costs, works offline | ✓ Good — central to portfolio narrative |
| Environment variables for config | Simple, Docker-friendly, standard practice | ✓ Good — fail-fast at startup |
| Pydantic v2 for validation | Type safety, automatic validation, clear schema definition | ✓ Good — source span + confidence validated cleanly |
| FastAPI over Flask | Modern async support, automatic OpenAPI docs, type hints | ✓ Good — asyncio.gather parallel extraction natural fit |
| Plugin registry pattern (@register_extractor) | Extensible without core code changes | ✓ Good — EXT-01/EXT-02 satisfied cleanly |
| asyncio.to_thread for parallel extraction | llama-cpp-python sync, but gather enables parallelism | ✓ Good — correct async pattern for blocking I/O |
| Confidence filtering at endpoint level | Respect configurable env var; extractors stay pure | ✓ Good — D-20 consolidation fixed hardcoded 0.5 |
| Zero-based [start, end) offsets for spans | Python slicing convention | ✓ Good — simplifies hallucination detection |
| Synthetic German clinical samples | GGPONC HuggingFace API broken in datasets 3.0+ | ✓ Adjusted — maintains portfolio value without PHI risk |
| stdlib urllib healthcheck | No curl in python:3.11-slim | ✓ Good — zero overhead, zero dependencies |
| Non-root container user | ASVS V1.6 security practice | ✓ Good — production hardening signal for reviewers |

---
*Last updated: 2026-06-12 after v1.0 milestone*
