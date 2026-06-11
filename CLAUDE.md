<!-- GSD:project-start source:PROJECT.md -->

## Project

**German Clinical NLP Pipeline**

A portfolio-focused information extraction pipeline for German clinical text. Takes German clinical notes as input and extracts structured medical entities (dates, diagnoses, length-of-stay indicators, medications) as validated JSON. Built to showcase healthcare NLP, LLM engineering, and production API skills to recruiters and potential employers.

**Core Value:** Demonstrates production-ready clinical NLP with local LLM deployment, structured output validation, and explicit hallucination handling — all with German medical text.

### Constraints

- **Language**: German clinical text only
- **Model**: Local GGUF models via llama-cpp-python (no cloud API dependencies)
- **Deployment**: Docker-based local development (no cloud infra required)
- **Data privacy**: No real patient data — synthetic/public datasets only
- **Scope**: Portfolio showcase — production hardening deferred

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

## Executive Summary

## Core Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **llama-cpp-python** | Latest (0.3.x+) | Local GGUF model deployment, structured output via JSON schema | Native JSON schema mode for structured outputs, no cloud dependencies, production-ready OpenAI-compatible API, active development with 2025+ features. **HIGH confidence** (Context7 verified) |
| **FastAPI** | 0.136.3+ | REST API framework | Modern async support, automatic OpenAPI docs, native Pydantic v2 integration, industry standard for ML/NLP APIs in 2025. **HIGH confidence** (Context7 verified current version) |
| **Pydantic** | 2.x (2.8.0+) | Data validation and structured output schemas | Fast Rust-core validation, native structured output support for LLMs, experimental partial validation for streaming, type safety with zero boilerplate. **HIGH confidence** (Context7 verified v2 features) |
| **Python** | 3.11 or 3.12 | Runtime | Stable performance, async improvements, type hinting maturity. 3.13 not recommended yet for production LLM work (ecosystem compatibility). **MEDIUM confidence** (standard practice, not verified in docs) |

### Rationale: Why llama-cpp-python over transformers/HuggingFace?

- **GGUF ecosystem dominance**: All state-of-the-art models (Llama 3.3, Mistral, Qwen) available in optimized GGUF format
- **Memory efficiency**: Q4_K_M/Q5_K_M quantization provides 95-98% quality with 75% size reduction
- **Zero GPU requirement**: CPU-only deployment sufficient for portfolio demo, optional GPU acceleration available
- **Structured output native**: Built-in JSON schema mode (response_format parameter), no additional libraries needed
- **Production patterns**: OpenAI-compatible API server included, mature Docker deployment patterns

## LLM Models

| Model | Size | Format | Purpose | Why |
|-------|------|--------|---------|-----|
| **Llama 3.3 70B Instruct** | ~40 GB (Q4_K_M) | GGUF | Primary extraction model | Multilingual (includes German), state-of-the-art instruction following, excellent structured output compliance, widely available in GGUF. **HIGH confidence** (official Llama 3.3 docs confirm German support) |
| **Llama 3.3 70B Instruct** | ~48 GB (Q5_K_M) | GGUF | Higher quality fallback | Use if sufficient VRAM/RAM, +3% quality over Q4_K_M for complex medical reasoning. **HIGH confidence** |
| **Mistral 7B Instruct v0.2** | ~4.5 GB (Q4_K_M) | GGUF | Lightweight alternative for testing | Smaller footprint, faster inference, adequate for simpler entity extraction (dates, medications). **MEDIUM confidence** (community usage, not medically validated) |

### Why NOT German-Specific Medical Models?

- Not available in GGUF format (HuggingFace transformers only)
- Require GPU for reasonable inference speed
- Designed for embedding/classification, not generative extraction
- Add infrastructure complexity (transformers + torch dependencies)

### Quantization Strategy

| Format | Size (7B) | Size (70B) | Quality Loss | Use Case | Confidence |
|--------|-----------|------------|--------------|----------|------------|
| **Q4_K_M** | ~4.5 GB | ~40 GB | ~3.5% | **Default recommendation** - Best size/quality tradeoff | **HIGH** (2026 benchmarks) |
| **Q5_K_M** | ~5.3 GB | ~48 GB | ~1% | Use when quality > size priority | **HIGH** |
| Q8_0 | ~8 GB | ~75 GB | <0.5% | Overkill for most tasks | MEDIUM |

