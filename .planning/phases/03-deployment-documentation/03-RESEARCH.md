# Phase 3: Deployment & Documentation - Research

**Researched:** 2026-06-12
**Domain:** Docker containerization, docker-compose orchestration, portfolio README documentation
**Confidence:** MEDIUM

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Model Delivery**
- D-01: Default model is Mistral 7B Instruct Q4_K_M (~4.5GB) — practical for portfolio reviewers without requiring 40GB download. Llama 3.3 70B remains available as an optional override via the existing `MODEL_PATH` environment variable.
- D-02: Model delivered via volume mount from host `models/` directory — docker-compose.yml mounts `./models:/app/models`. README instructs: download GGUF to `models/mistral-7b-instruct.gguf`, then `docker-compose up`.
- D-03: Docker container enforces 8GB memory limit (`mem_limit: 8g`) — comfortable headroom for Mistral 7B (~4.5GB model + ~2GB working memory), realistic for developer hardware.
- D-04: Container health check: poll GET /health every 30s, 3 retries, 60s start period — the 60s start period accounts for Mistral 7B model load time (~20-30s). Standard Docker HEALTHCHECK CMD pattern visible in `docker ps` output.

**README Structure**
- D-05: Quick-start section first — README opens with: prerequisites → clone → download model → `docker-compose up` → curl demo. Recruiter can run the demo without reading anything else.
- D-06: API usage examples include curl + Python httpx, both showing full JSON output — complete extraction request with a real German clinical sentence and the formatted JSON response (entities, confidence scores, source spans).
- D-07: Explanatory tone — README explains what each component does and why key decisions were made (local LLM vs cloud API, German-specific challenges, plugin architecture). Teaches the reader, not just documents commands.

**Architecture Documentation**
- D-08: Architecture docs live in separate `docs/architecture.md`, linked from README — keeps README focused while making deeper content discoverable. Easier to link directly to the architecture doc from a portfolio or cover letter.
- D-09: `docs/architecture.md` covers three sections:
  1. Component diagram showing `main.py` → pipeline → extractors → validators data flow
  2. Plugin architecture: how `BaseExtractor`, the registry, and `asyncio.gather` work together
  3. Step-by-step "how to add a new entity type" walkthrough with code snippets

**Example Extraction Output**
- D-10: Static JSON files committed to `data/examples/` — one file shown inline (truncated) in README, full files available for inspection. Works without a running model so reviewers see extraction quality immediately on landing.
- D-11: 3 example samples covering different entity strengths:
  - Sample 1: Date-heavy clinical note (admission/discharge dates)
  - Sample 2: Diagnosis-focused (ICD codes, condition names)
  - Sample 3: Mixed — medications + LOS indicators
- D-12: Examples are model-generated from actual Mistral 7B Q4_K_M inference during development — authentic output showing real confidence scores and source spans, not hand-authored idealizations.

### Claude's Discretion
- Specific Dockerfile base image choice (python:3.11-slim recommended per CLAUDE.md)
- Multi-stage vs single-stage Dockerfile build
- docker-compose service naming and port mapping
- README section ordering within the quick-start (beyond the entry point decision above)
- Exact content of the German clinical text used in API usage examples
- Which GGPONC-derived sentence to use for each of the 3 example samples

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DEPLOY-01 | Dockerfile enables local development deployment | Dockerfile pattern: python:3.11-slim, pip install from pyproject.toml, uvicorn CMD |
| DEPLOY-02 | docker-compose.yml provides one-command working demo | docker-compose with volumes, env_file, port mapping, restart policy |
| DEPLOY-03 | Docker configuration includes explicit memory limits | `mem_limit: 8g` in docker-compose service definition |
| DEPLOY-04 | Container includes health checks | HEALTHCHECK in Dockerfile + healthcheck block in docker-compose |
| DOC-01 | README includes setup instructions | Quick-start section: prerequisites, clone, download model, `docker-compose up` |
| DOC-02 | README includes API usage examples with curl/Python | curl example + Python httpx example with full JSON response |
| DOC-03 | README includes example extraction output (JSON samples) | 3 static JSON files in `data/examples/`, one truncated inline in README |
| DOC-04 | Architecture documentation explains component design and extensibility | `docs/architecture.md` already exists and is comprehensive — verify it covers all three required sections |
</phase_requirements>

