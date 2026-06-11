# Architecture Patterns: German Clinical NLP Extraction Pipeline

**Domain:** Clinical NLP Information Extraction
**Researched:** 2026-06-11
**Confidence:** HIGH

## Executive Summary

Clinical NLP extraction systems follow a modular pipeline architecture with clear component boundaries. For German clinical NLP with local LLM deployment, the recommended architecture consists of five core components: (1) API Layer for request/response handling, (2) Extraction Engine for LLM-based entity extraction, (3) Validation Layer for schema enforcement and hallucination mitigation, (4) Model Management for GGUF model loading and configuration, and (5) Data Layer for sample data and output formatting.

This architecture is based on established patterns from clinical NLP systems (medspaCy, GATE, UIMA frameworks), modern LLM-based extraction pipelines (PARSE, DELM frameworks), and production FastAPI service patterns. The modular design enables extensibility (easy addition of new entity types), clear separation of concerns, and straightforward build ordering.

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                             │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ POST /extract  │  │  GET /health   │  │ GET /models  │  │
│  └────────┬───────┘  └────────┬───────┘  └──────┬───────┘  │
│           │                   │                   │           │
└───────────┼───────────────────┼───────────────────┼──────────┘
            │                   │                   │
            ↓                   │                   ↓
┌───────────────────────────────┼─────────────────────────────┐
│         Extraction Engine     │    Model Management         │
│  ┌────────────────────────┐  │  ┌──────────────────────┐   │
│  │   Entity Extractors    │  │  │   Model Loader       │   │
│  │  ├─ DateExtractor      │  │  │  ├─ GGUF Loading     │   │
│  │  ├─ DiagnosisExtractor │  │  │  ├─ Config from ENV  │   │
│  │  ├─ LOSExtractor       │  │  │  └─ llama-cpp-python │   │
│  │  └─ MedicationExtractor│  │  └──────────────────────┘   │
│  └────────┬───────────────┘  │                              │
│           │                  │                              │
└───────────┼──────────────────┼──────────────────────────────┘
            │                  │
            ↓                  ↓
┌─────────────────────────────────────────────────────────────┐
│                    Validation Layer                          │
│  ┌─────────────────────┐  ┌─────────────────────────────┐  │
│  │  Pydantic Schemas   │  │  Custom Validators           │  │
│  │  ├─ DateEntity      │  │  ├─ Future date rejection    │  │
│  │  ├─ DiagnosisEntity │  │  ├─ Format validation        │  │
│  │  ├─ LOSEntity       │  │  ├─ Grounding verification   │  │
│  │  └─ MedicationEntity│  │  └─ Confidence thresholding  │  │
│  └─────────────────────┘  └─────────────────────────────┘  │
│                                                              │
└───────────────────────────────┬──────────────────────────────┘
                                │
                                ↓
┌─────────────────────────────────────────────────────────────┐
│                        Data Layer                            │
│  ┌──────────────────────┐  ┌──────────────────────────┐    │
│  │  Sample Clinical     │  │  Output Formatter         │    │
│  │  Notes (GGPONC/      │  │  └─ Validated JSON        │    │
│  │  BRONCO datasets)    │  │                           │    │
│  └──────────────────────┘  └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Component Boundaries

| Component | Responsibility | Inputs | Outputs | Communicates With |
|-----------|---------------|--------|---------|-------------------|
| **API Layer** | HTTP request handling, endpoint routing, error responses | HTTP requests (JSON) | HTTP responses (JSON) | Extraction Engine, Model Management |
| **Extraction Engine** | Entity-specific extraction logic, prompt engineering, LLM invocation | Clinical text, entity type | Raw extracted entities | Model Management, Validation Layer |
| **Validation Layer** | Schema enforcement, impossible value rejection, confidence scoring | Raw extracted entities | Validated entity objects or errors | Extraction Engine, Data Layer |
| **Model Management** | GGUF model loading, configuration, LLM lifecycle | ENV variables, model paths | Initialized LLM instance | Extraction Engine |
| **Data Layer** | Sample data provision, output formatting | Validated entities | Structured JSON responses | Validation Layer, API Layer |