## Structured Output Libraries

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| **Pydantic** | 2.8.0+ | Define extraction schemas (entities, validators) | **Always** - Core validation layer | **HIGH** (Context7) |
| **Instructor** (optional) | Latest | Simplified LLM → Pydantic workflow | Optional - llama-cpp-python has native schema support | **MEDIUM** (adds abstraction, not required) |
| **Outlines** (optional) | Latest | Grammar-constrained generation | **Avoid** - llama-cpp-python has native JSON schema mode, Outlines adds compilation overhead | **MEDIUM** (verified Outlines docs show llama.cpp integration but with performance cost) |

### Recommendation: Use Native JSON Schema Mode

- **Instructor**: Adds retry logic and convenience wrappers but llama-cpp-python has native schema support (no extra dependency needed for basic use)
- **Outlines**: Adds 40% throughput overhead vs native approach (2025 benchmarks), longer compilation times

## API Layer

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **FastAPI** | 0.136.3+ | REST API framework | See Core Framework above | **HIGH** |
| **Uvicorn** | 0.34.0+ | ASGI server (dev) | FastAPI's default development server, excellent hot-reload | **HIGH** |
| **Gunicorn** | 23.0.0+ | Process manager (production) | Production-grade multi-worker management | **HIGH** |
| **uvicorn.workers.UvicornWorker** | - | Gunicorn worker class | Combines Gunicorn process management with Uvicorn async handling | **HIGH** (2026 best practice) |

### Production Deployment Command

## Data Layer

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **datasets** (HuggingFace) | 3.4.0+ | Load GGPONC corpus | Standard for loading research datasets, converts to pandas easily | **HIGH** (Context7 verified) |
| **pandas** | 2.2.0+ | Sample data manipulation | Industry standard, integrates with HuggingFace datasets | **HIGH** |

### German Clinical Datasets

| Dataset | Size | Content | License | Use |
|---------|------|---------|---------|-----|
| **GGPONC 2.0** | 1.87M tokens (30 guidelines) | German oncology clinical practice guidelines, entity-annotated | Freely distributable | **Primary sample data source** - No patient data, largest annotated German medical corpus | **HIGH confidence** |
| **BRONCO150** | 150 discharge letters | De-identified German discharge letters | Restricted | **Avoid** - Access restrictions, privacy concerns | **MEDIUM confidence** |

## Supporting Libraries

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| **python-dotenv** | 1.0.0+ | Environment variable management | Load .env files for local dev config | **HIGH** (standard practice) |
| **loguru** | 0.7.0+ | Structured logging | Production logging with JSON output, rotation, async support | **HIGH** (2026 production standard) |
| **httpx** | 0.28.0+ | HTTP client for testing | Async API testing with pytest | **HIGH** |
| **pytest** | 8.x+ | Testing framework | Standard Python testing | **HIGH** |
| **pytest-asyncio** | 0.24.0+ | Async test support | Test async FastAPI endpoints | **HIGH** (2026 best practice: asyncio_mode="auto") |

### Why Loguru over stdlib logging?

- **Simplicity**: Single unified API vs complex stdlib handlers/formatters
- **Structured logging**: Native JSON output with `serialize=True`
- **Production features**: Automatic rotation, retention, async logging, @logger.catch decorator
- **Performance**: Non-blocking async logging for high-throughput APIs

## Containerization

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Docker** | 20.10+ | Container runtime | Standard containerization | **HIGH** |
| **docker-compose** | 2.x | Multi-container orchestration | Dev environment simplicity | **HIGH** |

### Base Image Recommendation

- Smaller attack surface, faster builds
- llama-cpp-python wheels available (no compile needed)
- Sufficient for CPU inference

## Installation

### Core Dependencies

# Core framework

# Production server

# Data handling

# Configuration and logging

# Testing

### Optional Enhancements

# If using instructor for simplified LLM → Pydantic workflow

# If using outlines for constrained generation (not recommended, see above)

### llama-cpp-python GPU Support (Optional)

# For CUDA GPU acceleration (NVIDIA)

# For Metal GPU acceleration (Apple Silicon)

## Alternatives Considered

