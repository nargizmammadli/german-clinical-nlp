# Requirements: German Clinical NLP Pipeline

**Defined:** 2026-06-11
**Core Value:** Demonstrates production-ready clinical NLP with local LLM deployment, structured output validation, and explicit hallucination handling — all with German medical text.

## v1 Requirements

Requirements for initial portfolio-ready release. Each maps to roadmap phases.

### Entity Extraction

- [x] **ENTITY-01**: System extracts dates from German clinical text with confidence scores
- [x] **ENTITY-02**: System extracts diagnoses from German clinical text with confidence scores
- [x] **ENTITY-03**: System extracts medications from German clinical text with confidence scores
- [x] **ENTITY-04**: System extracts length-of-stay indicators from German clinical text with confidence scores
- [x] **ENTITY-05**: Each extracted entity includes source text span (evidence grounding)
- [x] **ENTITY-06**: Extraction output is validated JSON conforming to Pydantic schemas

### Model & Inference

- [x] **MODEL-01**: System uses llama-cpp-python to load GGUF models
- [x] **MODEL-02**: Model selection is configurable via environment variables
- [x] **MODEL-03**: System works with local GGUF models (no cloud API dependencies)
- [x] **MODEL-04**: System handles context window appropriately (8K+ tokens or chunking)

### API Endpoints

- [x] **API-01**: POST /extract endpoint accepts German clinical text and returns extracted entities
- [x] **API-02**: GET /health endpoint returns service health status
- [x] **API-03**: GET /models endpoint returns active model metadata
- [x] **API-04**: API provides meaningful error responses for invalid requests
- [x] **API-05**: API automatically generates OpenAPI documentation

### Validation

- [x] **VAL-01**: Pydantic schema validation enforces entity structure
- [x] **VAL-02**: Domain validators reject impossible values (future dates, invalid formats)
- [x] **VAL-03**: Confidence scores included for each extracted entity

### Data & Samples

- [x] **DATA-01**: Project includes sample German clinical text from GGPONC or BRONCO datasets
- [x] **DATA-02**: Sample data demonstrates extraction across all entity types
- [x] **DATA-03**: Sample data is freely distributable (no patient data)

### Deployment

- [x] **DEPLOY-01**: Dockerfile enables local development deployment
- [x] **DEPLOY-02**: docker-compose.yml provides one-command working demo
- [x] **DEPLOY-03**: Docker configuration includes explicit memory limits
- [x] **DEPLOY-04**: Container includes health checks

### Documentation

- [ ] **DOC-01**: README includes setup instructions
- [ ] **DOC-02**: README includes API usage examples with curl/Python
- [ ] **DOC-03**: README includes example extraction output (JSON samples)
- [ ] **DOC-04**: Architecture documentation explains component design and extensibility

### Extensibility

- [x] **EXT-01**: Entity extraction follows plugin pattern (easy to add new entity types)
- [x] **EXT-02**: Documentation demonstrates how to add a new entity type

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Clinical Features

- **CLIN-01**: Assertion status detection (confirmed vs negated vs hypothetical findings)
- **CLIN-02**: German medical abbreviation expansion
- **CLIN-03**: Temporal relation extraction (links entities to time)
- **CLIN-04**: Entity normalization to ICD-10-GM/ATC/OPS codes

### Quality Enhancements

- **QUAL-01**: Confidence score calibration on validation set
- **QUAL-02**: Grounding verification with fuzzy matching
- **QUAL-03**: Enhanced negation scope detection with dependency parsing
- **QUAL-04**: Comprehensive automated test suite

### Production Features

- **PROD-01**: Cloud deployment configuration (AWS/GCP/Azure)
- **PROD-02**: Database persistence for extraction results
- **PROD-03**: Structured logging with JSON output (loguru)
- **PROD-04**: Async request handling throughout pipeline
- **PROD-05**: Rate limiting and request queuing

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Web UI | Portfolio targets technical audience; API-first approach demonstrates backend focus |
| Real patient data | GDPR compliance risk; synthetic/public datasets sufficient |
| Production cloud deployment | Adds complexity without demonstrating core NLP skills; local Docker sufficient |
| Comprehensive test coverage | Time-intensive; example output demonstrates correctness |
| Multiple language support | German-only focus demonstrates domain depth |
| Real-time streaming | Batch processing sufficient for portfolio demo |
| Entity relationship extraction | High complexity; defer to v2+ |
| Custom model fine-tuning | Pre-trained models sufficient; focus on engineering not ML research |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENTITY-01 | Phase 2 | Complete |
| ENTITY-02 | Phase 2 | Complete |
| ENTITY-03 | Phase 2 | Complete |
| ENTITY-04 | Phase 2 | Complete |
| ENTITY-05 | Phase 2 | Complete |
| ENTITY-06 | Phase 2 | Complete |
| MODEL-01 | Phase 1 | Complete |
| MODEL-02 | Phase 1 | Complete |
| MODEL-03 | Phase 1 | Complete |
| MODEL-04 | Phase 1 | Complete |
| API-01 | Phase 2 | Complete |
| API-02 | Phase 1 | Complete |
| API-03 | Phase 1 | Complete |
| API-04 | Phase 2 | Complete |
| API-05 | Phase 1 | Complete |
| VAL-01 | Phase 2 | Complete |
| VAL-02 | Phase 2 | Complete |
| VAL-03 | Phase 2 | Complete |
| DATA-01 | Phase 1 | Complete |
| DATA-02 | Phase 1 | Complete |
| DATA-03 | Phase 1 | Complete |
| DEPLOY-01 | Phase 3 | Pending |
| DEPLOY-02 | Phase 3 | Pending |
| DEPLOY-03 | Phase 3 | Pending |
| DEPLOY-04 | Phase 3 | Pending |
| DOC-01 | Phase 3 | Pending |
| DOC-02 | Phase 3 | Pending |
| DOC-03 | Phase 3 | Pending |
| DOC-04 | Phase 3 | Pending |
| EXT-01 | Phase 2 | Complete |
| EXT-02 | Phase 2 | Complete |

**Coverage:**

- v1 requirements: 29 total
- Mapped to phases: 29/29 ✓
- Unmapped: 0

---
*Requirements defined: 2026-06-11*
*Last updated: 2026-06-11 after roadmap creation*
