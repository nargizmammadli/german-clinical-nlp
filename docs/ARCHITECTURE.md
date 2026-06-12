# Entity Extraction Architecture

## Overview

The German Clinical NLP pipeline uses a plugin-based architecture for entity extraction. This design allows developers to easily add new entity types without modifying core pipeline code. The architecture is built on three key components:

1. **BaseExtractor** — Abstract base class defining the extraction interface
2. **Extractor Registry** — Module-level registry for extractor discovery
3. **@register_extractor Decorator** — Automatic registration pattern

## Request Flow

When a POST /extract request arrives, the pipeline runs all registered extractors in parallel using `asyncio.gather`, merges results, and returns a validated `EntityResponse`.

```ascii
POST /extract
     |
     v
src/api/extract.py
(ExtractRequest validated by Pydantic)
     |
     v
asyncio.gather([                     <- parallel execution per D-17
    asyncio.to_thread(TemporalExtractor.extract, text),
    asyncio.to_thread(ClinicalExtractor.extract, text)
], return_exceptions=True)           <- partial results per D-19
     |
     v
Merge results (list.extend)          <- per D-18
Domain validation (validate_date_not_future)
Confidence filtering                 <- per D-20, CONFIDENCE_THRESHOLD env var
     |
     v
EntityResponse (Pydantic validation)
{
  "temporal_entities": [...],        <- Dates and LOS indicators
  "clinical_entities": [...],        <- Diagnoses and medications
  "errors": [...],                   <- Validation and extraction errors
  "low_confidence": [...]            <- Entities below threshold
}
     |
     v
JSON response to client
```

### Parallel Extraction

The extraction pipeline uses three asyncio patterns to achieve safe parallel execution with synchronous llama-cpp-python calls:

- **`asyncio.to_thread`** wraps each synchronous `Llama.create_chat_completion()` call (per D-17) so it runs in a thread pool, preventing it from blocking the FastAPI event loop. Without this, the second extractor would wait for the first to complete.
- **`return_exceptions=True`** in `asyncio.gather` ensures that if one extractor raises an exception, the other extractor's results are still returned — the error is captured in the `errors` array and processing continues (per D-19).
- **`list.extend()`** merges entity arrays from all extractor results into a single combined result (per D-18). Each extractor returns the full four-key dictionary; `temporal_entities` from all extractors are merged, as are `clinical_entities` and `errors`.

See `src/api/extract.py` for the full implementation.

## Plugin Pattern

### BaseExtractor Abstract Class

All extractors inherit from `BaseExtractor` (defined in `src/extraction/base.py`):

```python
from abc import ABC, abstractmethod

class BaseExtractor(ABC):
    def __init__(self, model):
        """Model injected via constructor (dependency injection)."""
        self.model = model

    @abstractmethod
    def extract(self, text: str) -> dict:
        """
        Extract entities from input text.
        
        Returns:
            Dictionary with temporal_entities, clinical_entities, errors, low_confidence arrays
        """
        pass
```

### Extractor Registry

The registry is a module-level dictionary that maps extractor names to classes:

```python
# Module-level registry in src/extraction/base.py
extractor_registry: Dict[str, Type[BaseExtractor]] = {}
```

Extractors are automatically added to this registry via the `@register_extractor` decorator.

### @register_extractor Decorator

The decorator registers extractors by name:

```python
@register_extractor("temporal")
class TemporalExtractor(BaseExtractor):
    ...
```

This pattern ensures:
- **No manual registration** — Just import the extractor module
- **Name-based lookup** — Retrieve extractors by string key
- **Dependency injection** — Model passed to constructor at runtime

## Adding a New Entity Type

Follow these steps to add a new extractor (e.g., for symptoms or procedures):

### 1. Create Extractor Module

Create `src/extraction/your_entity.py`:

```python
from src.extraction.base import BaseExtractor, register_extractor
```

### 2. Import Required Components

```python
from src.prompts.your_entity_prompt import YOUR_ENTITY_EXTRACTION_PROMPT
from src.schemas.entities import YourEntity, SourceSpan
from pydantic import ValidationError
import json
```

### 3. Define Extractor Class

```python
@register_extractor("your_entity")
class YourEntityExtractor(BaseExtractor):
    """
    Extractor for your custom entity type.
    """
    
    def extract(self, text: str) -> dict:
        # Implementation here (see existing extractors for pattern)
        pass
```

### 4. Decorate with @register_extractor

Use a unique name for your extractor:

```python
@register_extractor("symptom")  # Unique registry key
class SymptomExtractor(BaseExtractor):
    ...
```

### 5. Implement extract() Method

