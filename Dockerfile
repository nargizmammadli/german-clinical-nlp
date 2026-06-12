FROM python:3.11.12-slim

WORKDIR /app

# Install dependencies first for layer cache efficiency
# (pyproject.toml changes less frequently than source code)
COPY pyproject.toml ./

# llama-cpp-python may need build tools if a pre-built wheel is unavailable for linux/amd64.
# Install build-essential + cmake as a fallback; pip will use the wheel if available.
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential cmake && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir \
        "llama-cpp-python==0.3.28" \
        "fastapi==0.136.3" \
        "pydantic==2.13.4" \
        "uvicorn[standard]>=0.34.0" \
        "python-dotenv>=1.0.0" \
        "loguru>=0.7.0"

# Copy application source (changes more frequently than deps)
COPY src/ ./src/
COPY healthcheck.py ./

# Install the package itself now that source is present
RUN pip install --no-cache-dir --no-deps .

# Security: run as non-root user (ASVS V1.6 — T-03-01)
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

# Health check using Python stdlib urllib
# (curl not available in python:3.11-slim; no extra package needed)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python healthcheck.py

# Single worker required: llama-cpp-python Llama object is not picklable across processes.
# Exec form required: shell form breaks FastAPI lifespan signal propagation.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
