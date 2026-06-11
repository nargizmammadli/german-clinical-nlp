# Project Research Summary

**Project:** German Clinical NLP Information Extraction Pipeline  
**Domain:** Healthcare/Clinical Natural Language Processing  
**Researched:** 2026-06-11  
**Confidence:** HIGH

## Executive Summary

German clinical NLP information extraction systems are best built using local LLM deployment (llama-cpp-python with GGUF models) combined with structured output validation (Pydantic) and FastAPI for production-ready APIs. The recommended approach uses multilingual Llama 3.3 70B in GGUF format rather than German-specific medical models, as the latter lack GGUF availability and would require more complex HuggingFace/transformers infrastructure. For sample data, GGPONC 2.0 provides freely distributable German oncology clinical text with entity annotations, avoiding GDPR concerns that plague real patient data.

The architecture follows a modular pipeline pattern with five core components: API Layer (FastAPI), Extraction Engine (entity-specific extractors), Validation Layer (Pydantic schemas with grounding verification), Model Management (llama-cpp-python with environment-based configuration), and Data Layer (GGPONC samples with structured output formatting). This design enables extensibility—adding new entity types requires creating a new extractor plugin rather than rewriting core logic. Critical features include local-only deployment for GDPR compliance, structured JSON output with confidence scores, and support for German medical entity types (diagnoses, medications, treatments, temporal expressions).

The primary risks are negation scope misidentification (extracting "pneumonia" from "no evidence of pneumonia"), LLM hallucination without detection (fabricating entities not in source text), German compound word tokenization failures (missing "Niereninsuffizienz" as a diagnosis), and Docker memory errors during GGUF model loading. Mitigation strategies include restricted negation scope with dependency parsing, grounding verification requiring source text spans for all extractions, German-aware model selection with tokenization testing, and explicit Docker memory limits based on model quantization size.

## Key Findings

### Recommended Stack

The 2025-2026 stack centers on local LLM deployment using llama-cpp-python (v0.3.x+) for GGUF model inference with native JSON schema mode, FastAPI (0.136.3+) for REST API infrastructure, and Pydantic v2 (2.8.0+) for structured output validation. This stack avoids cloud dependencies (critical for German healthcare GDPR compliance), leverages the GGUF ecosystem dominance (all state-of-the-art models available in optimized formats), and provides production-ready patterns with OpenAI-compatible APIs.

**Core technologies:**
- **llama-cpp-python (0.3.x+)**: Local GGUF model deployment with native JSON schema enforcement — eliminates cloud API costs, supports offline operation, demonstrates local model deployment skills
- **Llama 3.3 70B Instruct (Q4_K_M)**: Multilingual LLM with German support (~40GB GGUF) — state-of-the-art instruction following, widely available, better GGUF ecosystem vs German-specific medical models
- **FastAPI (0.136.3+)**: REST API framework with async support — modern Python API standard, automatic OpenAPI docs, native Pydantic v2 integration
- **Pydantic v2 (2.8.0+)**: Data validation and structured output schemas — fast Rust-core validation, rich validators for domain constraints, LLM structured output ecosystem
- **Gunicorn + Uvicorn workers**: Production ASGI server — combines Gunicorn process management with Uvicorn async handling, standard 2026 deployment pattern
- **Docker**: Containerization with python:3.11-slim base image — minimal attack surface, sufficient for CPU inference, reproducible deployment

**Data and utilities:**
- **GGPONC 2.0 dataset** (via HuggingFace datasets): Freely distributable German oncology clinical guidelines with entity annotations (1.87M tokens) — no patient data, largest annotated German medical corpus
- **loguru (0.7.0+)**: Structured logging with JSON output and async support — production logging standard, simpler than stdlib logging
- **pytest + pytest-asyncio + httpx**: Testing framework for async API endpoints — standard Python testing with async support

**Alternatives rejected:**
- HuggingFace transformers stack: Requires GPU, larger memory footprint, no GGUF support
- medBERT.de/BioGottBERT: German medical BERT models not available in GGUF, designed for embedding/classification not generative extraction
- Ollama: Less control over inference parameters, harder custom validation integration
- Instructor/Outlines: Add abstraction/overhead when llama-cpp-python has native JSON schema support

### Expected Features

