"""
Base extractor class and plugin registry.

Per D-09: Plugin pattern with decorator-based registration.
Per D-11: Dependency injection pattern - model passed to extractor constructor.
"""

from abc import ABC, abstractmethod
from typing import Dict, Type

# Module-level extractor registry (populated via @register_extractor decorator)
extractor_registry: Dict[str, Type['BaseExtractor']] = {}


def register_extractor(name: str):
    """
    Decorator to register an extractor class in the global registry.

    Usage:
        @register_extractor("temporal")
        class TemporalExtractor(BaseExtractor):
            ...

    Args:
        name: Registry key for this extractor (e.g., "temporal", "clinical")

    Returns:
        Decorator function that adds class to extractor_registry
    """
    def decorator(cls: Type[BaseExtractor]) -> Type[BaseExtractor]:
        extractor_registry[name] = cls
        return cls
    return decorator


class BaseExtractor(ABC):
    """
    Abstract base class for entity extractors.

    Per D-11: Model is injected via constructor (dependency injection pattern).
    Subclasses implement extract() to perform entity extraction using the model.
    """

    def __init__(self, model):
        """
        Initialize extractor with LLM model.

        Args:
            model: llama-cpp-python Llama instance for inference
        """
        self.model = model

    @abstractmethod
    def extract(self, text: str) -> dict:
        """
        Extract entities from input text.

        Args:
            text: German clinical text to analyze

        Returns:
            Dictionary matching EntityResponse structure:
            {
                "temporal_entities": [...],
                "clinical_entities": [...],
                "errors": [...],
                "low_confidence": [...]
            }
        """
        pass
