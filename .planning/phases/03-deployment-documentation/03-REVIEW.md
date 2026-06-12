---
phase: 03-deployment-documentation
reviewed: 2026-06-12T17:13:48Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - .dockerignore
  - .env.example
  - Dockerfile
  - README.md
  - data/examples/diagnosis_extraction.json
  - data/examples/medication_los_extraction.json
  - data/examples/temporal_extraction.json
  - docker-compose.yml
  - docs/ARCHITECTURE.md
  - healthcheck.py
  - pyproject.toml
findings:
  critical: 1
  warning: 5
  info: 4
  total: 10
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-06-12T17:13:48Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Reviewed all deployment and documentation artifacts for the German Clinical NLP pipeline. The infrastructure files are generally well-structured with good security posture (non-root user, read-only volume mount, no secrets in image). However, there is one critical correctness failure in the Dockerfile's dependency-installation layer, a systematic documentation error where all `source_span` character offsets in the two README example responses are wrong, and a significant configuration trap where `docker-compose.yml` silently overrides every variable documented in `.env.example`, making user edits to `.env` ineffective.

---

## Critical Issues

### CR-01: Dockerfile `pip install .` runs before `src/` is copied — build will fail or produce a broken package layer

**File:** `Dockerfile:14`

**Issue:** The Dockerfile copies only `pyproject.toml` before running `pip install --no-cache-dir .`, then copies `src/` in a later layer. The comment explains this as a layer-caching optimisation (install deps before copying frequently-changing source code). However `pyproject.toml` declares `packages = ["src"]` (via `[tool.setuptools]`). When setuptools processes `pip install .` without the `src/` directory present, behaviour is pip/setuptools-version-dependent:

- Newer setuptools (>= 61 strict mode) raises `PackageNotFoundError` and the build fails outright.
- Older setuptools silently installs an empty stub for `src` in site-packages and installs the declared dependencies. The container then starts with `src` registered in site-packages as an empty package. At runtime uvicorn resolves `src.main:app` from the local `/app/src/` directory (because WORKDIR is in sys.path) rather than site-packages, so the API may work — but the installed package is corrupt/empty and the behaviour is fragile.

The layer-caching intent is sound; the implementation is not. The standard pattern for this is to install only the declared dependencies (not the package itself) in the cached layer.

**Fix:** Replace the single `pip install .` call with two steps: first install only the runtime dependencies, then install the package after copying source:

```dockerfile
COPY pyproject.toml ./

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential cmake && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir \
        "llama-cpp-python==0.3.28" \
        "fastapi==0.136.3" \
        "pydantic==2.13.4" \
        "uvicorn[standard]>=0.34.0" \
        "python-dotenv>=1.0.0" \
        "loguru>=0.7.0"

# Copy application source (changes more frequently than deps)
COPY src/ ./src/
COPY healthcheck.py ./

# Install the package itself after source is present
RUN pip install --no-cache-dir --no-deps .
```

Alternatively, add a `requirements.txt` extracted from pyproject.toml and use `pip install -r requirements.txt` in the cached layer, then `pip install --no-deps .` after copying source.

---

## Warnings

### WR-01: `docker-compose.yml` `environment:` block silently overrides all variables documented in `.env.example`

**File:** `docker-compose.yml:15-22`

**Issue:** The compose file uses both `env_file: .env` and an `environment:` block. Docker Compose applies the `environment:` block _after_ `env_file`, so any key present in both sources takes the value from `environment:`. The `environment:` block hardcodes all four variables that `.env.example` documents as user-configurable: `MODEL_PATH`, `MODEL_NAME`, `LOG_LEVEL`, and `CONFIDENCE_THRESHOLD`. A user who follows the README instructions (`cp .env.example .env`) and edits `.env` to point at a different model file or change the log level will see no effect — their changes are silently discarded.

**Fix:** Remove the hardcoded defaults from the `environment:` block and let them be sourced exclusively from the `env_file`. Keep only values that must be forced regardless of user config in `environment:`:

```yaml
env_file:
  - .env
# No environment: block needed — all vars are in .env.example with correct defaults
```

