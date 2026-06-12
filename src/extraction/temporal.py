"""
Temporal entity extractor for German clinical text.

Extracts dates and length-of-stay indicators using LLM with structured output.
Per D-09: Registered via @register_extractor decorator.
Per D-11: Model injected via constructor.
Per D-14: Validates source spans match input text.
Per D-15: Flags entities with source_span_validated boolean.
Per D-16: LLM provides character-offset source spans.
"""

import json
from src.extraction.base import BaseExtractor, register_extractor
from src.prompts.temporal_prompt import TEMPORAL_EXTRACTION_PROMPT
from src.schemas.entities import TemporalEntity, SourceSpan
from pydantic import ValidationError


@register_extractor("temporal")
class TemporalExtractor(BaseExtractor):
    """
    Extractor for temporal entities (dates and length-of-stay indicators).

    Uses LLM with structured JSON output to extract temporal information
    from German clinical text. Validates source spans against input text.
    """

    def extract(self, text: str) -> dict:
        """
        Extract temporal entities from German clinical text.

        Args:
            text: German clinical text to analyze

        Returns:
            Dictionary with structure:
            {
                "temporal_entities": [TemporalEntity, ...],
                "clinical_entities": [],
                "errors": [str, ...],
                "low_confidence": [...]
            }

        Per D-05: Returns partial results even if some extractions fail.
        Per D-08: Errors captured in errors array.
        """
        result = {
            "temporal_entities": [],
            "clinical_entities": [],
            "errors": [],
            "low_confidence": []
        }

        try:
            # Call LLM with structured output per llama-cpp-python JSON schema mode
            # Per CLAUDE.md: Use response_format for JSON schema mode
            response = self.model.create_chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": TEMPORAL_EXTRACTION_PROMPT
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                response_format={
                    "type": "json_object"
                },
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=2048
            )

            # Extract JSON from response
            content = response["choices"][0]["message"]["content"]
            llm_output = json.loads(content)

            # Process temporal entities with source span validation
            if "temporal_entities" in llm_output:
                for entity_data in llm_output["temporal_entities"]:
                    try:
                        # Validate source span per D-14: check if input_text[start:end] == source_span.text
                        source_span_data = entity_data.get("source_span", {})
                        start = source_span_data.get("start", 0)
                        end = source_span_data.get("end", 0)
                        span_text = source_span_data.get("text", "")

                        # Validate span matches input text
                        if 0 <= start < end <= len(text):
                            actual_text = text[start:end]
                            source_span_validated = (actual_text == span_text)
                        else:
                            source_span_validated = False

                        # Create SourceSpan
                        source_span = SourceSpan(
                            start=start,
                            end=end,
                            text=span_text
                        )

                        # Create TemporalEntity with validated flag per D-15
                        entity = TemporalEntity(
                            type=entity_data["type"],
                            text=entity_data["text"],
                            confidence=entity_data.get("confidence", 0.5),
                            source_span=source_span,
                            source_span_validated=source_span_validated
                        )

                        # Add to results
                        result["temporal_entities"].append(entity.model_dump())

                        # Per D-06: Flag low confidence entities (threshold 0.5)
                        if entity.confidence < 0.5:
                            result["low_confidence"].append(entity.model_dump())

                    except (ValidationError, KeyError, ValueError) as e:
                        # Per D-05, D-08: Capture error but continue processing
                        error_msg = f"Failed to validate entity {entity_data.get('text', 'unknown')}: {str(e)}"
                        result["errors"].append(error_msg)
                        continue

        except json.JSONDecodeError as e:
            result["errors"].append(f"Failed to parse LLM JSON output: {str(e)}")
        except KeyError as e:
            result["errors"].append(f"Missing key in LLM response: {str(e)}")
        except Exception as e:
            result["errors"].append(f"Extraction failed: {str(e)}")

        return result