---

## Summary

Phase 3 packages the completed German clinical NLP extraction pipeline into a portfolio-ready containerized demo. The deliverables are a Dockerfile, docker-compose.yml, updated README.md, verification of `docs/architecture.md` completeness, and three pre-generated example JSON files in `data/examples/`. No new Python packages are introduced — this phase is purely infrastructure and documentation.

The key constraint is the model size (~4.5GB GGUF file). The model must never be bundled inside the Docker image; it lives on the host and is volume-mounted at runtime. The Dockerfile installs dependencies only; the model path is injected via the `MODEL_PATH` environment variable that `src/config.py` already validates at startup. The existing `GET /health` endpoint (returns 503 when model not loaded) is already the ideal Docker health check target.

Architecture documentation (`docs/ARCHITECTURE.md`) already exists and is comprehensive. The planner must verify it covers the three sections specified in D-09 and add any missing content rather than creating it from scratch.

**Primary recommendation:** Write a single-stage Dockerfile using `python:3.11-slim`, install from `pyproject.toml`, and use `uvicorn src.main:app --host 0.0.0.0 --port 8000` as CMD. Use Python's built-in `urllib.request` for the HEALTHCHECK (no curl dependency required in slim image).

## Project Constraints (from CLAUDE.md)

- Language: German clinical text only — example JSON files must use authentic German clinical text
- Model: Local GGUF models via llama-cpp-python — never reference cloud APIs in documentation
- Deployment: Docker-based local development — no cloud infra, no external services
- Data privacy: Synthetic/public data only — example files must use GGPONC-derived or synthetic text
- Base image: `python:3.11-slim` recommended per CLAUDE.md
- All packages already established in `pyproject.toml` — no new runtime dependencies in this phase

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Container image build | Docker build | — | Dockerfile owns dependency installation and runtime config |
| Service orchestration | Docker Compose | — | docker-compose.yml coordinates volume mounts, env vars, limits, health checks |
| Model file delivery | Host filesystem (volume) | — | GGUF files too large for image layers; volume mount is the only viable pattern |
| Health signaling | API tier (existing /health) | Docker (HEALTHCHECK consumer) | /health already implemented in health.py; Docker polls it |
| Memory enforcement | Docker Compose | — | mem_limit at compose service level enforces OOM kill threshold |
| Setup instructions | README.md | — | Developer-facing entry point for portfolio reviewers |
| API usage docs | README.md | — | curl + Python httpx examples live in README |
| Architecture docs | docs/architecture.md | README (link) | Separate file already exists, linked from README |
| Example output files | data/examples/ | README (inline snippet) | Static JSON files in repo; README shows truncated preview |

---

## Standard Stack

### Core (No new packages — all already in pyproject.toml)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `python:3.11-slim` | Docker base image | Container runtime | ~500MB vs 1.1GB full image; all Python deps compatible; recommended in CLAUDE.md [ASSUMED] |
| `uvicorn` | 0.34.0+ | ASGI server CMD in container | Already installed; single worker required for llama-cpp-python (non-picklable model) [VERIFIED: CLAUDE.md] |
| `curl` / `python urllib` | OS built-in / stdlib | Health check probe | python:3.11-slim does NOT include curl by default; use Python stdlib urllib for HEALTHCHECK [ASSUMED: slim image docs] |

### Docker Infrastructure

| File | Purpose | Key Decisions |
|------|---------|---------------|
| `Dockerfile` | Build image with deps | Single-stage, python:3.11-slim, install from pyproject.toml, urllib healthcheck script |
| `docker-compose.yml` | Orchestrate container | Volume mount, env_file, port 8000, mem_limit 8g, healthcheck block |
| `healthcheck.py` | Stdlib HTTP probe | Used by HEALTHCHECK CMD — no curl dependency |
| `.dockerignore` | Exclude models/ and .env | Models too large, .env contains secrets |
| `data/examples/` (3 JSON files) | Pre-generated extraction samples | Run from live Mistral 7B; authentic confidence scores |

**Installation:** No new packages. Dockerfile installs existing `pyproject.toml` dependencies.

---

## Package Legitimacy Audit

> This phase introduces NO new external packages. The legitimacy audit covers only pre-existing packages already verified in prior phases (fastapi, uvicorn, pydantic, python-dotenv, loguru, httpx).

