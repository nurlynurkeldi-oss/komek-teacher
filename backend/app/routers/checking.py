"""AI checking workflow for an assignment (teacher side).

Step 1  POST   /api/assignments/{id}/sources          teacher uploads lesson material
Step 2  POST   /api/assignments/{id}/analyze          AI analyzes material -> expected answers + rubric
Step 3  POST   /api/assignments/{id}/submissions      teacher uploads a student's work
        (students upload themselves via the public link, see public.py)
Step 4  (automatic, background)                       AI checks each submission
Step 5  PATCH  /api/submissions/{id}/grade            teacher reviews, changes and finalizes the grade
"""
import secrets
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Assignment, Material, Submission, SubmissionFile, Teacher
from ..schemas import TeacherGradeIn
from ..services import checker, llm
from ..services.security import current_teacher
from ..services.storage_service import AI_READABLE_EXTENSIONS, HEIC_EXTENSIONS, storage

router = APIRouter(prefix="/api", tags=["checking"])

MAX_FILES_PER_SUBMISSION = 10


def new_share_code() -> str:
    return secrets.token_urlsafe(6).replace("-", "x").replace("_", "y")


def own_assignment(db: Session, teacher: Teacher, assignment_id: int) -> Assignment:
    a = db.get(Assignment, assignment_id)
    if not a or a.teacher_id != teacher.id:
        raise HTTPException(404, "Assignment not found")
    return a


def own_submission(db: Session, teacher: Teacher, submission_id: int) -> Submission:
    s = db.get(Submission, submission_id)
    if not s or s.assignment.teacher_id != teacher.id:
        raise HTTPException(404, "Submission not found")
    return s


def submission_summary(s: Submission) -> dict:
    final = s.teacher_score if s.teacher_score is not None else s.ai_score
    return {
        "id": s.id, "student_name": s.student_name, "status": s.status, "error": s.error,
        "ai_score": s.ai_score, "teacher_score": s.teacher_score, "final_score": final,
        "finalized": s.finalized, "created_at": s.created_at, "checked_at": s.checked_at,
        "file_count": len(s.files),
    }


async def create_submission(
    db: Session, a: Assignment, student_name: str, files: list[UploadFile], background: BackgroundTasks
) -> Submission:
    student_name = (student_name or "").strip()
    if not student_name:
        raise HTTPException(400, "Student name is required")
    files = [f for f in files if f.filename]
    if not files:
        raise HTTPException(400, "Attach at least one file or photo")
    if len(files) > MAX_FILES_PER_SUBMISSION:
        raise HTTPException(400, f"At most {MAX_FILES_PER_SUBMISSION} files")
    s = Submission(assignment_id=a.id, student_name=student_name[:120])
    db.add(s)
    db.flush()
    try:
        for f in files:
            stored, size = await storage.save(f, f"submissions/{a.id}", AI_READABLE_EXTENSIONS)
            ctype = "image/jpeg" if Path(f.filename).suffix.lower() in HEIC_EXTENSIONS else f.content_type
            s.files.append(SubmissionFile(original_name=f.filename, stored_name=stored, content_type=ctype, size_bytes=size))
    except HTTPException:
        for sf in s.files:
            storage.delete(sf.stored_name)
        db.rollback()
        raise
    db.commit()
    background.add_task(checker.grade_submission, s.id)
    return s


# ------------------------------------------------------------ overview
@router.get("/assignments/{assignment_id}/workflow")
def workflow(assignment_id: int, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    a = own_assignment(db, teacher, assignment_id)
    if not a.share_code:
        a.share_code = new_share_code()
        db.commit()
    return {
        "assignment": {
            "id": a.id, "title": a.title, "kind": a.kind, "content": a.content, "subject": a.subject,
            "grade": a.grade, "language": a.language, "max_score": a.max_score, "due_date": a.due_date,
            "share_code": a.share_code,
        },
        "sources": [
            {"id": m.id, "original_name": m.original_name, "size_bytes": m.size_bytes} for m in a.sources
        ],
        "ai_enabled": checker.ai_enabled(),
        "ai_provider": llm.provider(),
        "ai_model": llm.model_name(),
        "analysis_status": a.analysis_status,
        "analysis_error": a.analysis_error,
        "analysis": checker.parse_json(a.analysis),
        "submissions": [submission_summary(s) for s in sorted(a.submissions, key=lambda x: x.created_at)],
    }


# ------------------------------------------------------------ step 1
@router.post("/assignments/{assignment_id}/sources")
async def add_source(
    assignment_id: int, file: UploadFile = File(...),
    teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db),
):
    a = own_assignment(db, teacher, assignment_id)
    stored, size = await storage.save(file, teacher.id, AI_READABLE_EXTENSIONS)
    ctype = "image/jpeg" if Path(file.filename or "").suffix.lower() in HEIC_EXTENSIONS else file.content_type
    m = Material(teacher_id=teacher.id, assignment_id=a.id, original_name=file.filename or "file",
                 stored_name=stored, content_type=ctype, size_bytes=size)
    db.add(m)
    db.commit()
    return {"id": m.id, "original_name": m.original_name, "size_bytes": m.size_bytes}