If the MODEL_PATH comment (explaining container-relative path resolution) is important to preserve, add it to `.env.example` instead, where the user can actually modify it.

---

### WR-02: All `source_span` character offsets in the README Quick Start response are wrong

**File:** `README.md:63-95`

**Issue:** The Quick Start section shows an expected API response for the input text:

```
Patient wurde am 15.03.2024 mit Diabetes mellitus Typ 2 aufgenommen. Verweildauer: 5 Tage. Metformin 1000mg täglich.
```

Every single `source_span` offset in that response block is incorrect. Verified by Python string slicing:

| Entity | README start:end | Actual start:end | README slice resolves to |
|--------|-----------------|-----------------|--------------------------|
| `15.03.2024` | 18:28 | **17:27** | `"5.03.2024 "` |
| `Diabetes mellitus Typ 2` | 34:57 | **32:55** | `"abetes mellitus Typ 2 a"` |
| `5 Tage` | 71:77 | **83:89** | `"rweild"` |
| `Metformin 1000mg` | 85:101 | **91:107** | `"Tage. Metformin "` |

Because the README is the primary portfolio artifact (what recruiters and evaluators read first), shipping it with demonstrably wrong `source_span_validated: true` alongside incorrect offsets directly undermines the credibility of the hallucination-detection feature.

**Fix:** Replace the response block with correct offsets (or regenerate it by running the actual API):

```json
"source_span": {"start": 17, "end": 27, "text": "15.03.2024"}
"source_span": {"start": 32, "end": 55, "text": "Diabetes mellitus Typ 2"}
"source_span": {"start": 83, "end": 89, "text": "5 Tage"}
"source_span": {"start": 91, "end": 107, "text": "Metformin 1000mg"}
```

---

### WR-03: All `source_span` offsets in the README "Example Extraction Output" response are wrong (and Bronchialkarzinom has an additional length error)

**File:** `README.md:207-249`

**Issue:** The "Example Extraction Output" section contains a second JSON response block for the input:

```
Stationäre Aufnahme am 03.01.2024. Entlassung am 10.01.2024. Gesamtaufenthalt: 7 Tage.\nPrimärdiagnose: Bronchialkarzinom (C34.1). Chemotherapie mit Carboplatin begonnen.
```

Verified offsets:

| Entity | README start:end | Actual start:end | Correct? |
|--------|-----------------|-----------------|----------|
| `03.01.2024` | 22:32 | **23:33** | No — off by 1 |
| `10.01.2024` | 48:58 | **49:59** | No — off by 1 |
| `7 Tage` | 78:84 | **79:85** | No — off by 1 |
| `Bronchialkarzinom (C34.1)` | 102:126 | **103:128** | No — start off by 1, span length wrong (24 vs 25) |
| `Carboplatin` | 148:159 | **148:159** | Correct |

`Bronchialkarzinom (C34.1)` has a compound error: start is off by 1 (102 vs 103) _and_ the end (126) implies a span length of 24, but the entity text is 25 characters long (`len('Bronchialkarzinom (C34.1)') == 25`). Only `Carboplatin` is correct in this block.

**Fix:** Replace with correct offsets:
```json
{"start": 23, "end": 33, "text": "03.01.2024"}
{"start": 49, "end": 59, "text": "10.01.2024"}
{"start": 79, "end": 85, "text": "7 Tage"}
{"start": 103, "end": 128, "text": "Bronchialkarzinom (C34.1)"}
```

---

### WR-04: Unpinned base image tag in Dockerfile exposes build to silent upstream changes

**File:** `Dockerfile:1`

**Issue:** `FROM python:3.11-slim` uses a mutable floating tag. Docker Hub can update the image layer behind this tag (OS security patches, Python minor version bumps) at any time. Any subsequent `docker build` or CI pull may produce a different image than before without any change to the Dockerfile. For a portfolio project showcasing production readiness, this contradicts the "reproducible build" principle and means security regression is possible without visibility.

**Fix:** Pin to a specific image digest. Find the current digest via `docker inspect python:3.11-slim` or Docker Hub and use:

```dockerfile
FROM python:3.11-slim@sha256:<digest>
```

At minimum, pin to a patch-level tag:

