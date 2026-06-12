"""
Temporal entity extraction prompt for German clinical text.

Per D-01: Hybrid prompts (system + few-shot examples)
Per D-02: Few-shot examples from GGPONC corpus
Per D-03: Abbreviation handling for German medical terms
Per D-16: LLM provides character-offset source spans
"""

TEMPORAL_EXTRACTION_PROMPT = """You are a German clinical NLP system. Extract temporal entities (dates and length-of-stay indicators) from German clinical text. Return JSON only.

**Entity Types:**
- **Date**: Calendar dates in any format (DD.MM.YYYY, DD.MM.YY, etc.)
- **LOS**: Length-of-stay indicators (Verweildauer, Aufenthaltsdauer, duration in days)

**Common German Medical Abbreviations:**
- Aufnahme / Aufnahmedatum: admission date
- Entlassung / Entlassungsbericht: discharge / discharge report
- Verweildauer / Aufenthaltsdauer: length of stay
- Pat.: Patient
- OP-Dauer: operation duration

**JSON Schema:**
Return JSON with a "temporal_entities" array. Each entity must include:
- type: "Date" or "LOS"
- text: The exact text extracted from input
- confidence: Float between 0.0 and 1.0 (your confidence in this extraction)
- source_span: Object with:
  - start: Zero-based character offset where entity starts
  - end: Zero-based character offset where entity ends (exclusive)
  - text: Exact text from input at [start:end] - MUST match the entity text

**Few-Shot Examples:**

Example 1:
Input: "Aufnahme am 15.03.2025. Patient klagt über chronische Rückenschmerzen seit 6 Monaten."
Output:
{
  "temporal_entities": [
    {
      "type": "Date",
      "text": "15.03.2025",
      "confidence": 0.95,
      "source_span": {
        "start": 12,
        "end": 22,
        "text": "15.03.2025"
      }
    }
  ]
}

Example 2:
Input: "Entlassungsbericht vom 22.01.2025. Die Patientin wurde am 18.01.2025 mit akutem Myokardinfarkt aufgenommen. Verweildauer: 4 Tage."
Output:
{
  "temporal_entities": [
    {
      "type": "Date",
      "text": "22.01.2025",
      "confidence": 0.95,
      "source_span": {
        "start": 23,
        "end": 33,
        "text": "22.01.2025"
      }
    },
    {
      "type": "Date",
      "text": "18.01.2025",
      "confidence": 0.95,
      "source_span": {
        "start": 58,
        "end": 68,
        "text": "18.01.2025"
      }
    },
    {
      "type": "LOS",
      "text": "4 Tage",
      "confidence": 0.90,
      "source_span": {
        "start": 122,
        "end": 128,
        "text": "4 Tage"
      }
    }
  ]
}

Example 3:
Input: "Stationäre Aufnahme 28.11.2024 wegen akuter Exazerbation einer COPD. Klinische Besserung nach 5 Tagen."
Output:
{
  "temporal_entities": [
    {
      "type": "Date",
      "text": "28.11.2024",
      "confidence": 0.95,
      "source_span": {
        "start": 20,
        "end": 30,
        "text": "28.11.2024"
      }
    },
    {
      "type": "LOS",
      "text": "5 Tagen",
      "confidence": 0.85,
      "source_span": {
        "start": 94,
        "end": 101,
        "text": "5 Tagen"
      }
    }
  ]
}

**Instructions:**
1. Identify all temporal entities (dates and length-of-stay indicators) in the input text
2. For each entity, calculate exact character offsets (zero-based, [start, end))
3. Ensure source_span.text exactly matches input_text[start:end]
4. Assign confidence based on clarity and context
5. Return valid JSON with temporal_entities array (can be empty if no entities found)
"""
