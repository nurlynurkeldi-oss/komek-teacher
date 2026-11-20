"""Komek Teacher API entry point.

Run from the backend/ folder:
    uvicorn app.main:app --reload
Then open http://127.0.0.1:8000  (API docs: /docs)
"""
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import init_db
from .routers import ai, assignments, auth, checking, lessons, materials, public, rollcall

init_db()  # prototype: auto-create tables / add new columns (use Alembic later)


def _reset_interrupted_jobs() -> None:
    """AI jobs run in the server process; after a restart, unfinished ones must not hang forever."""
    from .database import SessionLocal
    from .models import Assignment, RollCallPhoto, Submission

    with SessionLocal() as db:
        db.query(Assignment).filter_by(analysis_status="running").update(
            {"analysis_status": "error", "analysis_error": "Interrupted by a server restart, run the analysis again"})
        interrupted = {"status": "error", "error": "Interrupted by a server restart, press ↻ to check again"}
        db.query(Submission).filter_by(status="checking").update(interrupted)
        # "pending" is fine while step 2 is not done (they are checked after it); otherwise the queued job was lost.
        for s in db.query(Submission).filter_by(status="pending"):
            if s.assignment.analysis_status == "done":
                s.status, s.error = interrupted["status"], interrupted["error"]
        db.query(RollCallPhoto).filter(RollCallPhoto.ai_status.in_(["pending", "checking"])).update(
            {"ai_status": "error", "ai_note": "Interrupted by a server restart, press ↻ to count again"})
        db.commit()


_reset_interrupted_jobs()

app = FastAPI(title="Komek Teacher API", version="0.1.0")

app.include_router(auth.router)
app.include_router(lessons.router)
app.include_router(assignments.router)
app.include_router(materials.router)
app.include_router(ai.router)
app.include_router(checking.router)
app.include_router(public.router)
app.include_router(rollcall.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.middleware("http")
async def no_stale_frontend(request, call_next):
    """Browsers must re-check the page/JS/CSS each load, so updates show up without a hard refresh."""
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


# Serve the browser frontend from the same server.
app.mount("/static", StaticFiles(directory=settings.frontend_dir), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(settings.frontend_dir / "index.html")
