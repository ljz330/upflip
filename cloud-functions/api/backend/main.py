import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Only load .env in local development — on Vercel / EdgeOne, env vars are set
# via the platform dashboard.
if not os.getenv("VERCEL") and not os.getenv("EDGEONE"):
    load_dotenv()

app = FastAPI(title="UPFLIP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# EdgeOne strips the /api prefix from the URL before routing to the function,
# so routes must be registered without /api.  Local dev and Vercel keep /api.
_API_PREFIX = os.getenv("API_PREFIX", "/api")

from routes.optimize import router as optimize_router
app.include_router(optimize_router, prefix=_API_PREFIX)


@app.get(_API_PREFIX + "/health")
async def health():
    return {"status": "ok"}


# Static files: serve from backend/static/ (local dev + Vercel).
# EdgeOne serves static files natively from the project root, so the mount
# is only used when not on EdgeOne.
if not os.getenv("EDGEONE"):
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
