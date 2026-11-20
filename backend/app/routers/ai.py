"""AI tools: lesson plan and assignment generation."""
from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Assignment, Lesson, Teacher
from ..schemas import AIResult, AssignmentRequest, LessonPlanRequest
from ..services import ai_service, llm
from ..services.security import current_teacher

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/status")
def ai_status():
    return {"mode": llm.provider() or "mock", "model": llm.model_name()}


@router.post("/lesson-plan", response_model=AIResult)
async def lesson_plan(req: LessonPlanRequest, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    content, mode = await run_in_threadpool(ai_service.generate_lesson_plan, req)
    saved_id = None
    if req.save:
        lesson = Lesson(
            teacher_id=teacher.id, title=req.topic, subject=req.subject, grade=req.grade,
            topic=req.topic, duration_min=req.duration_min, plan=content,
        )
        db.add(lesson)
        db.commit()
        saved_id = lesson.id
    return AIResult(content=content, mode=mode, saved_id=saved_id)


@router.post("/assignment", response_model=AIResult)
async def assignment(req: AssignmentRequest, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    content, mode = await run_in_threadpool(ai_service.generate_assignment, req)
    saved_id = None
    if req.save:
        a = Assignment(
            teacher_id=teacher.id, lesson_id=req.lesson_id, title=req.topic, kind=req.kind, content=content,
        )
        db.add(a)
        db.commit()
        saved_id = a.id
    return AIResult(content=content, mode=mode, saved_id=saved_id)
