# German Clinical NLP Pipeline

## What This Is

A portfolio-focused information extraction pipeline for German clinical text. Takes German clinical notes as input and extracts structured medical entities (dates, diagnoses, length-of-stay indicators, medications) as validated JSON. Built to showcase healthcare NLP, LLM engineering, and production API skills to recruiters and potential employers.

## Core Value

Demonstrates production-ready clinical NLP with local LLM deployment, structured output validation, and explicit hallucination handling — all with German medical text.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Pipeline extracts dates from German clinical text
- [ ] Pipeline extracts diagnoses from German clinical text
- [ ] Pipeline extracts length-of-stay indicators from German clinical text
- [ ] Pipeline extracts medication mentions from German clinical text
- [ ] Extraction output is validated JSON with Pydantic schemas
- [ ] Pipeline uses llama-cpp-python with configurable GGUF models
- [ ] Model selection via environment variables
- [ ] Confidence scores included for each extracted entity
- [ ] Pydantic validators reject impossible values (future dates, invalid formats)
- [ ] FastAPI exposes POST /extract endpoint
- [ ] FastAPI exposes GET /health endpoint
- [ ] FastAPI exposes GET /models endpoint
- [ ] Includes sample data from public German clinical NLP datasets (GGPONC or BRONCO)
- [ ] Dockerfile for local development deployment
- [ ] Pipeline architecture is extensible (easy to add new entity types)
- [ ] Clean README with setup instructions and usage examples
- [ ] Example extraction output documented (JSON samples or screenshots)
- [ ] Working demo: docker-compose up and extract entities from sample notes

### Out of Scope

- Production cloud deployment — Local dev environment sufficient for portfolio
- Web UI — API-only, recruiters can test via curl/Postman
- Database persistence — JSON responses sufficient
- Test coverage — Example output demonstrates correctness, formal tests deferred
- Multiple language support — German only
- Real clinical data — Synthetic/public datasets only for privacy compliance

## Context

**Target audience:** Healthcare AI developers and technical recruiters reviewing GitHub portfolio.

**Technical environment:** Python ecosystem, local LLM deployment, healthcare NLP domain.

**Key demonstration goals:**
- Healthcare NLP domain expertise (clinical entity recognition in German)
- LLM engineering skills (local model deployment, structured output, prompt engineering)
- Production API patterns (FastAPI, validation, error handling, containerization)
- Non-English NLP capabilities (German language processing)

**Data source:** Public German clinical NLP datasets (GGPONC, BRONCO) for sample clinical notes — avoids privacy issues while demonstrating realistic clinical text handling.

## Constraints

- **Language**: German clinical text only
- **Model**: Local GGUF models via llama-cpp-python (no cloud API dependencies)
- **Deployment**: Docker-based local development (no cloud infra required)
- **Data privacy**: No real patient data — synthetic/public datasets only
- **Scope**: Portfolio showcase — production hardening deferred

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| llama-cpp-python over cloud APIs | Demonstrates local model deployment skills, no API costs, works offline | — Pending |
| Environment variables for config | Simple, Docker-friendly, standard practice | — Pending |
| Pydantic for validation | Type safety, automatic validation, clear schema definition | — Pending |
| FastAPI over Flask | Modern async support, automatic OpenAPI docs, type hints | — Pending |
| No web UI | Keeps scope focused on API/backend skills, recruiters can test via curl | — Pending |
| Extensible entity architecture | Shows architectural thinking, easy to demonstrate adding new entity types | — Pending |

---
*Last updated: 2026-06-11 after initialization*