German clinical NLP extraction systems require a baseline of table-stakes features (entity extraction, structured output, API endpoints, Docker deployment) plus differentiators that demonstrate domain expertise and production thinking. The MVP should prioritize local deployment for GDPR compliance, core entity types (diagnosis, medication, treatment, temporal), and validation that prevents hallucinations. Advanced clinical features (assertion status, temporal relations, entity normalization to ICD-10/ATC) should be deferred unless time permits.

**Must have (table stakes):**
- Named Entity Recognition for clinical entities (diagnosis, medication, treatment/procedure, temporal expressions) — fundamental capability, ICD-10/ATC/OPS compatible for German healthcare
- Structured JSON output with Pydantic schema validation — standard for API systems, prevents invalid data propagation
- Confidence scores per entity — enables filtering and human review workflows, essential for safety-critical applications
- RESTful API endpoints (/extract, /health) — standard interface pattern, required for monitoring and orchestration
- Docker containerization — expected deployment method, ensures reproducible environment
- Basic error handling with meaningful HTTP responses — users need feedback when requests fail

**Should have (competitive differentiators):**
- Local LLM deployment (no cloud APIs) — CRITICAL for German healthcare GDPR compliance, demonstrates regulatory understanding, portfolio differentiator
- Environment-based model selection — flexibility to swap models without code changes, shows production-ready configuration practices
- Modular entity pipeline — easy to add new entity types, demonstrates architectural thinking beyond immediate requirements
- Comprehensive sample data from GGPONC — demonstrates real-world applicability with realistic German clinical text
- Model metadata endpoint (/models) — transparency about active model, professional API design
- One-command demo (docker-compose up) — instant working system for portfolio evaluation by recruiters

**Should have (advanced clinical features - defer if time-constrained):**
- Assertion status detection — distinguishes confirmed vs negated vs hypothetical findings ("no evidence of cancer" vs "cancer"), production clinical NLP requirement but HIGH complexity
- German medical abbreviations handling — z.B., bzw., u.a. and clinical shorthand, shows deep domain knowledge, MEDIUM complexity
- Temporal relation extraction — links entities to time ("currently on medication" vs "discontinued"), critical for patient timelines, HIGH complexity
- GGPONC/BRONCO-aligned entity types — uses established German clinical NLP taxonomy (SNOMED CT-based), MEDIUM complexity

**Defer (v2+ or anti-features for portfolio):**
- Production cloud deployment — adds complexity without demonstrating core NLP skills, document cloud-readiness instead
- Database persistence — overkill for portfolio, return JSON responses directly
- Web UI for extraction — portfolio targets technical audience, API-first approach demonstrates backend focus
- Entity normalization (ICD-10/ATC/OPS coding) — HIGH complexity, defer to "future work" documentation
- Relation extraction (medication→dosage links) — HIGH complexity, advanced feature
- Real-time streaming extraction — not needed for batch document processing
- Comprehensive automated test suite — time-intensive, provide documented example outputs instead

### Architecture Approach

The recommended architecture follows a modular pipeline pattern with clear component boundaries and strategy-based extensibility. Five core components collaborate via well-defined interfaces: (1) API Layer handles HTTP routing and error responses, (2) Extraction Engine implements entity-specific extractors as plugins, (3) Validation Layer enforces three-stage validation (schema → domain → grounding), (4) Model Management loads GGUF models via environment configuration, and (5) Data Layer provides GGPONC samples and formats structured output.

**Major components:**
1. **API Layer (FastAPI)** — HTTP request handling, endpoint routing (/extract, /health, /models), exception handling with HTTPException
2. **Extraction Engine** — Entity-specific extractors implementing plugin pattern, prompt engineering for German clinical text, LLM invocation with JSON schema constraints
3. **Validation Layer (Pydantic)** — Three-stage validation pipeline (schema → domain → grounding), custom validators for medical constraints
4. **Model Management** — GGUF model loading via llama-cpp-python, configuration from environment variables
5. **Data Layer** — Sample clinical notes from GGPONC/BRONCO datasets, output formatting with metadata

**Key patterns:**
- Extractor plugin pattern (one per entity type)
- Three-stage validation pipeline
- Environment-based model config
- Structured output at model level
- Async-first API design

