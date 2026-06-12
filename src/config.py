"""
Environment configuration with fail-fast validation.

Validates required environment variables and resolves paths relative to project root.
Raises clear errors if configuration is invalid or missing.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists (development mode)
load_dotenv()

# Project root directory (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Validate required environment variables
REQUIRED_VARS = ["MODEL_PATH"]
missing = [var for var in REQUIRED_VARS if not os.getenv(var)]
if missing:
    raise EnvironmentError(
        f"Missing required environment variables: {', '.join(missing)}. "
        f"See .env.example for required configuration."
    )

# Extract configuration values
MODEL_PATH_RAW = os.getenv("MODEL_PATH")
MODEL_NAME = os.getenv("MODEL_NAME", "unknown")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Confidence threshold for entity filtering per D-06
# Entities below this threshold are moved to the low_confidence array in responses.
CONFIDENCE_THRESHOLD_RAW = os.getenv("CONFIDENCE_THRESHOLD", "0.5")
try:
    CONFIDENCE_THRESHOLD = float(CONFIDENCE_THRESHOLD_RAW)
except ValueError:
    raise ValueError(
        f"CONFIDENCE_THRESHOLD must be a number between 0.0 and 1.0, "
        f"got: '{CONFIDENCE_THRESHOLD_RAW}'"
    )
if not 0.0 <= CONFIDENCE_THRESHOLD <= 1.0:
    raise ValueError(
        f"CONFIDENCE_THRESHOLD must be between 0.0 and 1.0, "
        f"got {CONFIDENCE_THRESHOLD}"
    )

# Resolve MODEL_PATH relative to project root (per D-08)
MODEL_PATH = PROJECT_ROOT / MODEL_PATH_RAW

# Validate model file exists
if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Model file not found at: {MODEL_PATH.resolve()}\n"
        f"Please ensure MODEL_PATH in .env points to a valid GGUF model file."
    )

# Threat mitigation T-01-01: Validate MODEL_PATH is within expected models/ directory
# This prevents path traversal attacks via environment variable tampering
if not MODEL_PATH.resolve().is_relative_to(PROJECT_ROOT / "models"):
    raise ValueError(
        f"Security: MODEL_PATH must be within the models/ directory.\n"
        f"Got: {MODEL_PATH.resolve()}\n"
        f"Expected parent: {(PROJECT_ROOT / 'models').resolve()}"
    )
