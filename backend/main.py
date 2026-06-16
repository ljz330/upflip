import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Only load .env in local development — Vercel sets env vars via dashboard.
if not os.getenv("VERCEL"):
    load_dotenv()

app = FastAPI(title="UPFLIP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routes.optimize import router as optimize_router

app.include_router(optimize_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Static files: serve from backend/static/ (local dev + Vercel).
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
