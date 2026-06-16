"""Vercel serverless entry point for the UPFLIP FastAPI app.

On Vercel, the Python runtime looks for an ``app`` variable (ASGI application)
in ``api/index.py``.  This thin wrapper sets up the import path so the backend
package can be imported, then re-exports the FastAPI app.
"""

import os
import sys

# Ensure the backend directory is on sys.path so that imports like
# ``from routes.optimize import router`` resolve correctly.
backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, backend_dir)

# The FastAPI application instance — Vercel's Python runtime discovers this
# automatically.
from main import app  # noqa: E402
