"""Lessons CRUD + dashboard summary."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Assignment, Lesson, Material, Teacher
from ..schemas import DashboardOut, LessonIn, LessonOut
from ..services.security import current_teacher

router = APIRouter(prefix="/api", tags=["lessons"])


def _own_lesson(db: Session, teacher: Teacher, lesson_id: int) -> Lesson:
    lesson = db.get(Lesson, lesson_id)
    if not lesson or lesson.teacher_id != teacher.id:
        raise HTTPException(404, "Lesson not found")
    return lesson


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    upcoming = (
        db.query(Lesson)
        .filter(Lesson.teacher_id == teacher.id, Lesson.scheduled_at >= datetime.now())
        .order_by(Lesson.scheduled_at).limit(5).all()
    )
    return DashboardOut(
        lessons=db.query(Lesson).filter_by(teacher_id=teacher.id).count(),
        assignments=db.query(Assignment).filter_by(teacher_id=teacher.id).count(),
        materials=db.query(Material).filter_by(teacher_id=teacher.id).count(),
        upcoming=upcoming,
    )


@router.get("/lessons", response_model=list[LessonOut])
def list_lessons(teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    return db.query(Lesson).filter_by(teacher_id=teacher.id).order_by(Lesson.created_at.desc()).all()


@router.post("/lessons", response_model=LessonOut)
def create_lesson(data: LessonIn, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    lesson = Lesson(teacher_id=teacher.id, **data.model_dump())
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


@router.get("/lessons/{lesson_id}", response_model=LessonOut)
def get_lesson(lesson_id: int, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    return _own_lesson(db, teacher, lesson_id)


@router.put("/lessons/{lesson_id}", response_model=LessonOut)
def update_lesson(lesson_id: int, data: LessonIn, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    lesson = _own_lesson(db, teacher, lesson_id)
    for key, value in data.model_dump().items():
        setattr(lesson, key, value)
    db.commit()
    db.refresh(lesson)
    return lesson


@router.delete("/lessons/{lesson_id}")
def delete_lesson(lesson_id: int, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    db.delete(_own_lesson(db, teacher, lesson_id))
    db.commit()
    return {"ok": True}
