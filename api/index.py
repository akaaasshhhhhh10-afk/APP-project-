"""Vercel serverless entrypoint: exposes the combined FastAPI + Flask app from backend/main.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from main import app  # noqa: E402,F401