@router.delete("/assignments/{assignment_id}/sources/{material_id}")
def remove_source(assignment_id: int, material_id: int, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    a = own_assignment(db, teacher, assignment_id)
    m = db.get(Material, material_id)
    if not m or m.assignment_id != a.id:
        raise HTTPException(404, "File not found")
    storage.delete(m.stored_name)
    db.delete(m)
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------ step 2
@router.post("/assignments/{assignment_id}/analyze")
def analyze(assignment_id: int, background: BackgroundTasks, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    a = own_assignment(db, teacher, assignment_id)
    if not checker.ai_enabled():
        raise HTTPException(400, "AI is not connected (set AI_MODE=gemini and GEMINI_API_KEY in backend/.env)")
    if not a.sources and not (a.content or "").strip():
        raise HTTPException(400, "Upload material or write the task first (step 1)")
    if a.analysis_status == "running":
        return {"status": "running"}
    a.analysis_status, a.analysis_error = "running", None
    db.commit()
    background.add_task(checker.analyze_assignment, a.id)
    return {"status": "running"}


# ------------------------------------------------------------ step 3 (teacher uploads for a student)
@router.post("/assignments/{assignment_id}/submissions")
async def add_submission(
    assignment_id: int, background: BackgroundTasks,
    student_name: str = Form(...), files: list[UploadFile] = File(...),
    teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db),
):
    a = own_assignment(db, teacher, assignment_id)
    s = await create_submission(db, a, student_name, files, background)
    return submission_summary(s)


# ------------------------------------------------------------ step 4 / 5
@router.get("/submissions/{submission_id}")
def get_submission(submission_id: int, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    s = own_submission(db, teacher, submission_id)
    return {
        **submission_summary(s),
        "teacher_comment": s.teacher_comment,
        "max_score": s.assignment.max_score,
        "ai_result": checker.parse_json(s.ai_result),
        "files": [{"id": f.id, "original_name": f.original_name, "content_type": f.content_type} for f in s.files],
    }


@router.get("/submissions/{submission_id}/files/{file_id}")
def get_submission_file(submission_id: int, file_id: int, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    s = own_submission(db, teacher, submission_id)
    f = next((x for x in s.files if x.id == file_id), None)
    if not f:
        raise HTTPException(404, "File not found")
    return FileResponse(storage.open_path(f.stored_name), filename=f.original_name, media_type=f.content_type)


@router.post("/submissions/{submission_id}/regrade")
def regrade(submission_id: int, background: BackgroundTasks, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    s = own_submission(db, teacher, submission_id)
    if s.status == "checking":
        return submission_summary(s)
    s.status, s.error, s.finalized = "pending", None, False
    db.commit()
    background.add_task(checker.grade_submission, s.id)
    return submission_summary(s)


@router.patch("/submissions/{submission_id}/grade")
def set_grade(submission_id: int, data: TeacherGradeIn, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    s = own_submission(db, teacher, submission_id)
    max_score = s.assignment.max_score
    if data.teacher_score is not None and not (0 <= data.teacher_score <= max_score):
        raise HTTPException(400, f"Score must be between 0 and {max_score}")
    if data.finalized and data.teacher_score is None and s.ai_score is None:
        raise HTTPException(400, "Nothing to finalize yet")
    s.teacher_score = data.teacher_score
    s.teacher_comment = data.teacher_comment
    s.finalized = data.finalized
    db.commit()
    return submission_summary(s)


@router.delete("/submissions/{submission_id}")
def delete_submission(submission_id: int, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    s = own_submission(db, teacher, submission_id)
    for f in s.files:
        storage.delete(f.stored_name)
    db.delete(s)
    db.commit()
    return {"ok": True}