| Category | Recommended | Alternative | Why Not Alternative | Confidence |
|----------|-------------|-------------|---------------------|------------|
| **LLM Runtime** | llama-cpp-python | transformers + torch | Requires GPU, larger memory footprint, no GGUF support | **HIGH** |
| **LLM Runtime** | llama-cpp-python | Ollama | Less control over inference parameters, harder to integrate custom validation | **MEDIUM** |
| **API Framework** | FastAPI | Flask | No async support, no automatic OpenAPI docs, no native Pydantic integration | **HIGH** |
| **Validation** | Pydantic v2 | marshmallow | Slower, no LLM structured output ecosystem, less type-safe | **MEDIUM** |
| **Logging** | loguru | stdlib logging | Complex configuration, no structured logging by default | **HIGH** |
| **Structured Output** | Native llama-cpp | Outlines | 40% throughput overhead, compilation latency | **MEDIUM** |
| **Structured Output** | Native llama-cpp | Instructor | Adds abstraction without critical features for this project | **LOW** (subjective) |
| **German Medical Model** | Llama 3.3 (multilingual) | medBERT.de | Not in GGUF format, requires transformers stack | **HIGH** |
| **Testing** | pytest + httpx | unittest | Less ergonomic, no async fixtures, less plugin ecosystem | **HIGH** |

## Architecture Decisions

### 1. Local LLM Deployment (No Cloud APIs)

### 2. Structured Output Strategy

### 3. Multilingual Model over German-Specific

### 4. GGPONC 2.0 for Sample Data

### 5. Docker-Only Deployment

## Stack Validation Checklist

- [x] **Versions are current**: FastAPI 0.136.3, Pydantic 2.8+, llama-cpp-python 0.3+ verified from Context7 and official docs
- [x] **German support confirmed**: Llama 3.3 official docs list German as supported language
- [x] **Structured output verified**: llama-cpp-python JSON schema mode documented in Context7 and official repo
- [x] **Dataset accessibility**: GGPONC 2.0 confirmed on HuggingFace (bigbio/ggponc2), freely distributable
- [x] **Production patterns validated**: Gunicorn + Uvicorn workers documented in 2026 FastAPI deployment guides
- [x] **Quantization benchmarks verified**: Q4_K_M and Q5_K_M quality metrics from 2026 GGUF quantization guides

## Open Questions & Research Gaps

## Sources

### High Confidence (Context7 / Official Docs)

- [llama-cpp-python documentation](https://github.com/abetlen/llama-cpp-python) - Context7 verified structured output support
- [Pydantic documentation](https://github.com/pydantic/pydantic) - Context7 verified v2 features
- [FastAPI documentation](https://github.com/fastapi/fastapi) - Context7 verified version 0.136.3
- [Outlines documentation](https://github.com/dottxt-ai/outlines) - Context7 verified llama.cpp integration
- [Llama 3.3 official model card](https://www.llama.com/docs/model-cards-and-prompt-formats/llama3_3/) - German language support confirmed

### Medium Confidence (Web Search Verified)

- [GGPONC corpus paper](https://arxiv.org/abs/2007.06400) - Verified corpus structure and license
- [GGPONC 2.0 on HuggingFace](https://huggingface.co/datasets/bigbio/ggponc2) - Verified dataset availability
- [medBERT.de paper](https://arxiv.org/pdf/2303.08179) - Verified German medical BERT model
- [Critical assessment of German clinical NLP](https://academic.oup.com/jamiaopen/article/5/4/ooac087/6827559) - BioGottBERT evaluation
- [FastAPI deployment guide 2026](https://www.zestminds.com/blog/fastapi-deployment-guide/) - Production best practices
- [llama.cpp production stack guide](https://markaicode.com/stack/llamacpp-fastapi-docker-inference-stack/) - Docker deployment patterns
- [GGUF quantization guide 2026](https://bmdpat.com/blog/gguf-quantization-q4-q5-q8-explained-2026) - Q4_K_M vs Q5_K_M benchmarks
- [Python logging best practices 2026](https://tutorials.technology/tutorials/python-logging-best-practices-structlog-loguru-2026.html) - Loguru vs stdlib comparison
- [Instructor library documentation](https://python.useinstructor.com/) - Structured LLM outputs with Pydantic
- [Structured output generation guide](https://medium.com/@emrekaratas-ai/structured-output-generation-in-llms-json-schema-and-grammar-based-decoding-6a5c58b698a6) - JSON schema approach
- [pytest-asyncio guide 2026](https://qaskills.sh/blog/pytest-asyncio-testing-guide) - Async testing best practices

### Low Confidence (Unverified Assumptions)

- German prompting strategies for clinical NLP - No specific research found
- Llama 3.3 vs medBERT.de accuracy comparison - No benchmarks found
- GGPONC entity type compatibility - Assumed from corpus description, not verified

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