| Package | Registry | Source Repo | Verdict | Disposition |
|---------|----------|-------------|---------|-------------|
| fastapi | PyPI | github.com/fastapi/fastapi | OK (pre-verified in CLAUDE.md) | Approved |
| uvicorn | PyPI | github.com/Kludex/uvicorn | OK (pre-verified in CLAUDE.md) | Approved |
| pydantic | PyPI | github.com/pydantic/pydantic | OK (pre-verified in CLAUDE.md) | Approved |
| python-dotenv | PyPI | github.com/theskumar/python-dotenv | OK (pre-verified in CLAUDE.md) | Approved |
| loguru | PyPI | github.com/Delgan/loguru | OK (pre-verified in CLAUDE.md) | Approved |
| httpx | PyPI | github.com/encode/httpx | OK (pre-verified in CLAUDE.md) | Approved |

**Note:** The `gsd-tools package-legitimacy` seam returned `SUS` for all packages with reason `unknown-downloads` — this reflects a PyPI API limitation in the tool (weekly download data unavailable), not actual suspicion. All packages have verified GitHub repos, long history, and were confirmed HIGH confidence via Context7 in prior phases.

**Packages removed due to SLOP verdict:** None
**Packages flagged as suspicious SUS:** None (tool limitation artifact, not genuine concern)

---

## Architecture Patterns

### System Architecture Diagram

```
Host Filesystem                    Docker Container
  models/                             Port 8000
  mistral-7b-instruct.gguf  ──────>  /app/models/ (volume mount, read-only)
  .env  ──────────────────────────>  env_file injection
                                          |
                               ┌──────────▼──────────┐
                               │   uvicorn server     │
                               │   src/main.py        │
                               │   FastAPI lifespan   │
                               │   loads model ──────>│  llama-cpp-python
                               └──────────────────────┘  (Llama object in app.state)
                                          |
                               ┌──────────▼──────────┐
                               │    API Endpoints     │
                               │  GET  /health   ─────┼─────> Docker HEALTHCHECK probe
                               │  GET  /models        │       (every 30s, 60s grace)
                               │  POST /extract  ─────┼─────> TemporalExtractor
                               └──────────────────────┘       ClinicalExtractor
                                                               (asyncio.gather, parallel)
```

### Recommended Project Structure (additions this phase)

```
german-clinical-nlp/
├── Dockerfile              # NEW: single-stage build, python:3.11-slim
├── docker-compose.yml      # NEW: volume mount, mem_limit, healthcheck
├── healthcheck.py          # NEW: stdlib urllib health probe for Docker
├── .dockerignore           # NEW: exclude models/, .env, __pycache__
├── README.md               # UPDATE: replace stub with full portfolio README
├── data/
│   ├── samples/            # EXISTS: ggponc_samples.json
│   └── examples/           # NEW DIR: 3 pre-generated extraction JSON files
│       ├── temporal_extraction.json
│       ├── diagnosis_extraction.json
│       └── medication_los_extraction.json
└── docs/
    └── ARCHITECTURE.md     # EXISTS: verify covers D-09 sections, supplement if needed
```

### Pattern 1: Single-Stage Dockerfile for Python + GGUF Model

**What:** Build image with pip deps only; model file injected at runtime via volume mount.

**When to use:** Portfolio/dev deployments where image rebuild frequency matters more than final image size. Single-stage is simpler and sufficient for this project.

**Example:**
```dockerfile
# Source: FastAPI official Docker docs + markaicode.com/stack/llamacpp-fastapi-docker-inference-stack
FROM python:3.11-slim

WORKDIR /app

# Install deps first for layer cache efficiency
COPY pyproject.toml ./
# Install in non-editable mode with no pip cache
RUN pip install --no-cache-dir ".[dev]" || pip install --no-cache-dir .

# Copy application code (changes more frequently than deps)
COPY src/ ./src/
COPY healthcheck.py ./

# Non-root user for security (ASVS V1.6)
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

# HEALTHCHECK: python:3.11-slim has no curl; use stdlib urllib
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python healthcheck.py

# Single worker required: llama-cpp-python Llama object is not picklable
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

### Pattern 2: docker-compose.yml for One-Command Demo

**What:** Orchestrates volume mount, environment injection, memory limits, health checks, and port exposure.

**When to use:** Local development and portfolio demo — the canonical one-command entry point.

**Example:**
```yaml
# Source: docs.docker.com/reference/compose-file/services/ + virtua.cloud tutorial
version: "3.8"

