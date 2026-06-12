# Phase 3: Deployment & Documentation - Context

**Gathered:** 2026-06-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Package the working German clinical NLP extraction pipeline as a portfolio-ready containerized demo. Deliverables: Dockerfile, docker-compose.yml with memory limits and health checks, a comprehensive README (quick-start through explanatory content), separate architecture documentation, and pre-generated example extraction output files. A recruiter can clone the repo, place one 4.5GB model file, run `docker-compose up`, and have a working extraction API within 5 minutes.

</domain>

<decisions>
## Implementation Decisions

### Model Delivery
- **D-01:** Default model is **Mistral 7B Instruct Q4_K_M** (~4.5GB) — practical for portfolio reviewers without requiring 40GB download. Llama 3.3 70B remains available as an optional override via the existing `MODEL_PATH` environment variable.
- **D-02:** Model delivered via **volume mount from host `models/` directory** — docker-compose.yml mounts `./models:/app/models`. README instructs: download GGUF to `models/mistral-7b-instruct.gguf`, then `docker-compose up`.
- **D-03:** Docker container enforces **8GB memory limit** (`mem_limit: 8g`) — comfortable headroom for Mistral 7B (~4.5GB model + ~2GB working memory), realistic for developer hardware.
- **D-04:** Container health check: **poll GET /health every 30s, 3 retries, 60s start period** — the 60s start period accounts for Mistral 7B model load time (~20-30s). Standard Docker HEALTHCHECK CMD pattern visible in `docker ps` output.

### README Structure
- **D-05:** **Quick-start section first** — README opens with: prerequisites → clone → download model → `docker-compose up` → curl demo. Recruiter can run the demo without reading anything else.
- **D-06:** API usage examples include **curl + Python httpx, both showing full JSON output** — complete extraction request with a real German clinical sentence and the formatted JSON response (entities, confidence scores, source spans).
- **D-07:** **Explanatory tone** — README explains what each component does and why key decisions were made (local LLM vs cloud API, German-specific challenges, plugin architecture). Teaches the reader, not just documents commands.

### Architecture Documentation
- **D-08:** Architecture docs live in **separate `docs/architecture.md`**, linked from README — keeps README focused while making deeper content discoverable. Easier to link directly to the architecture doc from a portfolio or cover letter.
- **D-09:** `docs/architecture.md` covers three sections:
  1. Component diagram showing `main.py` → pipeline → extractors → validators data flow
  2. Plugin architecture: how `BaseExtractor`, the registry, and `asyncio.gather` work together
  3. Step-by-step "how to add a new entity type" walkthrough with code snippets
  This satisfies EXT-01, EXT-02, and DOC-04.

### Example Extraction Output
- **D-10:** Static JSON files committed to `data/examples/` — one file shown inline (truncated) in README, full files available for inspection. Works without a running model so reviewers see extraction quality immediately on landing.
- **D-11:** **3 example samples** covering different entity strengths:
  - Sample 1: Date-heavy clinical note (admission/discharge dates)
  - Sample 2: Diagnosis-focused (ICD codes, condition names)
  - Sample 3: Mixed — medications + LOS indicators
- **D-12:** Examples are **model-generated from actual Mistral 7B Q4_K_M inference** during development — authentic output showing real confidence scores and source spans, not hand-authored idealizations.

### Claude's Discretion
- Specific Dockerfile base image choice (python:3.11-slim recommended per CLAUDE.md)
- Multi-stage vs single-stage Dockerfile build
- docker-compose service naming and port mapping
- README section ordering within the quick-start (beyond the entry point decision above)
- Exact content of the German clinical text used in API usage examples
- Which GGPONC-derived sentence to use for each of the 3 example samples

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Requirements
- `.planning/REQUIREMENTS.md` — Phase 3 requirements: DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-04, DOC-01, DOC-02, DOC-03, DOC-04
- `.planning/PROJECT.md` — Core value proposition, target audience (healthcare AI developers, technical recruiters), constraints
- `.planning/ROADMAP.md` — Phase 3 goal and success criteria

### Prior Phase Context
- `.planning/phases/01-foundation-core-infrastructure/01-CONTEXT.md` — Configuration decisions: env-vars only (D-07), relative paths (D-08), fail-fast (D-09), model at startup (D-01)
- `.planning/phases/02-entity-extraction-pipeline/02-CONTEXT.md` — API response structure, validation behavior, confidence threshold env var, source span format

### Technical Stack
- `CLAUDE.md` — Technology stack: llama-cpp-python, FastAPI, Pydantic v2, Docker base image recommendation, llama-cpp-python GPU note (not needed for portfolio demo)

No external specs — requirements fully captured in references above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`src/main.py`** — FastAPI app with lifespan manager; Dockerfile CMD should target this module (e.g., `uvicorn src.main:app`)
- **`src/config.py`** — Environment variable validation at startup; `MODEL_PATH` is already the env var for model location (maps cleanly to the `./models` volume mount path)
- **`src/api/health.py`** — GET /health endpoint already implemented and returns model readiness; use as Docker HEALTHCHECK target
- **`data/`** — Already exists as a directory; `data/examples/` is a natural home for pre-generated extraction samples

### Established Patterns
- **Environment-variable configuration** (from Phase 1 D-07 to D-09) — All container config via env vars in docker-compose; no config files needed
- **Fail-fast on missing config** — Container will refuse to start if `MODEL_PATH` not set or model file not found; README must cover this clearly to avoid confusing "startup failures"
- **Relative model paths** (Phase 1 D-08) — `MODEL_PATH=models/mistral-7b-instruct.gguf` inside the container maps to the volume-mounted file

### Integration Points
- **`models/` directory** — Already exists as a placeholder (gitignored GGUF files); docker-compose volume mount `./models:/app/models` connects to this
- **Port 8000** — FastAPI default; docker-compose should expose `8000:8000`
- **`GET /health`** — Health endpoint that checks model readiness; already returns 503 when model not loaded (D-06 from Phase 1)

</code_context>

<specifics>
## Specific Ideas

**Docker-Compose Setup Story:**
```
git clone ... && cd german-clinical-nlp
# Download model (4.5GB)
mkdir -p models && wget -O models/mistral-7b-instruct.gguf <huggingface-url>
# Set environment
cp .env.example .env
# Launch
docker-compose up
# Test
curl -X POST http://localhost:8000/extract -H "Content-Type: application/json" \
  -d '{"text": "Patient wurde am 15.03.2024 mit Diabetes mellitus Typ 2 aufgenommen."}'
```

**Example Output Samples Plan:**
- `data/examples/temporal_extraction.json` — input with date-rich oncology timeline, output with extracted admission/discharge dates
- `data/examples/diagnosis_extraction.json` — input with ICD-coded diagnoses, output with condition entities + confidence scores
- `data/examples/medication_los_extraction.json` — input with medication prescriptions + Verweildauer mention, output showing mixed entity types

**Architecture Doc Extensibility Section:**
The "how to add a new entity type" walkthrough should show the minimal 3-step process: (1) create `src/extraction/my_entity_extractor.py` implementing `BaseExtractor`, (2) define the Pydantic schema in the same file, (3) register via decorator — no changes to core pipeline required. This is the key demonstration of EXT-01/EXT-02.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-Deployment & Documentation*
*Context gathered: 2026-06-12*
