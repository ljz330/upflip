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
import traceback

# EdgeOne strips the /api prefix — FastAPI routes must not include it.
os.environ["API_PREFIX"] = ""
os.environ["EDGEONE"] = "1"

# Ensure backend imports resolve.
# On EdgeOne, cloud-functions/api/ is deployed as /var/user/api/ — only ONE
# level up from the repo root, not two (the cloud-functions prefix is stripped).
_backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, _backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Instantiate FastAPI INLINE (required for EdgeOne detection) ──────
app = FastAPI(title="UPFLIP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "platform": "edgeone"}


@app.get("/debug")
async def debug_info():
    """Return diagnostic info to help troubleshoot deployment issues."""
    # Resolve the real backend path
    _real_backend = os.path.abspath(_backend_dir)
    _parent = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _ls(path):
        """List directory contents, return None if not found."""
        try:
            return sorted(os.listdir(path))
        except Exception:
            return None

    info = {
        "python_version": sys.version,
        "sys_path": [os.path.abspath(p) for p in sys.path[:5]],
        "cwd": os.getcwd(),
        "file": __file__,
        "backend_dir_raw": _backend_dir,
        "backend_dir_real": _real_backend,
        "parent_dir": _parent,
        # What files actually exist?
        "ls_cwd": _ls(os.getcwd()),
        "ls_parent": _ls(_parent),
        "ls_backend": _ls(_real_backend),
        "ls_backend_routes": _ls(os.path.join(_real_backend, "routes")),
    }
    # Try importing the router
    try:
        from routes.optimize import router as _test_router
        info["router_import"] = "ok"
        info["router_routes"] = [r.path for r in _test_router.routes]
    except Exception as exc:
        info["router_import"] = f"FAILED: {exc}"
        info["router_traceback"] = traceback.format_exc()
    return info


# ── Lazy-load the optimizer router ───────────────────────────────────
# Wrapped in try/except so /health and /debug work even if the heavy
# imports fail.  EdgeOne will still register this file as a FastAPI app
# because it detected ``app = FastAPI(...)`` above.
try:
    from routes.optimize import router as optimize_router  # noqa: E402
    app.include_router(optimize_router, prefix="")
except Exception:
    # If the router import fails, at least /health and /debug still work.
    # The error details are exposed via /debug above.
    pass
