"""Render may build from the repository root: run backend/download_models.py from here."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent / "backend" / "download_models.py"), run_name="__main__")