**Build order:**
1. Phase 1 - Foundation: Model Management → Data Layer → API scaffold
2. Phase 2 - Single Entity: DateEntity Pydantic model → DateExtractor → /extract endpoint
3. Phase 3 - Multi-Entity: Remaining entities → Remaining extractors → Multi-entity output
4. Phase 4 - Robustness: Grounding verification → Error handling → Confidence scoring
5. Phase 5 - Deployment: Docker configuration → Documentation

### Critical Pitfalls

1. **Negation scope misidentification** — Extracting "pneumonia" from "no evidence of pneumonia". **Prevention:** Restrict scope to 5-7 token windows, add termination triggers, use dependency parsing, test with adversarial examples.

2. **LLM hallucination without detection** — Fabricating entities not in source text. **Prevention:** Grounding verification, require source_span fields, confidence thresholds, JSON schema enforcement, explicit prompts "Extract ONLY present information".

3. **German compound word tokenization failures** — Missing "Niereninsuffizienz" or splitting incorrectly. **Prevention:** German-aware tokenization models (GBERT, GottBERT), validate entity boundaries, test suite with medical compounds.

4. **Context window truncation** — Long documents losing medication lists or timelines. **Prevention:** Models with 8K+ context, document-aware chunking on section headers, sliding window with aggregation, validate input length.

5. **Unreliable confidence scores** — High confidence on hallucinations, low on correct extractions. **Prevention:** Don't trust raw scores, calibrate on validation set, use multiple signals, ensemble verification, measure ECE/Brier Score.

6. **Docker memory errors** — OOM during model loading or mmap failures. **Prevention:** Calculate requirements (model size + 2-4GB), set --memory limits, appropriate quantization, test with production limits, health checks.

**Moderate pitfalls:** Abbreviation expansion errors, temporal expression ambiguity, medication dosage/strength confusion, limited German UMLS coverage.

**Minor pitfalls:** JSON schema violations, inadequate health checks, testing only on synthetic data, ignoring German performance in model selection, non-extensible architecture.

## Implications for Roadmap

Based on research, the project naturally divides into 5 phases following architectural dependencies and risk mitigation priorities.

### Phase 1: Foundation - Model & Infrastructure
**Rationale:** Must establish working model deployment before attempting extraction. Model selection irreversible without significant rework.

**Delivers:** 
- GGUF model loading via llama-cpp-python with environment configuration
- Validated structured output (test JSON schema enforcement)
- FastAPI scaffold with /health and /models endpoints
- GGPONC sample data loading

**Avoids pitfalls:** Model selection ignoring German performance, Docker memory errors, context window truncation

**Research flags:** STANDARD PATTERNS — llama-cpp-python and FastAPI well-documented

---

### Phase 2: Core Extraction - Single Entity (Dates)
**Rationale:** Prove end-to-end extraction with simplest entity type before adding complexity.

**Delivers:**
- DateEntity Pydantic model with validators
- DateExtractor implementing plugin pattern
- POST /extract endpoint
- Three-stage validation pipeline
- Evidence grounding verification

**Avoids pitfalls:** LLM hallucination, temporal expression ambiguity, JSON schema violations

**Research flags:** NEEDS RESEARCH — German date extraction prompting, temporal expression normalization

---

### Phase 3: Multi-Entity Extraction - Scale to All Types
**Rationale:** Demonstrate extensibility by adding diagnosis, medication, LOS extractors following plugin pattern.

**Delivers:**
- DiagnosisEntity, MedicationEntity, LOSEntity Pydantic models
- DiagnosisExtractor, MedicationExtractor, LOSExtractor
- Extraction orchestrator
- Multi-entity JSON output formatting
- German medical terminology handling

**Avoids pitfalls:** German compound tokenization failures, medication dosage/strength confusion, non-extensible architecture

**Research flags:** NEEDS RESEARCH for medication — German naming conventions, dosage formats, ATC basics

---

### Phase 4: Robustness - Production Quality
**Rationale:** Add production-grade error handling, confidence calibration, negation detection.

**Delivers:**
- Enhanced grounding verification with fuzzy matching
- Confidence thresholding with calibration
- Comprehensive API error handling
- Enhanced negation scope detection
- Validation on real GGPONC/BRONCO samples

**Avoids pitfalls:** Negation scope misidentification, unreliable confidence scores, inadequate health checks, testing only synthetic data

**Research flags:** NEEDS RESEARCH — Negation detection for German, confidence calibration methods

---

### Phase 5: Deployment - Portfolio Demonstration
**Rationale:** Package as containerized demo with comprehensive documentation.