### Component Details

#### 1. API Layer (FastAPI)

**Purpose:** Exposes REST endpoints for extraction requests and system health.

**Key responsibilities:**
- Request validation (Pydantic models for request bodies)
- Endpoint routing (`/extract`, `/health`, `/models`)
- Exception handling (HTTPException for client errors, custom handlers for domain errors)
- CORS configuration (for frontend access if needed)
- Automatic OpenAPI documentation generation

**Technology:** FastAPI with async support, automatic JSON serialization

**Configuration:** Minimal - port binding, CORS settings, logging level

**Error handling pattern:**
```python
# Custom exception handlers for domain errors
@app.exception_handler(ModelNotFoundError)
async def model_not_found_handler(request: Request, exc: ModelNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc), "error_type": "model_not_found"}
    )

# HTTPException for standard HTTP errors
raise HTTPException(status_code=400, detail="Invalid clinical text format")
```

#### 2. Extraction Engine

**Purpose:** Orchestrates entity extraction using specialized extractors for each entity type.

**Key responsibilities:**
- Entity-specific extraction logic (one extractor per entity type)
- Prompt engineering for German clinical text
- LLM invocation with JSON schema constraints
- Confidence score calculation
- Extraction orchestration (parallel or sequential extraction)

**Architecture pattern:** Strategy pattern with pluggable extractors

**Extractor interface:**
```python
class EntityExtractor(ABC):
    entity_type: str
    schema: dict  # JSON schema for structured output
    
    @abstractmethod
    async def extract(self, text: str, llm: Llama) -> list[dict]:
        """Extract entities from clinical text using LLM."""
        pass
    
    def get_prompt(self, text: str) -> str:
        """Generate extraction prompt for this entity type."""
        pass
```

**Concrete extractors:**
- `DateExtractor` - Extracts dates with temporal normalization
- `DiagnosisExtractor` - Identifies diagnoses using ICD-10/SNOMED patterns
- `LOSExtractor` - Finds length-of-stay indicators
- `MedicationExtractor` - Extracts medication mentions with dosages

**Extensibility:** Add new extractor by:
1. Subclass `EntityExtractor`
2. Define entity-specific JSON schema
3. Implement extraction prompt
4. Register in extraction orchestrator

#### 3. Validation Layer (Pydantic)

**Purpose:** Enforces schema constraints, rejects impossible values, mitigates hallucinations.

**Key responsibilities:**
- Type validation (string, int, date formats)
- Domain rule enforcement (no future dates, valid ICD codes)
- Confidence threshold filtering
- Grounding verification (extracted value exists in input text)
- Structured error messages

**Validation architecture (three-stage):**
1. **Schema validation** - Pydantic type checking and required field enforcement
2. **Domain validation** - Custom validators for medical domain rules
3. **Grounding verification** - Post-validation check that extracted text appears in source

**Example Pydantic model:**
```python
from pydantic import BaseModel, field_validator, ValidationInfo
from datetime import date

class DateEntity(BaseModel):
    value: date
    text: str  # Original text span
    confidence: float
    context: str | None = None
    
    @field_validator('value', mode='after')
    @classmethod
    def reject_future_dates(cls, v: date) -> date:
        if v > date.today():
            raise ValueError(f'Future date not allowed in clinical records: {v}')
        return v
    
    @field_validator('confidence', mode='after')
    @classmethod
    def check_confidence_threshold(cls, v: float) -> float:
        if v < 0.6:
            raise ValueError(f'Confidence too low: {v}')
        return v
```