Return dictionary with standard structure:

```python
def extract(self, text: str) -> dict:
    result = {
        "temporal_entities": [],
        "clinical_entities": [],  # Or add new array type
        "errors": [],
        "low_confidence": []
    }
    
    # Call LLM, validate entities, populate result
    return result
```

### 6. Import in Endpoint

Add import to `src/api/extract.py`:

```python
from src.extraction import your_entity  # noqa: F401
```

### 7. Add to Parallel Execution

Update `extract_entities` function in `src/api/extract.py`:

```python
your_entity_extractor_cls = extractor_registry.get("your_entity")
if your_entity_extractor_cls is not None:
    your_entity_extractor = your_entity_extractor_cls(request.app.state.model)
    extractors.append(("your_entity", your_entity_extractor))
```

The extractor will automatically run in parallel with existing extractors via `asyncio.gather`.

## Example: Adding Symptom Extraction

Here's a complete example for adding symptom extraction:

### Step 1: Create Prompt

Create `src/prompts/symptom_prompt.py`:

```python
SYMPTOM_EXTRACTION_PROMPT = """You are a German clinical NLP system. Extract symptom entities from German clinical text. Return JSON only.

**Entity Types:**
- **Symptom**: Patient-reported or observed symptoms (e.g., "Kopfschmerzen", "Fieber", "Übelkeit")

**Common German Medical Terms:**
- Symptom / Beschwerde: symptom / complaint
- Pat. klagt über: patient complains of
- berichtet: reports

**JSON Schema:**
Return JSON with a "symptom_entities" array. Each entity must include:
- type: "Symptom"
- text: The exact symptom text
- confidence: Float between 0.0 and 1.0
- source_span: Object with start, end, text fields

**Few-Shot Examples:**
[Include 2-3 German clinical examples with symptoms]
"""
```

### Step 2: Create Extractor

Create `src/extraction/symptom.py`:

```python
"""
Symptom entity extractor for German clinical text.
"""

import json
from src.extraction.base import BaseExtractor, register_extractor
from src.prompts.symptom_prompt import SYMPTOM_EXTRACTION_PROMPT
from src.schemas.entities import SourceSpan
from pydantic import BaseModel, Field, ValidationError


class SymptomEntity(BaseModel):
    """Symptom entity schema."""
    type: str = Field(default="Symptom")
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_span: SourceSpan
    source_span_validated: bool = False


@register_extractor("symptom")
class SymptomExtractor(BaseExtractor):
    """
    Extractor for symptom entities.
    """

    def extract(self, text: str) -> dict:
        result = {
            "temporal_entities": [],
            "clinical_entities": [],
            "symptom_entities": [],  # New entity type
            "errors": [],
            "low_confidence": []
        }

        try:
            response = self.model.create_chat_completion(
                messages=[
                    {"role": "system", "content": SYMPTOM_EXTRACTION_PROMPT},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2048
            )

            content = response["choices"][0]["message"]["content"]
            llm_output = json.loads(content)

            if "symptom_entities" in llm_output:
                for entity_data in llm_output["symptom_entities"]:
                    try:
                        # Validate source span
                        source_span_data = entity_data.get("source_span", {})
                        start = source_span_data.get("start", 0)
                        end = source_span_data.get("end", 0)
                        span_text = source_span_data.get("text", "")

                        if 0 <= start < end <= len(text):
                            actual_text = text[start:end]
                            source_span_validated = (actual_text == span_text)
                        else:
                            source_span_validated = False

                        source_span = SourceSpan(
                            start=start,
                            end=end,
                            text=span_text
                        )

                        entity = SymptomEntity(
                            text=entity_data["text"],
                            confidence=entity_data.get("confidence", 0.5),
                            source_span=source_span,
                            source_span_validated=source_span_validated
                        )

                        result["symptom_entities"].append(entity.model_dump())

                        if entity.confidence < 0.5:
                            result["low_confidence"].append(entity.model_dump())

                    except (ValidationError, KeyError, ValueError) as e:
                        error_msg = f"Failed to validate symptom entity: {str(e)}"
                        result["errors"].append(error_msg)
                        continue

        except Exception as e:
            result["errors"].append(f"Symptom extraction failed: {str(e)}")

        return result
```

### Step 3: Update Response Schema

Add `symptom_entities` field to `EntityResponse` in `src/schemas/entities.py`:

```python
class EntityResponse(BaseModel):
    temporal_entities: list[TemporalEntity] = Field(default=[])
    clinical_entities: list[ClinicalEntity] = Field(default=[])
    symptom_entities: list[SymptomEntity] = Field(default=[])  # New field
    errors: list[str] = Field(default=[])
    low_confidence: list[TemporalEntity | ClinicalEntity | SymptomEntity] = Field(default=[])
```