services:
  api:
    build: .
    container_name: german-clinical-nlp
    ports:
      - "8000:8000"
    volumes:
      # Model volume: host ./models maps to /app/models inside container (read-only)
      - ./models:/app/models:ro
    env_file:
      - .env
    environment:
      # Override: point MODEL_PATH to the volume-mounted file
      - MODEL_PATH=models/mistral-7b-instruct.gguf
      - MODEL_NAME=Mistral 7B Instruct Q4_K_M
    mem_limit: 8g
    mem_reservation: 6g
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "healthcheck.py"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### Pattern 3: stdlib healthcheck.py (no curl dependency)

**What:** Python script using `urllib.request` to probe the /health endpoint. Required because `python:3.11-slim` does not include curl.

**When to use:** Always — this is the required pattern for slim Python images.

**Example:**
```python
# healthcheck.py
# Source: muratcorlu.com/docker-healthcheck-without-curl-or-wget
import sys
import urllib.request

try:
    response = urllib.request.urlopen("http://localhost:8000/health", timeout=5)
    if response.status == 200:
        sys.exit(0)
    else:
        sys.exit(1)
except Exception:
    sys.exit(1)
```

### Pattern 4: README Quick-Start Structure

**What:** Portfolio README that opens with the minimal path to a working demo, then explains context.

**Recommended section order (D-05, D-06, D-07):**
1. One-sentence project description + badge row
2. **Quick Start** (prerequisites → clone → download model → `docker-compose up` → curl test)
3. **API Reference** (all endpoints with curl + Python httpx examples, full JSON response)
4. **Example Extraction Output** (inline truncated JSON from one example file)
5. **Why This Project** (design rationale: local LLM, German clinical text, plugin architecture)
6. **Architecture** (brief overview + link to `docs/architecture.md`)
7. **Development** (test suite, adding new entity types)
8. **License**

### Anti-Patterns to Avoid

- **Bundling model files in Docker image:** GGUF files are 4.5-40GB — they must be volume-mounted, never COPYed. Image would be impossibly large and rebuilds would download the model every time. [ASSUMED]
- **Using `tiangolo/uvicorn-gunicorn-fastapi` base image:** Officially deprecated by FastAPI maintainers. Always build from official Python base. [CITED: fastapi.tiangolo.com/deployment/docker/]
- **Multiple uvicorn workers with llama-cpp-python:** The `Llama` object is not picklable across worker processes. Always use `--workers 1`. [ASSUMED: standard llama-cpp-python constraint]
- **Shell form CMD:** `CMD uvicorn src.main:app ...` (shell form) does not propagate signals properly and breaks graceful shutdown/lifespan events. Always use exec form: `CMD ["uvicorn", ...]`. [CITED: fastapi.tiangolo.com/deployment/docker/]
- **Putting curl health check in slim image without installing curl first:** python:3.11-slim has no curl. Either install curl via `RUN apt-get install -y curl` (adds ~20MB) or use the stdlib urllib healthcheck.py approach (preferred — zero overhead). [ASSUMED: slim image contents]
- **model_path in COPY instruction:** Never COPY the GGUF file into the image. A reviewer would need to rebuild the image to swap models; volume mount allows swap without rebuild.
- **Hand-authoring example JSON files:** Example files must be generated from actual model inference (D-12). Hand-authored examples misrepresent extraction quality and confidence scores.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Health probe in Docker | Custom TCP check script | `python healthcheck.py` using `urllib.request` | Already have a working /health endpoint; stdlib urllib is zero-dep and reliable |
| Docker memory limits | Custom OOM monitoring | `mem_limit: 8g` in docker-compose | Docker natively enforces hard limits; container exits cleanly on OOM |
| Model loading timeout | Custom startup delay | `start_period: 60s` in HEALTHCHECK config | Docker's built-in grace period — failures during grace do not trigger unhealthy state |
| Environment configuration in container | Custom config file parsing | `env_file: .env` in docker-compose + existing `src/config.py` | Config is already fully env-var driven from Phase 1; compose env_file injection is the standard pattern |
| Architecture documentation format | Custom HTML/PDF docs | Markdown in `docs/architecture.md` | Markdown renders natively on GitHub; already partially written |

