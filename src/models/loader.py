"""
Model loader for GGUF models via llama-cpp-python.

Initializes Llama models with appropriate context window and threading settings.
"""

import time
from pathlib import Path
from typing import Optional

try:
    from llama_cpp import Llama
except ImportError:
    # Allow module to be imported even if llama-cpp-python is not installed
    # This enables testing without the library (mocked model state)
    Llama = None


def initialize_model(model_path: Path, n_ctx: int = 8192) -> Optional[object]:
    """
    Initialize a Llama model from a GGUF file.

    Args:
        model_path: Path to the GGUF model file
        n_ctx: Context window size (default: 8192, per MODEL-04)

    Returns:
        Llama model instance, or None if llama-cpp-python is not installed

    Raises:
        FileNotFoundError: If model file does not exist
        RuntimeError: If model loading fails
    """
    if Llama is None:
        raise ImportError(
            "llama-cpp-python is not installed. "
            "Install it with: pip install llama-cpp-python==0.3.28"
        )

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    print(f"Loading model from {model_path} (may take 60-120 seconds)...")
    start_time = time.time()

    try:
        # Initialize Llama model with optimized settings
        model = Llama(
            model_path=str(model_path),
            n_ctx=4096,            # Enough for prompt + response
            n_threads=4,           # CPU optimization
            verbose=True           # Show loading progress (RESEARCH.md pitfall 3)
        )

        elapsed = time.time() - start_time
        print(f"Model loaded in {elapsed:.1f}s")

        return model

    except Exception as e:
        raise RuntimeError(f"Failed to load model from {model_path}: {e}") from e