**Hallucination mitigation strategies:**
1. **Confidence filtering** - Reject extractions below threshold
2. **Grounding check** - Verify extracted text span exists in input
3. **Format validation** - Reject malformed values (invalid dates, non-numeric LOS)
4. **Domain constraints** - Enforce medical knowledge (valid ICD codes, drug names)

**Note on limitations:** Confidence scores from LLMs can be unreliable (high confidence on incorrect answers is common). Grounding verification is the strongest mitigation.

#### 4. Model Management

**Purpose:** Loads and configures GGUF models via llama-cpp-python.

**Key responsibilities:**
- Model loading from local files or download
- Configuration from environment variables
- LLM instance lifecycle (singleton or pooled)
- JSON schema enforcement at model level
- GPU/CPU selection

**Configuration via ENV:**
```bash
MODEL_PATH=/path/to/model.gguf
MODEL_TYPE=llama  # or mistral, etc.
N_GPU_LAYERS=35   # GPU offloading
N_CTX=2048        # Context window
TEMPERATURE=0.3   # Low for consistent extraction
```

**LLM invocation with structured output:**
```python
from llama_cpp import Llama

llm = Llama(
    model_path=model_path,
    n_gpu_layers=n_gpu_layers,
    n_ctx=n_ctx,
)

response = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "Extract dates from German clinical text."},
        {"role": "user", "content": clinical_text}
    ],
    response_format={
        "type": "json_object",
        "schema": {
            "type": "object",
            "properties": {
                "dates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "string"},
                            "text": {"type": "string"},
                            "confidence": {"type": "number"}
                        },
                        "required": ["value", "text", "confidence"]
                    }
                }
            },
            "required": ["dates"]
        }
    },
    temperature=0.3
)
```

**Model selection criteria:**
- German language support (essential)
- Instruction-following capability (chat-tuned models preferred)
- JSON mode support (most modern LLMs)
- Size vs. performance tradeoff (7B-13B models for local deployment)

#### 5. Data Layer

**Purpose:** Provides sample clinical notes and formats validated output.

**Key responsibilities:**
- Load sample data from GGPONC/BRONCO datasets
- Format validated entities as JSON responses
- Include metadata (model version, extraction timestamp, confidence stats)

**Sample data structure:**
```json
{
  "note_id": "ggponc_001",
  "text": "Patient wurde am 15.03.2024 mit Verdacht auf Pneumonie aufgenommen...",
  "source": "GGPONC",
  "language": "de"
}
```

**Output format:**
```json
{
  "note_id": "ggponc_001",
  "extracted_entities": {
    "dates": [
      {
        "value": "2024-03-15",
        "text": "15.03.2024",
        "confidence": 0.95,
        "context": "Patient wurde am 15.03.2024 mit Verdacht"
      }
    ],
    "diagnoses": [
      {
        "value": "Pneumonie",
        "text": "Pneumonie",
        "confidence": 0.88,
        "code": "J18.9"
      }
    ]
  },
  "metadata": {
    "model": "llama-2-7b-german-medical",
    "extraction_timestamp": "2024-03-20T10:15:30Z",
    "average_confidence": 0.915
  }
}
```

## Data Flow

### Extraction Request Flow

```
1. Client → API Layer: POST /extract with clinical text
   ↓
2. API Layer → Extraction Engine: Route to extraction orchestrator
   ↓
3. Extraction Engine → Model Management: Get LLM instance
   ↓
4. Extraction Engine: Execute extractors (parallel or sequential)
   - DateExtractor → LLM (with date schema)
   - DiagnosisExtractor → LLM (with diagnosis schema)
   - LOSExtractor → LLM (with LOS schema)
   - MedicationExtractor → LLM (with medication schema)
   ↓
5. Extraction Engine → Validation Layer: Pass raw extractions
   ↓
6. Validation Layer: 
   - Pydantic schema validation
   - Custom domain validators
   - Grounding verification
   ↓
7. Validation Layer → Data Layer: Format validated entities
   ↓
8. Data Layer → API Layer: Return structured JSON
   ↓
9. API Layer → Client: HTTP 200 with extraction results
```