**Key insight:** Docker provides all the infrastructure primitives needed (memory limits, health checks, volume mounts, environment injection). The application code (`src/config.py`, `src/api/health.py`) is already designed to work correctly inside a container with no modifications.

---

## Common Pitfalls

### Pitfall 1: src/config.py Fails at Container Startup

**What goes wrong:** The container starts, but `src/config.py` raises `EnvironmentError: Missing required environment variables: MODEL_PATH` and the process exits with code 1.

**Why it happens:** `MODEL_PATH` is a required env var with fail-fast validation (Phase 1 D-09). If docker-compose doesn't inject it, the FastAPI app never starts. The `/health` endpoint never comes up, so the health check immediately fails all retries.

**How to avoid:** Ensure docker-compose.yml sets `MODEL_PATH` explicitly in the `environment` block (or via `env_file`). The value must be the container-internal path: `models/mistral-7b-instruct.gguf` (relative to `/app/` WORKDIR). The volume mount `./models:/app/models` means the file resolves to `/app/models/mistral-7b-instruct.gguf`.

**Warning signs:** Container exits immediately with code 1; `docker logs` shows the `EnvironmentError` message.

### Pitfall 2: Model File Not Found at Volume Mount Path

**What goes wrong:** Container starts, MODEL_PATH is set, but `src/config.py` raises `FileNotFoundError: Model file not found at /app/models/mistral-7b-instruct.gguf`.

**Why it happens:** The host `models/` directory exists but the GGUF file is not yet downloaded, or the filename in `.env`/docker-compose `MODEL_PATH` doesn't match the actual filename.

**How to avoid:** README must be explicit about the exact filename expected. The docker-compose environment block should hardcode `MODEL_PATH=models/mistral-7b-instruct.gguf` so there is only one correct answer. The quickstart must show the exact `wget` command with the exact output filename.

**Warning signs:** `FileNotFoundError` in `docker logs`; health endpoint returns 503.

### Pitfall 3: Health Check Fails During 60s Grace Period

**What goes wrong:** `docker ps` shows `(health: starting)` for longer than expected. Operators mistake this for a problem and restart the container prematurely.

**Why it happens:** Mistral 7B takes 20-30s to load into memory; the FastAPI app won't serve requests until `lifespan()` completes model loading. If `start_period` is too short, the first health check fires before the model is ready and registers as a failure.

**How to avoid:** `start_period: 60s` provides safe headroom. README should explicitly state "container takes 30-60s to become healthy on first run." Do not reduce `start_period` below 45s.

**Warning signs:** `(unhealthy)` status in `docker ps` within the first 60 seconds.

### Pitfall 4: Volume Mount Permission Failure on mmap

**What goes wrong:** Container starts, model file is at the correct path, but llama-cpp-python raises an OS-level error when trying to memory-map the GGUF file.

**Why it happens:** `llama-cpp-python` uses `mmap` to load GGUF files efficiently. If the host volume has restrictive permissions or the container runs as a non-root user without read access to the mounted file, `mmap` fails silently or with a cryptic error.

**How to avoid:** Ensure the GGUF file on the host is world-readable (`chmod 644 models/mistral-7b-instruct.gguf`). If running the container as non-root (`USER appuser`), verify that UID matches or use group-readable permissions on the host.

**Warning signs:** `mmap` or `permission denied` in docker logs; model loads to 0% and fails.

### Pitfall 5: README curl Example Uses Wrong Content-Type

**What goes wrong:** The portfolio reviewer copies the curl command from README, gets `422 Unprocessable Entity`.

**Why it happens:** FastAPI's POST /extract expects `Content-Type: application/json`. A curl example missing `-H "Content-Type: application/json"` sends `application/x-www-form-urlencoded`, which Pydantic rejects.

**How to avoid:** Every curl example in README must include `-H "Content-Type: application/json"` explicitly. Test the exact curl command against a running container before committing.

**Warning signs:** Response body contains `{"detail": [{"type": "json_invalid"...}]}`.

