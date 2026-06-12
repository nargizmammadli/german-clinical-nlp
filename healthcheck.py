# curl not available in python:3.11-slim; use stdlib urllib
# Exit 0 = container healthy (GET /health returned 200)
# Exit 1 = container unhealthy (non-200 response or any exception)
import sys
import urllib.request

try:
    response = urllib.request.urlopen("http://localhost:8000/health", timeout=5)
    if response.status == 200:
        sys.exit(0)
    else:
        sys.exit(1)
except Exception:
    sys.exit(1)
