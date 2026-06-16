"""EdgeOne Pages entry point for the UPFLIP FastAPI app.

EdgeOne Pages uses file-system routing: ``cloud-functions/api/index.py`` is
mapped to the ``/api`` URL prefix.  The prefix is stripped before the request
reaches FastAPI, so routes should be registered *without* the ``/api`` prefix.

This thin wrapper sets ``API_PREFIX=""``, adds the backend directory to
``sys.path``, and re-exports the FastAPI app from ``backend.main``.
"""

import os
import sys

# EdgeOne strips the /api prefix — FastAPI routes must not include it.
os.environ["API_PREFIX"] = ""
os.environ["EDGEONE"] = "1"

# Ensure backend imports resolve.
backend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
sys.path.insert(0, backend_dir)

# Re-export the FastAPI application.
from main import app  # noqa: E402
