"""Lets `uvicorn app.main:app` work from the repository root (Render with an empty Root Directory).

The real package lives in backend/app; this makes `app.<module>` load from there.
"""
from pathlib import Path

__path__ = [str(Path(__file__).resolve().parent.parent / "backend" / "app")]
