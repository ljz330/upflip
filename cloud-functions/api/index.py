"""EdgeOne Pages entry point for the UPFLIP FastAPI app.

EdgeOne Pages uses file-system routing: ``cloud-functions/api/index.py`` is
mapped to the ``/api`` URL prefix.  The prefix is stripped before the request
reaches FastAPI, so routes are registered *without* the ``/api`` prefix.

IMPORTANT: EdgeOne detects Python entry points by scanning for the literal
pattern ``app = FastAPI(...)`` in the file.  The app must be instantiated
inline here — merely importing it from ``backend.main`` won't work.
"""

import os
import sys

# EdgeOne strips the /api prefix — FastAPI routes must not include it.
os.environ["API_PREFIX"] = ""
os.environ["EDGEONE"] = "1"

# Ensure backend imports resolve.
_backend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
sys.path.insert(0, _backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Instantiate FastAPI INLINE (required for EdgeOne detection) ──────
app = FastAPI(title="UPFLIP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and mount the optimizer router (no /api prefix — EdgeOne strips it).
from routes.optimize import router as optimize_router  # noqa: E402

app.include_router(optimize_router, prefix="")


@app.get("/health")
async def health():
    return {"status": "ok"}
