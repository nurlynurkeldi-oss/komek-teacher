"""Student side (no login): open the assignment by its link and upload the work (step 3)."""
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Assignment
from .checking import create_submission

router = APIRouter(prefix="/api/public", tags=["student"])


def _by_code(db: Session, code: str) -> Assignment:
    a = db.query(Assignment).filter_by(share_code=code).first()
    if not a:
        raise HTTPException(404, "Assignment not found")
    return a


@router.get("/a/{code}")
def assignment_for_student(code: str, db: Session = Depends(get_db)):
    a = _by_code(db, code)
    return {
        "title": a.title, "subject": a.subject, "grade": a.grade, "content": a.content,
        "due_date": a.due_date, "teacher": a.teacher.full_name, "language": a.language,
    }


@router.post("/a/{code}/submit")
async def submit(
    code: str, background: BackgroundTasks,
    student_name: str = Form(...), files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    a = _by_code(db, code)
    s = await create_submission(db, a, student_name, files, background)
    return {"ok": True, "id": s.id}
