# Phase 3: Deployment & Documentation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-12
**Phase:** 03-deployment-documentation
**Areas discussed:** Model delivery strategy, README structure, Architecture docs placement, Example extraction output

---

## Model Delivery Strategy

### Q1: Default model choice

| Option | Description | Selected |
|--------|-------------|----------|
| Mistral 7B Instruct Q4_K_M (4.5 GB) | Recruiter downloads 4.5GB file, mounts via volume — done. Llama 3.3 available as override. | ✓ |
| Llama 3.3 70B Q4_K_M (40 GB) | Better quality but 40GB download/RAM requirement — dealbreaker for most reviewers. | |
| Model-agnostic (no default) | User provides any GGUF via MODEL_PATH. Less opinionated, more friction. | |

**User's choice:** Mistral 7B Instruct Q4_K_M (4.5 GB)

### Q2: Model delivery mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Volume mount from host models/ directory | docker-compose mounts `./models:/app/models`. README: download GGUF to models/, then docker-compose up. | ✓ |
| Env var path (absolute host path) | MODEL_PATH points anywhere on host. More flexible, messier docker-compose docs. | |
| Download script in docker-compose | Automated pull from HuggingFace. Adds complexity, rate limits, network dependency. | |

**User's choice:** Volume mount from host models/ directory

### Q3: Memory limit

| Option | Description | Selected |
|--------|-------------|----------|
| 8 GB | Comfortable headroom for Mistral 7B (~4.5GB model + ~2GB working memory). | ✓ |
| 6 GB | Tighter, could cause OOM on heavy extraction. | |
| 16 GB | Unnecessarily generous for Mistral 7B demo. | |

**User's choice:** 8 GB (`mem_limit: 8g` in docker-compose)

### Q4: Health check timing

| Option | Description | Selected |
|--------|-------------|----------|
| Poll every 30s, 3 retries, 60s start period | 60s accounts for Mistral 7B load time (~20-30s). Standard pattern. | ✓ |
| Poll every 10s, 5 retries, 120s start period | More aggressive, longer grace period. | |
| You decide | Claude picks timing values. | |

**User's choice:** Poll every 30s, 3 retries, 60s start period

---

## README Structure

### Q1: What comes first?

| Option | Description | Selected |
|--------|-------------|----------|
| Quick-start section | Prerequisites → clone → download model → docker-compose up → curl demo. Run it in 5 minutes. | ✓ |
| Project introduction | Lead with what the pipeline does and why it's interesting, then setup. | |
| Architecture overview | Engineering depth first, then setup. Unusual but demonstrates technical confidence. | |

**User's choice:** Quick-start section first

### Q2: API usage examples

| Option | Description | Selected |
|--------|-------------|----------|
| curl + Python httpx, both with full JSON output | Complete extraction request + formatted JSON response showing entities, confidence scores, source spans. | ✓ |
| curl only (minimal) | Simpler, less maintenance. | |
| curl + Python + OpenAPI /docs link | Three-touch coverage including interactive Swagger UI. | |

**User's choice:** curl + Python httpx, both with full JSON output

### Q3: README tone

| Option | Description | Selected |
|--------|-------------|----------|
| Technical and concise — let the code speak | Crisp headers, minimal prose, code blocks front-and-center. | |
| Explanatory — teach the reader | Explain what each component does, why decisions were made. Shows domain knowledge. | ✓ |
| You decide | Claude picks tone based on portfolio context. | |

**User's choice:** Explanatory — teach the reader

---

## Architecture Docs Placement

### Q1: Where does DOC-04 live?

| Option | Description | Selected |
|--------|-------------|----------|
| Separate docs/architecture.md, linked from README | Clean README + deep content discoverable. Easy to link directly. | ✓ |
| Embedded directly in README | One-doc approach, can't miss it. But README gets long. | |
| Both — brief overview in README + full docs/architecture.md | Best of both worlds, slightly more maintenance surface. | |

**User's choice:** Separate docs/architecture.md, linked from README

### Q2: What does docs/architecture.md cover?

| Option | Description | Selected |
|--------|-------------|----------|
| Components + plugin pattern + add-entity walkthrough | Three sections: component diagram, plugin architecture, step-by-step "how to add entity type". Covers EXT-01, EXT-02, DOC-04. | ✓ |
| Narrative request walkthrough | Follow a POST /extract request end-to-end. More readable, less reference-friendly. | |
| You decide | Claude determines most valuable architecture content. | |

**User's choice:** Components + plugin pattern + add-entity walkthrough

---

## Example Extraction Output

### Q1: How to provide examples?

| Option | Description | Selected |
|--------|-------------|----------|
| Static JSON files committed to data/examples/ | Works without model, immediately visible on GitHub. One shown inline in README. | ✓ |
| Live output (README shows real terminal output) | More impressive visually but fragile as documentation — becomes stale when format changes. | |
| Both — static JSON + scripts/demo.py that regenerates them | Best documentation value, more development effort. | |

**User's choice:** Static JSON files committed to data/examples/

### Q2: What inputs to cover?

| Option | Description | Selected |
|--------|-------------|----------|
| 3 samples: one per entity category focus | Sample 1: date-heavy, Sample 2: diagnosis-focused, Sample 3: medications + LOS mixed. | ✓ |
| 1 comprehensive sample showing all 4 entity types | Simpler but may look cherry-picked. | |
| 5+ samples for thorough coverage | More impressive but more maintenance; variable quality from Mistral 7B. | |

**User's choice:** 3 samples covering different entity strengths

### Q3: How to generate examples?

| Option | Description | Selected |
|--------|-------------|----------|
| Manually authored (hand-written ideal JSON) | Represents best-case output. No model required. | |
| Model-generated from actual Mistral 7B Q4_K_M inference | Authentic output with real confidence scores and source spans. | ✓ |
| You decide | Claude picks based on what serves portfolio reviewers. | |

**User's choice:** Model-generated from actual inference run during development

---

## Claude's Discretion

- Dockerfile base image choice (python:3.11-slim recommended per CLAUDE.md)
- Multi-stage vs single-stage Dockerfile build
- docker-compose service naming and port mapping
- README section ordering within quick-start
- Exact German clinical text used in API usage examples
- Which GGPONC-derived sentences to use for the 3 example samples

## Deferred Ideas

None — discussion stayed within phase scope