**Delivers:**
- Dockerfile with explicit memory configuration
- docker-compose.yml
- README with setup, architecture, API examples
- Sample extraction output
- Extensibility demonstration

**Avoids pitfalls:** Docker memory errors, inadequate health checks

**Research flags:** STANDARD PATTERNS — Docker deployment well-documented

---

### Phase Ordering Rationale

**Dependency-driven:** Phase 1 foundational, Phase 2 establishes patterns for Phase 3, Phase 4 enhances Phases 2-3, Phase 5 packages all.

**Risk mitigation:** Critical pitfalls in Phase 1-2 (model selection, hallucination), German-specific in Phase 3 (compound tokenization), production risks in Phase 4 (negation, calibration), deployment risks in Phase 5.

**Architecture validation:** Phase 2 proves plugin pattern, Phase 3 proves scalability, Phase 4 proves quality enhancement, Phase 5 proves containerization.

**Pitfall avoidance:** Model selection (Phase 1) prevents cascading failures, grounding (Phase 2) prevents hallucination accumulation, real data (Phase 4) catches issues before packaging (Phase 5).

### Research Flags

**Needs deeper research:**
- Phase 2: German date extraction prompting, temporal normalization
- Phase 3: German medication conventions, abbreviation handling
- Phase 4: German negation detection, confidence calibration

**Standard patterns:**
- Phase 1: llama-cpp-python and FastAPI setup
- Phase 5: Docker deployment

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Core technologies verified via Context7 and official docs |
| Features | HIGH | Table stakes from production systems, German requirements from GGPONC/BRONCO papers |
| Architecture | HIGH | Patterns from clinical NLP frameworks (medspaCy, GATE) and LLM extraction systems |
| Pitfalls | HIGH | From production reports, academic research, German NLP studies |

**Overall confidence:** HIGH

Research based on verified sources (Context7, official docs, academic papers, production guides). German clinical NLP is well-studied with established corpora. Local LLM deployment with GGUF is mature 2026 approach.

### Gaps to Address

**German prompting strategies:** No specific research for Llama 3.3 on German clinical text. **Resolution:** Validate on GGPONC during Phase 2-3, iterate based on quality.

**Llama 3.3 vs medBERT.de accuracy:** No benchmarks comparing multilingual vs German-specific models. **Resolution:** Track accuracy during development, consider hybrid if needed.

**GGPONC entity type coverage:** Annotations confirmed but exact taxonomy not detailed. **Resolution:** Load dataset in Phase 1, examine schema.

**Model memory for 70B Q4_K_M:** ~40GB indicated but not tested. **Resolution:** Test in Phase 1, fallback to 7B/8B if insufficient.

**Confidence score extraction:** Unclear if JSON schema mode provides per-entity scores. **Resolution:** Test in Phase 2, may need logprobs or ensemble-based confidence.

**German dependency parsing:** DEEPEN algorithm uses Stanford parser, unclear if German equivalent exists. **Resolution:** Phase 4 research, fallback to rule-based scope restriction if needed.

## Sources

### Primary (HIGH confidence)
- Context7 verified: llama-cpp-python, Pydantic v2, FastAPI 0.136.3, Outlines
- Llama 3.3 official model card — German language support confirmed
- GGPONC 2.0 on HuggingFace — Dataset availability verified
- FastAPI official documentation
- Pydantic official documentation

### Secondary (MEDIUM confidence)
- GGPONC corpus papers (arxiv.org/abs/2007.06400, aclanthology.org/2022.lrec-1.389/)
- GERNERMED++ (German medical NLP challenges)
- medBERT.de and BioGottBERT papers
- FastAPI deployment guide 2026
- GGUF quantization guide 2026
- DEEPEN negation detection system
- Medical hallucination in foundation models
- LLM uncertainty and calibration benchmarks
- Docker with llama.cpp production guide
- Clinical NLP modular pipeline architecture papers
- PARSE and DELM LLM extraction frameworks
- medspaCy clinical NLP toolkit

### Tertiary (LOW confidence - needs validation)
- German prompting strategies for clinical NLP
- Llama 3.3 vs medBERT.de accuracy comparison
- GGPONC entity taxonomy details
- llama-cpp-python confidence scores in JSON schema mode

---
*Research completed: 2026-06-11*  
*Ready for roadmap: yes*