```dockerfile
FROM python:3.11.12-slim
```

---

### WR-05: `docs/ARCHITECTURE.md` testing example is missing `TestClient` import — example code will not run

**File:** `docs/ARCHITECTURE.md:417-441`

**Issue:** The "Testing Extractors" section provides a test function that calls `TestClient(app)` on line 430 but never imports `TestClient`. The example as written will raise `NameError: name 'TestClient' is not defined` if a developer copies it.

```python
# Current — missing import
from src.main import app
from unittest.mock import MagicMock
# ... TestClient(app) used below without being imported
```

**Fix:** Add the import at the top of the example:

```python
from fastapi.testclient import TestClient
from src.main import app
from unittest.mock import MagicMock
```

---

## Info

### IN-01: `pyproject.toml` uses a non-standard `packages = ["src"]` declaration — namespace collision risk

**File:** `pyproject.toml:33-34`

**Issue:** `[tool.setuptools] packages = ["src"]` installs a package named `src` into site-packages. `src` is an extremely generic name that collides with any other installed package that uses the same convention. The project's import path (`src.main`, `src.api`, `src.extraction`) works in development because Python resolves the local `/app/src/` directory first when `/app` is in sys.path. However, a future `pip install` of any other package that installs a `src` namespace could shadow or conflict with this package.

**Fix:** Rename the package directory (e.g., `german_clinical_nlp/`) and update the import path, or use `find_packages` with `package_dir`:

```toml
[tool.setuptools.packages.find]
where = ["."]
include = ["src*"]
```

Or rename the import root to something project-specific:

```toml
[tool.setuptools]
package-dir = {"german_clinical_nlp" = "src"}
packages = ["german_clinical_nlp"]
```

---

### IN-02: README links to a HuggingFace URL that may be a dead link (TheBloke account)

**File:** `README.md:33-34`

**Issue:** The Quick Start model download step uses `https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/...`. The TheBloke HuggingFace organisation was migrated in 2024 and many model repositories were archived or deleted. The README already documents an alternative source (`mistral-community`) as a blockquote, but uses the potentially dead URL as the primary command.

**Fix:** Swap primary and alternative URLs. Use the `mistral-community` URL as the primary `wget` target since it is maintained by the official Mistral team:

```bash
wget -O models/mistral-7b-instruct.gguf \
  https://huggingface.co/mistral-community/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/Mistral-7B-Instruct-v0.2.Q4_K_M.gguf
```

---

### IN-03: Duplicate healthcheck definition across Dockerfile and `docker-compose.yml`

**File:** `docker-compose.yml:28-35`, `Dockerfile:28-29`

**Issue:** Both files define an identical healthcheck (`python healthcheck.py`, interval 30s, timeout 10s, retries 3, start_period 60s). Docker Compose healthcheck overrides the Dockerfile `HEALTHCHECK` directive when both are present. The duplication means future changes to the healthcheck must be made in two places and can silently diverge.

**Fix:** Remove the `HEALTHCHECK` directive from `Dockerfile` and keep the single authoritative definition in `docker-compose.yml`. This makes the compose file the single source of truth for healthcheck configuration.

---

### IN-04: `docs/ARCHITECTURE.md` symptom extractor example hardcodes confidence threshold (magic number 0.5)

**File:** `docs/ARCHITECTURE.md:305`

**Issue:** The example `SymptomExtractor.extract()` implementation on line 305 contains:

```python
if entity.confidence < 0.5:
    result["low_confidence"].append(entity.model_dump())
```

The production extractors read this threshold from the `CONFIDENCE_THRESHOLD` environment variable (as documented in `.env.example`). A developer who follows this example will write an extractor that ignores the configured threshold, silently using a hardcoded value instead.

**Fix:** Show how to read the threshold from configuration in the example:

```python
import os
threshold = float(os.environ.get("CONFIDENCE_THRESHOLD", "0.5"))
if entity.confidence < threshold:
    result["low_confidence"].append(entity.model_dump())
```

Or document explicitly in the walkthrough that the threshold must be injected (e.g., passed to the extractor constructor or read from env).

---

_Reviewed: 2026-06-12T17:13:48Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