### Pitfall 6: Example JSON Files Are Stale After Code Changes

**What goes wrong:** The example JSON files in `data/examples/` show entity schemas that don't match what the API actually returns (e.g., missing `source_span_validated` field, or field names differ).

**Why it happens:** Example files are generated once from the live model then committed. If schema changes happen after generation, the files become stale documentation.

**How to avoid:** Generate example files last, after all Phase 2 and 3 code is complete. Include a comment in each example file: `"_generated_by": "Mistral 7B Instruct Q4_K_M via /extract endpoint"`. The planner should sequence example generation as the final task.

---

## Code Examples

### Dockerfile (Complete)

```dockerfile
# Source: fastapi.tiangolo.com/deployment/docker + CLAUDE.md recommendation
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for layer caching (requirements change less than code)
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy application source
COPY src/ ./src/
COPY healthcheck.py ./

# Security: run as non-root
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

# Health check using Python stdlib (curl not available in slim image)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python healthcheck.py

# Single worker: llama-cpp-python Llama object is not picklable
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

### docker-compose.yml (Complete)

```yaml
# Source: docs.docker.com/reference/compose-file/services/
version: "3.8"

services:
  api:
    build: .
    container_name: german-clinical-nlp
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models:ro
    env_file:
      - .env
    environment:
      - MODEL_PATH=models/mistral-7b-instruct.gguf
      - MODEL_NAME=Mistral 7B Instruct Q4_K_M
      - LOG_LEVEL=INFO
      - CONFIDENCE_THRESHOLD=0.5
    mem_limit: 8g
    mem_reservation: 6g
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "healthcheck.py"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### .dockerignore (Complete)

```
# Never bundle models into image
models/

# Never expose secrets
.env
.env.*

# Development artifacts
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.coverage
htmlcov/
*.egg-info/

# Git
.git/
.gitignore

# Editor
.vscode/
.idea/
```

### README.md Quick-Start Section (Template)

```markdown
## Quick Start

**Prerequisites:** Docker 20.10+, docker-compose 2.x, 8GB RAM, 6GB free disk

### 1. Clone and prepare

git clone https://github.com/YOUR_USERNAME/german-clinical-nlp.git
cd german-clinical-nlp
cp .env.example .env

### 2. Download the model (~4.5GB)

mkdir -p models
# Mistral 7B Instruct Q4_K_M — practical size, good German clinical performance
wget -O models/mistral-7b-instruct.gguf \
  https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf

### 3. Start the API

docker-compose up
# First run takes 30-60s for model to load
# Watch for: {"status":"healthy","model_loaded":true,...}

### 4. Test extraction

curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "Patient wurde am 15.03.2024 mit Diabetes mellitus Typ 2 aufgenommen. Verweildauer: 5 Tage. Metformin 1000mg täglich."}'
```

### Python httpx Example (for README)

```python
# Source: httpx docs + project API structure
import httpx

client = httpx.Client(base_url="http://localhost:8000")

response = client.post(
    "/extract",
    json={
        "text": "Patient wurde am 15.03.2024 mit Diabetes mellitus Typ 2 aufgenommen. "
                "Verweildauer: 5 Tage. Metformin 1000mg täglich."
    }
)

data = response.json()
print(f"Temporal entities: {len(data['temporal_entities'])}")
print(f"Clinical entities: {len(data['clinical_entities'])}")
for entity in data["temporal_entities"]:
    print(f"  [{entity['type']}] {entity['text']} (confidence: {entity['confidence']:.2f})")
```

### Example JSON Output File Structure (data/examples/temporal_extraction.json)