### Step 4: Register in Endpoint

Add to `src/api/extract.py`:

```python
from src.extraction import symptom  # noqa: F401

# In extract_entities function:
symptom_extractor_cls = extractor_registry.get("symptom")
if symptom_extractor_cls is not None:
    symptom_extractor = symptom_extractor_cls(request.app.state.model)
    extractors.append(("symptom", symptom_extractor))
```

The symptom extractor now runs in parallel with temporal and clinical extractors.

## Existing Extractors

### TemporalExtractor

**Registry Key:** `"temporal"`  
**Module:** `src/extraction/temporal.py`  
**Prompt:** `src/prompts/temporal_prompt.py`

**Extracts:**
- **Date** — Calendar dates in any format (DD.MM.YYYY, DD.MM.YY, etc.)
- **LOS** — Length-of-stay indicators (Verweildauer, Aufenthaltsdauer, duration in days)

**Example Entities:**
- "15.03.2025" (Date)
- "4 Tage" (LOS)

### ClinicalExtractor

**Registry Key:** `"clinical"`  
**Module:** `src/extraction/clinical.py`  
**Prompt:** `src/prompts/clinical_prompt.py`

**Extracts:**
- **Diagnosis** — Medical conditions with or without ICD-10 codes (e.g., "Lumbalgie (M54.5)", "Diabetes mellitus Typ 2")
- **Medication** — Medications with or without dosages (e.g., "Ibuprofen 600mg", "Metformin 1000mg")

**Example Entities:**
- "Lumbalgie (M54.5)" (Diagnosis)
- "Ibuprofen 600mg" (Medication)

## Framework Decisions

### Phase 1: Foundation

The architecture is built on design decisions from Phase 1:

- **Local LLM Deployment** — llama-cpp-python with GGUF models (no cloud dependencies)
- **Structured Output** — Native JSON schema mode for LLM responses
- **FastAPI Async Patterns** — Parallel extraction via asyncio.gather
- **Pydantic Validation** — Type-safe entity schemas with automatic validation

See `.planning/phases/01-foundation-core-infrastructure/01-CONTEXT.md` for detailed Phase 1 decisions.

### Source Span Validation

All extractors follow the same validation pattern:

1. **LLM Provides Spans** — Character offsets included in JSON response
2. **Zero-Based Offsets** — `[start, end)` format matching Python slicing
3. **Exact Match Validation** — Verify `input_text[start:end] == entity.source_span.text`
4. **Validated Flag** — `source_span_validated` boolean indicates verification result
5. **Partial Results** — Include entities even if span validation fails (flag = false)

This pattern detects LLM hallucination while preserving all extraction results.

## Design Principles

1. **Dependency Injection** — Model passed to extractor constructor (not global state)
2. **Partial Results** — Return valid entities even if some extractions fail
3. **Error Transparency** — Errors array contains detailed validation messages
4. **Parallel Execution** — All extractors run concurrently via asyncio.gather
5. **Plugin Discovery** — Import-based registration (no manual configuration)
6. **Type Safety** — Pydantic schemas enforce structure at runtime

## Testing Extractors

Example test for new extractor:

```python
def test_extract_symptom_entities():
    from fastapi.testclient import TestClient
    from src.main import app
    from unittest.mock import MagicMock

    mock_model = MagicMock()
    mock_model.create_chat_completion.return_value = {
        "choices": [{
            "message": {
                "content": '{"symptom_entities": [{"type": "Symptom", "text": "Kopfschmerzen", "confidence": 0.90, "source_span": {"start": 20, "end": 33, "text": "Kopfschmerzen"}}]}'
            }
        }]
    }
    app.state.model = mock_model

    client = TestClient(app)
    response = client.post(
        "/extract",
        json={"text": "Patient klagt über Kopfschmerzen seit 2 Tagen."}
    )

    assert response.status_code == 200
    data = response.json()
    assert "symptom_entities" in data
    assert len(data["symptom_entities"]) > 0
```

## References

- **Plugin Pattern Documentation:** See `src/extraction/base.py` for registry implementation
- **Existing Extractors:** Review `src/extraction/temporal.py` and `src/extraction/clinical.py` for reference implementations
- **Prompt Engineering:** See `src/prompts/` for German medical prompt examples
- **Schema Definitions:** See `src/schemas/entities.py` for Pydantic models
- **Phase 1 Decisions:** See `.planning/phases/01-foundation-core-infrastructure/01-CONTEXT.md` for framework choices
