"""App settings, read from environment / backend/.env."""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent
load_dotenv(BACKEND_DIR / ".env")


def _path(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (BACKEND_DIR / p).resolve()


class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
    storage_dir: Path = _path(os.getenv("STORAGE_DIR", "./data/uploads"))
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "20"))
    ai_mode: str = os.getenv("AI_MODE", "mock").lower()
    ai_model: str = os.getenv("AI_MODEL", "claude-opus-5-5")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    # gemini-2.5-flash is closed to new Google accounts, so the default is a current Flash model.
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip() or "gemini-3.5-flash"
    gemini_fallback_models: list[str] = [
        m.strip() for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.5-flash,gemini-3.8-flash,gemini-2.5-flash").split(",") if m.strip()
    ]
    frontend_dir: Path = PROJECT_DIR / "frontend"


settings = Settings()

# Make relative SQLite paths relative to backend/, and make sure the folder exists
# (absolute paths too, e.g. sqlite:////var/data/app.db on a Render persistent disk).
if settings.database_url.startswith("sqlite:///./"):
    db_file = BACKEND_DIR / settings.database_url.removeprefix("sqlite:///./")
    settings.database_url = f"sqlite:///{db_file.as_posix()}"
if settings.database_url.startswith("sqlite:///"):
    Path(settings.database_url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
settings.storage_dir.mkdir(parents=True, exist_ok=True)