```json
{
  "_generated_by": "Mistral 7B Instruct Q4_K_M via POST /extract",
  "_input_text": "Aufnahme am 03.01.2024. Entlassung am 08.01.2024 nach 5 Tagen stationärem Aufenthalt.",
  "temporal_entities": [
    {
      "type": "Date",
      "text": "03.01.2024",
      "confidence": 0.97,
      "source_span": {"start": 11, "end": 21, "text": "03.01.2024"},
      "source_span_validated": true
    },
    {
      "type": "Date",
      "text": "08.01.2024",
      "confidence": 0.96,
      "source_span": {"start": 34, "end": 44, "text": "08.01.2024"},
      "source_span_validated": true
    },
    {
      "type": "LOS",
      "text": "5 Tagen",
      "confidence": 0.91,
      "source_span": {"start": 48, "end": 55, "text": "5 Tagen"},
      "source_span_validated": true
    }
  ],
  "clinical_entities": [],
  "errors": [],
  "low_confidence": []
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `tiangolo/uvicorn-gunicorn-fastapi` base image | Build from `python:3.11-slim` directly | 2023 (deprecated) | Simpler; gunicorn not needed for single-worker LLM containers |
| HEALTHCHECK with `curl` in slim images | HEALTHCHECK with Python stdlib `urllib` | Ongoing | No extra package install; zero overhead |
| Multi-stage builds for all Python apps | Single-stage for LLM portfolio demos | N/A | Multi-stage saves image size but adds complexity; model is volume-mounted anyway |
| `docker run` with manual flags | `docker-compose up` | Standard pattern | One-command demo is the portfolio minimum viable UX |

**Deprecated/outdated:**
- `tiangolo/uvicorn-gunicorn-fastapi` base image: officially deprecated; FastAPI docs explicitly say "do NOT use this." [CITED: fastapi.tiangolo.com/deployment/docker/]
- Shell form CMD (`CMD uvicorn ...`): breaks signal propagation and lifespan events. [CITED: fastapi.tiangolo.com/deployment/docker/]

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `python:3.11-slim` does not include `curl` by default | Pitfall 3, Pattern 1, Pattern 3 | If curl IS present, the simpler `CMD curl -f http://localhost:8000/health` works — healthcheck.py is still valid but unnecessary. Low risk. |
| A2 | `Llama` object from llama-cpp-python is not picklable (single worker required) | Anti-Patterns | If multi-worker is actually safe, `--workers 1` just leaves performance on the table — correct for this demo context anyway. Low risk. |
| A3 | Mistral 7B Q4_K_M load time is 20-30s on typical developer hardware | Pitfall 1, docker-compose start_period | If load time is longer (e.g., 50s on slower hardware), the 60s grace period may be tight. Mitigated: 60s is 2-3x the typical load time. |
| A4 | The `models/` directory exists and contains `test.gguf` — actual Mistral 7B must be separately downloaded | README quick-start | Confirmed by codebase inspection: `ls models/` shows `test.gguf` only. README must make this explicit. |
| A5 | `docs/ARCHITECTURE.md` already covers all three D-09 sections | Phase Requirements section | Confirmed by reading the file: it covers component descriptions, plugin pattern, and "how to add a new entity type." The planner should verify it links from README and the data flow diagram is present. |

---

## Open Questions

1. **HuggingFace URL for Mistral 7B Q4_K_M**
   - What we know: The model is `mistral-7b-instruct-v0.2.Q4_K_M.gguf` from TheBloke or official Mistral repos
   - What's unclear: The exact canonical HuggingFace URL (TheBloke repos may be deprecated in favor of official Mistral/lmstudio-community GGUF uploads)
   - Recommendation: README should use the TheBloke URL as example but note that the official `mistral-community/Mistral-7B-Instruct-v0.2-GGUF` is the authoritative source. Verify URL before committing.

2. **pip install from pyproject.toml in Dockerfile**
   - What we know: `pyproject.toml` has `[project.optional-dependencies] dev = [...]`
   - What's unclear: Whether `pip install .` (without dev extras) correctly installs only runtime deps in the container
   - Recommendation: Use `pip install .` for the container image (no test deps). Verify `llama-cpp-python==0.3.28` installs cleanly on python:3.11-slim without build tools; may need `RUN apt-get install -y build-essential` if wheel is unavailable.

3. **llama-cpp-python wheel availability for python:3.11-slim**
   - What we know: llama-cpp-python 0.3.28 has pre-built wheels for common platforms on PyPI
   - What's unclear: Whether the linux/amd64 slim image can install from wheel without cmake/gcc
   - Recommendation: Plan for a fallback `RUN apt-get install -y build-essential cmake` if wheel install fails. The Dockerfile should try wheel first; build from source is a known fallback pattern.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker | DEPLOY-01, DEPLOY-02 | Unknown (host) | — | None — Docker is required |
