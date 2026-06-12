"""
Clinical entity extractor for German clinical text.

Extracts diagnoses and medications using LLM with structured output.
Per D-09: Registered via @register_extractor decorator.
Per D-11: Model injected via constructor.
Per D-14: Validates source spans match input text.
Per D-15: Flags entities with source_span_validated boolean.
Per D-16: LLM provides character-offset source spans.
"""

import json
from src.extraction.base import BaseExtractor, register_extractor
from src.prompts.clinical_prompt import CLINICAL_EXTRACTION_PROMPT
from src.schemas.entities import ClinicalEntity, SourceSpan
from pydantic import ValidationError


@register_extractor("clinical")
class ClinicalExtractor(BaseExtractor):
    """
    Extractor for clinical entities (diagnoses and medications).

    Uses LLM with structured JSON output to extract clinical information
    from German clinical text. Validates source spans against input text.
    """

    def extract(self, text: str) -> dict:
        """
        Extract clinical entities from German clinical text.

        Args:
            text: German clinical text to analyze

        Returns:
            Dictionary with structure:
            {
                "temporal_entities": [],
                "clinical_entities": [ClinicalEntity, ...],
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
                        "content": CLINICAL_EXTRACTION_PROMPT
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

            # Process clinical entities with source span validation
            if "clinical_entities" in llm_output:
                for entity_data in llm_output["clinical_entities"]:
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

                        # Create ClinicalEntity with validated flag per D-15
                        entity = ClinicalEntity(
                            type=entity_data["type"],
                            text=entity_data["text"],
                            confidence=entity_data.get("confidence", 0.5),
                            source_span=source_span,
                            source_span_validated=source_span_validated
                        )

                        # Add to results
                        # Per D-06: Confidence filtering is done at the endpoint level
                        # using the configurable CONFIDENCE_THRESHOLD env variable.
                        result["clinical_entities"].append(entity.model_dump())

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
