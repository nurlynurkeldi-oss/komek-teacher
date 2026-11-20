"""Assignments CRUD."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Assignment, Lesson, Teacher
from ..schemas import AssignmentIn, AssignmentOut
from ..services.security import current_teacher
from ..services.storage_service import storage
from .checking import new_share_code

router = APIRouter(prefix="/api/assignments", tags=["assignments"])


def _own(db: Session, teacher: Teacher, assignment_id: int) -> Assignment:
    a = db.get(Assignment, assignment_id)
    if not a or a.teacher_id != teacher.id:
        raise HTTPException(404, "Assignment not found")
    return a


def _check_lesson(db: Session, teacher: Teacher, lesson_id: int | None) -> None:
    if lesson_id is not None:
        lesson = db.get(Lesson, lesson_id)
        if not lesson or lesson.teacher_id != teacher.id:
            raise HTTPException(400, "Unknown lesson_id")


@router.get("")
def list_assignments(teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    rows = db.query(Assignment).filter_by(teacher_id=teacher.id).order_by(Assignment.created_at.desc()).all()
    return [
        {
            **AssignmentOut.model_validate(a).model_dump(),
            "submission_count": len(a.submissions),
            "checked_count": sum(1 for s in a.submissions if s.status == "checked"),
            "finalized_count": sum(1 for s in a.submissions if s.finalized),
        }
        for a in rows
    ]


@router.post("", response_model=AssignmentOut)
def create_assignment(data: AssignmentIn, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    _check_lesson(db, teacher, data.lesson_id)
    a = Assignment(teacher_id=teacher.id, share_code=new_share_code(), **data.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.get("/{assignment_id}", response_model=AssignmentOut)
def get_assignment(assignment_id: int, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    return _own(db, teacher, assignment_id)


@router.put("/{assignment_id}", response_model=AssignmentOut)
def update_assignment(assignment_id: int, data: AssignmentIn, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    a = _own(db, teacher, assignment_id)
    _check_lesson(db, teacher, data.lesson_id)
    for key, value in data.model_dump().items():
        setattr(a, key, value)
    db.commit()
    db.refresh(a)
    return a


@router.delete("/{assignment_id}")
def delete_assignment(assignment_id: int, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    a = _own(db, teacher, assignment_id)
    for s in a.submissions:
        for f in s.files:
            storage.delete(f.stored_name)
    for m in a.sources:
        storage.delete(m.stored_name)
        db.delete(m)
    db.delete(a)
    db.commit()
    return {"ok": True}
