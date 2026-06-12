# German Clinical NLP Pipeline

Production-ready information extraction pipeline for German clinical text — demonstrates local LLM deployment, structured output validation, and hallucination detection with FastAPI and llama-cpp-python.

![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136.3-green)
![llama-cpp-python](https://img.shields.io/badge/llama--cpp--python-0.3.x-orange)
![Docker](https://img.shields.io/badge/Docker-20.10%2B-blue)
![License MIT](https://img.shields.io/badge/License-MIT-lightgrey)

---

## Quick Start

### Prerequisites

- Docker 20.10+ and docker-compose 2.x
- 8 GB RAM minimum
- 6 GB free disk space (for model file)

### Step 1: Clone and prepare

```bash
git clone https://github.com/nargizmammadli/german-clinical-nlp.git
cd german-clinical-nlp
cp .env.example .env
```

### Step 2: Download model (~4.5 GB)

```bash
mkdir -p models
wget -O models/mistral-7b-instruct.gguf \
  https://huggingface.co/mistral-community/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/Mistral-7B-Instruct-v0.2.Q4_K_M.gguf
```

### Step 3: Start the API

```bash
docker-compose up
```

> First run takes 30–60 seconds for the model to load. The container health check will show `healthy` once the model is ready. You can watch progress with `docker-compose logs -f`.

### Step 4: Test extraction

```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient wurde am 15.03.2024 mit Diabetes mellitus Typ 2 aufgenommen. Verweildauer: 5 Tage. Metformin 1000mg täglich."
  }'
```

**Expected response:**

```json
{
  "temporal_entities": [
    {
      "type": "Date",
      "text": "15.03.2024",
      "confidence": 0.97,
      "source_span": {"start": 17, "end": 27, "text": "15.03.2024"},
      "source_span_validated": true
    },
    {
      "type": "LOS",
      "text": "5 Tage",
      "confidence": 0.95,
      "source_span": {"start": 83, "end": 89, "text": "5 Tage"},
      "source_span_validated": true
    }
  ],
  "clinical_entities": [
    {
      "type": "Diagnosis",
      "text": "Diabetes mellitus Typ 2",
      "confidence": 0.96,
      "source_span": {"start": 32, "end": 55, "text": "Diabetes mellitus Typ 2"},
      "source_span_validated": true
    },
    {
      "type": "Medication",
      "text": "Metformin 1000mg",
      "confidence": 0.94,
      "source_span": {"start": 91, "end": 107, "text": "Metformin 1000mg"},
      "source_span_validated": true
    }
  ],
  "errors": [],
  "low_confidence": []
}
```

---

## API Reference

### GET /health

Check service status and model readiness.

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2024-03-15T10:30:00.000Z"
}
```

Returns `503 Service Unavailable` with `"status": "unavailable"` if the model is not yet loaded.

---

### GET /models

Retrieve active model metadata.

```bash
curl http://localhost:8000/models
```

```json
{
  "model_name": "Mistral 7B Instruct Q4_K_M",
  "model_path": "models/mistral-7b-instruct.gguf",
  "status": "loaded"
}
```

---

### POST /extract

Extract medical entities from German clinical text.

**curl example** (note: `-H "Content-Type: application/json"` is required — omitting it causes a 422 error):

```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Aufnahme am 03.01.2024. Entlassung nach 7 Tagen. Diagnose: Lumbalgie (M54.5). Ibuprofen 600mg 3x täglich."
  }'
```

**Python httpx example:**

```python
import httpx

client = httpx.Client(base_url="http://localhost:8000")
response = client.post(
    "/extract",
    json={
        "text": (
            "Aufnahme am 03.01.2024. Entlassung nach 7 Tagen. "
            "Diagnose: Lumbalgie (M54.5). Ibuprofen 600mg 3x täglich."
        )
    }
)

data = response.json()

print(f"Temporal entities: {len(data['temporal_entities'])}")
print(f"Clinical entities: {len(data['clinical_entities'])}")

for entity in data["temporal_entities"]:
    print(f"  [{entity['type']}] '{entity['text']}' (confidence: {entity['confidence']:.2f})")

for entity in data["clinical_entities"]:
    print(f"  [{entity['type']}] '{entity['text']}' (confidence: {entity['confidence']:.2f})")
```

**Response schema:**

| Field | Type | Description |
|-------|------|-------------|
| `temporal_entities` | array | Dates and length-of-stay indicators |
| `clinical_entities` | array | Diagnoses and medications |
| `errors` | array | Extraction or validation error messages |
| `low_confidence` | array | Entities below the confidence threshold (default 0.5) |

Each entity includes: `type`, `text`, `confidence` (0.0–1.0), `source_span` (`start`, `end`, `text`), `source_span_validated` (boolean).

---

## Example Extraction Output

**Input:**

```
Stationäre Aufnahme am 03.01.2024. Entlassung am 10.01.2024. Gesamtaufenthalt: 7 Tage.
Primärdiagnose: Bronchialkarzinom (C34.1). Chemotherapie mit Carboplatin begonnen.
```

**Response:**

```json
{
  "temporal_entities": [
    {
      "type": "Date",
      "text": "03.01.2024",
      "confidence": 0.98,
      "source_span": {"start": 23, "end": 33, "text": "03.01.2024"},
      "source_span_validated": true
    },
    {
      "type": "Date",
      "text": "10.01.2024",
      "confidence": 0.97,
      "source_span": {"start": 49, "end": 59, "text": "10.01.2024"},
      "source_span_validated": true
    },
    {
      "type": "LOS",
      "text": "7 Tage",
      "confidence": 0.96,
      "source_span": {"start": 79, "end": 85, "text": "7 Tage"},
      "source_span_validated": true
    }
  ],
  "clinical_entities": [
    {
      "type": "Diagnosis",
      "text": "Bronchialkarzinom (C34.1)",
      "confidence": 0.95,
      "source_span": {"start": 103, "end": 128, "text": "Bronchialkarzinom (C34.1)"},
      "source_span_validated": true
    },
    {
      "type": "Medication",
      "text": "Carboplatin",
      "confidence": 0.93,
      "source_span": {"start": 148, "end": 159, "text": "Carboplatin"},
      "source_span_validated": true
    }
  ],
  "errors": [],
  "low_confidence": []
}
```

See [data/examples/](data/examples/) for full extraction samples covering diagnoses, medications, and mixed entities.

---

## Why This Project

**Local LLM, not cloud API.** No data leaves the machine — no API key, no network latency, no per-token cost. The pipeline runs entirely on the host using llama-cpp-python with a quantized GGUF model. This demonstrates a production-ready self-hosted deployment pattern: the same architecture scales from a developer laptop to an on-premise hospital server with zero code changes, only resource scaling.

**German clinical text.** German medical NLP is underrepresented in open-source tooling compared to English. German introduces distinct challenges: compound words like "Krankenhausaufenthalt" (hospital stay) or "Behandlungsdauer" (treatment duration) that must be parsed as single entities; date formats in DD.MM.YYYY rather than YYYY-MM-DD; medical abbreviations like "Pat." (Patient), "Aufn." (Aufnahme), and "Entl." (Entlassung) that differ from English conventions. Using a multilingual model (Mistral 7B) rather than a German-specific fine-tune keeps the deployment simple while still handling these nuances.

**Plugin architecture.** New entity types — allergies, procedures, lab values — can be added by creating a single file that implements `BaseExtractor` and applying the `@register_extractor` decorator. The core pipeline (`src/api/extract.py`) does not need to change. This is the key extensibility demonstration: see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the complete plugin pattern and a step-by-step walkthrough for adding a new entity type.

---

## Architecture

The pipeline uses a modular plugin architecture. POST /extract triggers parallel extraction via `asyncio.gather` across all registered extractors. Each extractor calls llama-cpp-python with a JSON schema constraint, returns validated Pydantic entities, and results are merged into `EntityResponse`.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for component diagrams, plugin pattern details, and how to add a new entity type.

---

## Development

### Running Tests

```bash
# With Docker
docker-compose run api pytest

# Without Docker (requires Python 3.11+)
pip install ".[dev]"
pytest
```

### Adding a New Entity Type

1. Create `src/extraction/my_extractor.py` implementing `BaseExtractor` — define your extraction logic in the `extract()` method
2. Define a Pydantic schema in the same file for your new entity type
3. Apply `@register_extractor("my_entity")` decorator to auto-register the class

The extractor runs in parallel with existing ones automatically — no changes to the core pipeline required.

For a full step-by-step walkthrough with code snippets, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## License

MIT License — see [LICENSE](LICENSE) for full text.

Author: Nargiz Mammadli