### Error Flow

```
Validation Error:
  Validation Layer → API Layer: ValidationError
  API Layer → Client: HTTP 422 with error details

Model Error:
  Model Management → Extraction Engine: ModelLoadError
  Extraction Engine → API Layer: HTTPException(500)
  API Layer → Client: HTTP 500 with error message

Low Confidence:
  Validation Layer: Filter or flag low-confidence entities
  Option A: Exclude from response
  Option B: Include with warning flag
```

## Patterns to Follow

### Pattern 1: Extractor Plugin Pattern

**What:** Each entity type is a self-contained extractor with its own schema, prompt, and validation logic.

**When:** Adding new entity types (e.g., procedures, labs, vitals)

**Benefits:**
- Isolated changes (new extractor doesn't affect existing ones)
- Parallel development (team can work on extractors independently)
- Testable in isolation
- Clear ownership boundaries

**Example:**
```python
# Step 1: Define schema
procedure_schema = {
    "type": "object",
    "properties": {
        "procedures": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "date": {"type": "string"},
                    "confidence": {"type": "number"}
                },
                "required": ["name", "confidence"]
            }
        }
    }
}

# Step 2: Implement extractor
class ProcedureExtractor(EntityExtractor):
    entity_type = "procedure"
    schema = procedure_schema
    
    async def extract(self, text: str, llm: Llama) -> list[dict]:
        prompt = self.get_prompt(text)
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": "Extract medical procedures."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object", "schema": self.schema}
        )
        return response['choices'][0]['message']['content']

# Step 3: Register in orchestrator
extractor_registry = {
    "date": DateExtractor(),
    "diagnosis": DiagnosisExtractor(),
    "procedure": ProcedureExtractor(),  # New extractor
}
```

### Pattern 2: Three-Stage Validation Pipeline

**What:** Validation happens in three distinct stages: schema → domain → grounding.

**When:** Processing all extractions

**Benefits:**
- Clear failure points (know which validation stage failed)
- Incremental validation (fast schema check before expensive grounding)
- Composable validators (add domain rules without touching schema)

**Example:**
```python
# Stage 1: Schema validation (Pydantic automatic)
entity = DateEntity.model_validate(raw_extraction)  # Raises if invalid

# Stage 2: Domain validation (Pydantic custom validators)
# @field_validator automatically runs during model_validate

# Stage 3: Grounding verification (post-validation)
def verify_grounding(entity: DateEntity, source_text: str) -> bool:
    return entity.text in source_text

if not verify_grounding(entity, clinical_note):
    raise ValueError(f"Extracted text '{entity.text}' not found in source")
```

### Pattern 3: Environment-Based Model Configuration

**What:** All model configuration via environment variables, no hardcoded paths.

**When:** Model loading, deployment, testing

**Benefits:**
- Docker-friendly (override via docker-compose)
- Easy testing (swap models without code changes)
- Deployment flexibility (different models per environment)

**Example:**
```python
import os
from pathlib import Path

class ModelConfig:
    model_path: Path = Path(os.getenv("MODEL_PATH", "models/default.gguf"))
    n_gpu_layers: int = int(os.getenv("N_GPU_LAYERS", "0"))
    n_ctx: int = int(os.getenv("N_CTX", "2048"))
    temperature: float = float(os.getenv("TEMPERATURE", "0.3"))
    
    def validate(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
```

### Pattern 4: Structured Output at Model Level

**What:** Enforce JSON schema in LLM call, not post-processing.

**When:** All entity extractions

**Benefits:**
- Guaranteed valid JSON (no parsing errors)
- Reduced hallucination (constrained generation)
- Clear contract (schema is documentation)

**Example:**
```python
# Good: Schema-constrained generation
response = llm.create_chat_completion(
    messages=messages,
    response_format={"type": "json_object", "schema": entity_schema}
)
# LLM cannot generate invalid JSON

# Bad: Parse freeform output
response = llm.create_chat_completion(messages=messages)
json.loads(response)  # May fail, no schema enforcement
```

### Pattern 5: Async-First API Design

**What:** Use async/await for all I/O operations (LLM calls, file access).

**When:** Implementing FastAPI endpoints and extractors

**Benefits:**
- Better concurrency (handle multiple requests)
- Non-blocking LLM calls (important for slow inference)
- Scalable under load

**Example:**
```python
from fastapi import FastAPI
from typing import List

app = FastAPI()

@app.post("/extract")
async def extract_entities(request: ExtractionRequest) -> ExtractionResponse:
    # Async LLM calls allow handling other requests while waiting
    entities = await extraction_engine.extract_all(request.text)
    return ExtractionResponse(entities=entities)
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Monolithic Extractor

**What:** Single function that extracts all entity types in one pass.

**Why bad:**
- Brittle (one entity type breaks all extractions)
- Hard to test (cannot isolate entity type failures)
- Poor extensibility (adding entity type requires modifying core logic)
- Large prompts (trying to extract everything reduces quality)

**Instead:** Use extractor plugin pattern (one extractor per entity type).

### Anti-Pattern 2: Post-Hoc JSON Parsing

**What:** Let LLM generate freeform text, then parse with regex/heuristics.

**Why bad:**
- Parsing failures (malformed JSON, unexpected formats)
- Increased hallucination (no schema constraint)
- Fragile (LLM output variation breaks parser)

**Instead:** Use structured output with JSON schema at model level.

### Anti-Pattern 3: Validation in API Layer

**What:** Put domain validation logic (date checks, format validation) in FastAPI endpoints.

**Why bad:**
- Not reusable (validation tied to API)
- Hard to test (need to spin up API to test validation)
- Violates separation of concerns (API layer should route, not validate domain rules)

**Instead:** Use Pydantic models with custom validators in validation layer.

### Anti-Pattern 4: Confidence Score as Sole Quality Gate

**What:** Rely only on LLM confidence scores to filter hallucinations.

**Why bad:**
- Unreliable (LLMs can be very confident about wrong answers)
- No grounding (high confidence doesn't mean text is in source)
- Threshold tuning difficult (optimal threshold varies by entity type)

**Instead:** Combine confidence with grounding verification and domain constraints.

### Anti-Pattern 5: Hardcoded Model Paths

**What:** Hardcode model file paths in code.

**Why bad:**
- Deployment brittleness (paths differ between dev/prod)
- Testing difficulty (cannot easily swap test models)
- Docker unfriendly (paths may not exist in container)

**Instead:** Use environment variables for all configuration.

### Anti-Pattern 6: Synchronous LLM Calls

**What:** Use synchronous (blocking) calls to LLM in FastAPI endpoints.

**Why bad:**
- Blocks event loop (single slow request blocks all requests)
- Poor scalability (cannot handle concurrent requests)
- Timeout issues (long LLM inference blocks FastAPI)

**Instead:** Use async/await for all LLM calls.

## Build Order and Dependencies

### Phase 1: Foundation (No Dependencies)
**Goal:** Minimal working infrastructure

1. **Model Management Component**
   - Implement model loading from environment config
   - Test with simple LLM call (no extraction yet)
   - Validate JSON schema enforcement works
   - **Success criteria:** Can load GGUF model and get structured JSON response

2. **Data Layer - Sample Data**
   - Load GGPONC/BRONCO sample notes
   - Create data access interface
   - **Success criteria:** Can retrieve sample clinical notes

3. **API Layer - Basic Scaffold**
   - Set up FastAPI application
   - Implement `/health` endpoint
   - Implement `/models` endpoint (list loaded models)
   - **Success criteria:** API starts, health check returns 200

### Phase 2: Single Entity Extraction (Depends on Phase 1)
**Goal:** End-to-end extraction for simplest entity type

4. **Validation Layer - Date Entity**
   - Define `DateEntity` Pydantic model
   - Implement date format validators
   - Implement future date rejection
   - **Success criteria:** Can validate date entities, reject invalid dates

5. **Extraction Engine - Date Extractor**
   - Implement `DateExtractor` class
   - Create German date extraction prompt
   - Define date extraction JSON schema
   - **Success criteria:** Can extract dates from sample notes

6. **API Layer - Extraction Endpoint**
   - Implement POST `/extract` endpoint
   - Wire up date extraction
   - Return validated JSON
   - **Success criteria:** End-to-end date extraction via API

### Phase 3: Multi-Entity Extraction (Depends on Phase 2)
**Goal:** Prove extensibility, add remaining entity types

7. **Validation Layer - Remaining Entities**
   - Define `DiagnosisEntity`, `LOSEntity`, `MedicationEntity`
   - Implement entity-specific validators
   - **Success criteria:** All entity models defined with validation

8. **Extraction Engine - Remaining Extractors**
   - Implement `DiagnosisExtractor`
   - Implement `LOSExtractor`
   - Implement `MedicationExtractor`
   - Create extraction orchestrator (run all extractors)
   - **Success criteria:** Can extract all entity types in parallel

9. **Data Layer - Output Formatting**
   - Implement multi-entity JSON response formatter
   - Add metadata (model version, timestamp, confidence stats)
   - **Success criteria:** Clean JSON output with all entities

### Phase 4: Robustness (Depends on Phase 3)
**Goal:** Error handling, hallucination mitigation

10. **Validation Layer - Grounding Verification**
    - Implement grounding check (text span in source)
    - Add confidence thresholding
    - **Success criteria:** Can reject ungrounded extractions

11. **API Layer - Error Handling**
    - Implement custom exception handlers
    - Add validation error formatting
    - Handle model loading failures
    - **Success criteria:** Clean error responses for all failure modes

12. **Extraction Engine - Confidence Scoring**
    - Implement confidence calculation (if not from model)
    - Add confidence to all extractors
    - **Success criteria:** All entities include confidence scores

### Phase 5: Deployment (Depends on Phase 4)
**Goal:** Containerized local deployment

13. **Docker Configuration**
    - Create Dockerfile (Python, llama-cpp-python, model download)
    - Create docker-compose.yml (API service, volume for models)
    - Document environment variables
    - **Success criteria:** `docker-compose up` starts API

14. **Documentation**
    - README with setup instructions
    - API usage examples (curl commands)
    - Example extraction output (JSON samples)
    - **Success criteria:** Recruiter can run demo without assistance

## Dependency Graph

```
Phase 1 (Foundation)
├─ Model Management
├─ Data Layer - Sample Data
└─ API Layer - Basic Scaffold

Phase 2 (Single Entity)
├─ Validation Layer - Date Entity (depends on: nothing)
├─ Extraction Engine - Date Extractor (depends on: Model Management, Validation - Date)
└─ API Layer - Extraction Endpoint (depends on: Extraction Engine - Date, API Scaffold)

Phase 3 (Multi-Entity)
├─ Validation Layer - Remaining Entities (depends on: Validation - Date)
├─ Extraction Engine - Remaining Extractors (depends on: Extraction Engine - Date)
└─ Data Layer - Output Formatting (depends on: Validation - Remaining)

Phase 4 (Robustness)
├─ Validation Layer - Grounding (depends on: Validation - Remaining)
├─ API Layer - Error Handling (depends on: API - Extraction Endpoint)
└─ Extraction Engine - Confidence (depends on: Extraction Engine - Remaining)

Phase 5 (Deployment)
├─ Docker Configuration (depends on: all previous)
└─ Documentation (depends on: Docker)
```

## Scalability Considerations

| Concern | At 10 req/hour (Portfolio Demo) | At 100 req/hour (Small Clinic) | At 10K req/hour (Hospital) |
|---------|--------------------------------|--------------------------------|---------------------------|
| **LLM Instance** | Single model, CPU-only acceptable | Single model with GPU layers | Model pool with load balancing |
| **Concurrency** | FastAPI async sufficient | FastAPI with worker processes (Gunicorn) | Kubernetes pods with horizontal scaling |
| **Model Loading** | Load on startup | Load on startup, health checks for readiness | Model caching, blue-green model updates |
| **Storage** | In-memory responses only | Consider response caching (Redis) | Database for extractions, audit trail |
| **Error Handling** | Log to stdout | Structured logging (JSON), log aggregation | Distributed tracing (OpenTelemetry), error alerting |
| **Validation** | Synchronous validation acceptable | Async validation for faster response | Batch validation, circuit breakers for external checks |

**Portfolio scope:** Focus on "10 req/hour" column. Architecture supports scaling, but implementation is for demo/small-scale.

## German Clinical NLP Specific Considerations

### Language-Specific Architecture Decisions

1. **Model Selection Impact**
   - German-specific models preferred (better performance on medical terminology)
   - If multilingual model used, German prompt engineering critical
   - Medical domain: General German models may struggle with abbreviations (z.B., "OP" for Operation, "HWS" for Halswirbelsäule)

2. **Dataset-Specific Patterns**
   - GGPONC: Guideline text (formal, standardized) → easier extraction
   - BRONCO: Discharge letters (clinical notes, abbreviations, freeform) → harder extraction
   - Architecture must handle both formal and informal German clinical text

3. **Entity Type Considerations**
   - German dates: Multiple formats (15.03.2024, 15. März 2024, 15.3.24)
   - ICD-10-GM: German modification of ICD-10 (not identical to US ICD-10-CM)
   - Medications: German drug names (Paracetamol vs. Acetaminophen)

### Integration with GGPONC/BRONCO Datasets

**GGPONC annotations provide ground truth:**
- Entity types: Findings (Diagnosis, Other Finding), Substances (Clinical Drug, Nutrients, External), Procedures (Therapeutic, Diagnostic)
- Use GGPONC annotations for validation testing (compare extractions to gold standard)
- Architecture should support adding entity specifications (nested structure in GGPONC)

**Data flow for sample notes:**
```
GGPONC/BRONCO JSON → Data Layer → Sample note loader → API /extract endpoint
```

**Evaluation architecture (future):**
```
Gold annotations → Evaluation module ← Extraction output
                         ↓
                    Metrics (F1, precision, recall)
```

## Alternative Architectures Considered

| Architecture | Pros | Cons | Decision |
|-------------|------|------|----------|
| **spaCy/medspaCy pipeline** | Mature framework, component model, clinical patterns | English-focused, German support limited, rule-based not LLM | Not recommended - project requires LLM showcase |
| **UIMA framework** | Used in German clinical NLP research, modular | Complex setup, Java-based, overkill for portfolio | Not recommended - too heavyweight |
| **Single-pass extraction** | Simpler, one LLM call for all entities | Large prompts reduce quality, not extensible, harder to test | Not recommended - violates extensibility requirement |
| **Instructor library integration** | Easy Pydantic integration, automatic retries | Adds dependency, abstracts schema enforcement | Possible enhancement - document but defer |
| **Separate services per entity** | Ultimate isolation, independent scaling | Overkill for portfolio, deployment complexity | Not recommended - over-engineered for scope |

## Sources

### Clinical NLP Architecture
- [Deep learning-based NLP data pipeline for EHR-scanned document information extraction](https://academic.oup.com/jamiaopen/article/5/2/ooac045/6605916)
- [System Architecture for Temporal Information Extraction, Representation and Reasoning in Clinical Narrative Reports](https://pmc.ncbi.nlm.nih.gov/articles/PMC1560711/)
- [Natural Language Processing in Biomedicine: A Unified System Architecture Overview](https://arxiv.org/pdf/1401.0569)
- [A Lightweight API-Based Approach for Building Flexible Clinical NLP Systems](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6714318/)
- [Launching into clinical space with medspaCy: a new clinical text processing toolkit in Python](https://pmc.ncbi.nlm.nih.gov/articles/PMC8861690/)

### LLM Structured Output and Validation
- [Structured outputs with llama-cpp-python, a complete guide w/ instructor](https://python.useinstructor.com/integrations/llama-cpp-python/)
- [PARSE: LLM Driven Schema Optimization for Reliable Entity Extraction](https://arxiv.org/pdf/2510.08623)
- [DELM: a Python toolkit for Data Extraction with Language Models](https://arxiv.org/pdf/2509.20617)
- [llama-cpp-python GitHub](https://github.com/abetlen/llama-cpp-python) (HIGH confidence - official docs)
- [Pydantic GitHub](https://github.com/pydantic/pydantic) (HIGH confidence - official docs)

### FastAPI Architecture and Error Handling
- [Building Production-Ready FastAPI Applications with Service Layer Architecture](https://medium.com/@abhinav.dobhal/building-production-ready-fastapi-applications-with-service-layer-architecture-in-2025-f3af8a6ac563)
- [FastAPI Error Handling Patterns](https://betterstack.com/community/guides/scaling-python/error-handling-fastapi/)
- [FastAPI Official Documentation](https://fastapi.tiangolo.com/) (HIGH confidence - official docs)

### Hallucination Detection and Confidence Scoring
- [Medical Feature Extraction From Clinical Examination Notes: Development and Evaluation of a Two-Phase Large Language Model Framework](https://pmc.ncbi.nlm.nih.gov/articles/PMC12712565/)
- [Avoiding LLM hallucinations and building LLM confidence scores](https://nanonets.com/blog/how-to-tell-if-your-llm-is-hallucinating/)
- [Hallucination Detection: NLI, Self-Consistency & Learned Models](https://mbrenndoerfer.com/writing/hallucination-detection)

### Extensible Pipeline Patterns
- [Building Custom NLP Pipelines and Extending SpaCy's Functionality](https://www.statology.org/building-custom-nlp-pipelines-extending-spacy-functionality/)
- [Introducing custom pipelines and extensions for spaCy v2.0](https://explosion.ai/blog/spacy-v2-pipelines-extensions)

### Docker and Deployment
- [Deploying a NLP model with Docker and FastAPI](https://medium.com/analytics-vidhya/deploying-a-nlp-model-with-docker-and-fastapi-d972779d8008)
- [Docker Practices for Large Language Model Deployment](https://dzone.com/articles/llmops-docker-practices-llm-deployment)
- [End-to-End NLP Project with Hugging Face, FastAPI, and Docker](https://medium.com/data-science/end-to-end-nlp-project-with-hugging-face-fastapi-and-docker-615a63d80c53)

### German Clinical NLP Datasets
- [GGPONC 2.0 - The German Clinical Guideline Corpus for Oncology](https://aclanthology.org/2022.lrec-1.389/)
- [Comprehensive Study on German Language Models for Clinical and Biomedical Text Understanding](https://arxiv.org/html/2404.05694v1)
- [bigbio/ggponc2 on Hugging Face](https://huggingface.co/datasets/bigbio/ggponc2)

---

**Confidence Assessment:**
- Component boundaries: HIGH (based on established clinical NLP patterns and official FastAPI/Pydantic docs)
- Data flow: HIGH (verified with llama-cpp-python and FastAPI official documentation)
- Build order: MEDIUM (logical dependency structure, but actual implementation may reveal adjustments needed)
- German-specific considerations: MEDIUM (verified with GGPONC research, but specific model performance will vary)
- Scalability: MEDIUM (architectural patterns are sound, but portfolio scope limits validation at scale)