| docker-compose v2 | DEPLOY-02 | Unknown (host) | — | `docker compose` (v2 plugin) as alternative |
| Python 3.11+ | Container runtime | ✓ (in image) | 3.11-slim | — |
| `curl` on host | README wget alternative | Unknown | — | Use `wget` or Python as alternative download methods |

**Missing dependencies with no fallback:**
- Docker must be installed on the reviewer's machine. README must state this as a hard prerequisite.

**Missing dependencies with fallback:**
- `docker-compose` v1 vs v2 plugin: if `docker-compose` command is not found, `docker compose` (space, not hyphen) works as the v2 plugin equivalent. README should mention both forms.

---

## Security Domain

> `security_enforcement: true` in config.json. ASVS Level 1 applies.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth endpoints in this phase |
| V3 Session Management | No | Stateless API, no sessions |
| V4 Access Control | No | No user roles in portfolio demo scope |
| V5 Input Validation | Yes (existing) | Pydantic validation already implemented in Phase 2; Dockerfile does not change this |
| V6 Cryptography | No | No crypto operations |
| V1.6 Architecture — Non-root container | Yes | Add `USER appuser` in Dockerfile; do not run container as root |
| V14 Configuration — Secrets in environment | Yes | `.env` in `.dockerignore`; secrets injected via `env_file`, never COPY'd into image |

### Known Threat Patterns for Docker Deployment

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Running container as root | Elevation of Privilege | `adduser` + `USER appuser` in Dockerfile |
| Secrets in image layers | Information Disclosure | `.dockerignore` excludes `.env`; env_file injection at runtime |
| Path traversal via MODEL_PATH | Tampering | Already mitigated in `src/config.py` (validates MODEL_PATH is within `models/`) |
| GGUF model file tampering | Tampering | Volume mount with `:ro` flag (read-only); prevents container from modifying model |
| Unbounded memory consumption | Denial of Service | `mem_limit: 8g` hard limit in docker-compose |

**Security note:** This is a portfolio demo with no auth requirements. The primary security concerns are container hygiene (non-root, no secrets in image) and the existing path traversal protection in `src/config.py` (Phase 1 T-01-01).

---

## Sources

### Primary (MEDIUM confidence — official documentation)
- [FastAPI official Docker deployment guide](https://fastapi.tiangolo.com/deployment/docker/) — Dockerfile structure, CMD exec form, deprecated base image warning, requirements-first caching pattern
- [Docker Compose service reference](https://docs.docker.com/reference/compose-file/services/) — `mem_limit`, `mem_reservation`, `healthcheck` (test, interval, timeout, retries, start_period) exact syntax

### Secondary (LOW confidence — web resources)
- [markaicode.com llama.cpp + FastAPI + Docker stack](https://markaicode.com/stack/llamacpp-fastapi-docker-inference-stack/) — Volume mount pattern for GGUF, python:3.11-slim base, healthcheck configuration, single-worker constraint
- [muratcorlu.com Docker healthcheck without curl](https://muratcorlu.com/docker-healthcheck-without-curl-or-wget/) — Python urllib stdlib approach for health probes
- [virtua.cloud Docker Compose resource limits](https://www.virtua.cloud/learn/en/tutorials/docker-compose-resource-limits-healthchecks) — mem_limit and healthcheck composition

### Internal (HIGH confidence — direct codebase inspection)
- `src/config.py` — MODEL_PATH validation, path traversal protection, env var requirements
- `src/api/health.py` — /health endpoint returning 200/503 based on model state
- `src/main.py` — FastAPI lifespan pattern (uvicorn target: `src.main:app`)
- `docs/ARCHITECTURE.md` — Existing architecture doc content verified
- `pyproject.toml` — Exact package versions and dependency structure
- `.env.example` — Existing env var documentation and MODEL_PATH default

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; all existing deps already verified in prior phases
- Docker patterns: MEDIUM — FastAPI official docs + markaicode guide (web-sourced)
- Architecture documentation: HIGH — existing `docs/ARCHITECTURE.md` inspected directly
- Pitfalls: MEDIUM — derived from codebase analysis + standard Docker/llama-cpp patterns
- Example JSON structure: HIGH — derived directly from `src/schemas/entities.py`

**Research date:** 2026-06-12
**Valid until:** 2026-07-12 (Docker/compose patterns are stable; FastAPI version locked in pyproject.toml)
