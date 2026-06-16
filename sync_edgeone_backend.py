"""Sync backend code into cloud-functions for EdgeOne deployment.

EdgeOne Pages only deploys the cloud-functions/ directory to its Python
runtime — the project root's backend/ is NOT available.  This script
copies backend/ → cloud-functions/api/backend/ so EdgeOne can import it.

Run this whenever backend code changes.  The copy is committed to git.
"""
import shutil
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "backend")
DST = os.path.join(ROOT, "cloud-functions", "api", "backend")

# Patterns to exclude
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".env", "static")

print(f"Syncing: {SRC} → {DST}")
shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST, ignore=IGNORE)
print("Done. Now commit cloud-functions/api/backend/ and push.")
