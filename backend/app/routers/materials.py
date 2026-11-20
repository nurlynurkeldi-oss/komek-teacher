"""Materials: upload / list / download / delete documents."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Lesson, Material, Teacher
from ..schemas import MaterialOut
from ..services.security import current_teacher
from ..services.storage_service import storage

router = APIRouter(prefix="/api/materials", tags=["materials"])


def _own(db: Session, teacher: Teacher, material_id: int) -> Material:
    m = db.get(Material, material_id)
    if not m or m.teacher_id != teacher.id:
        raise HTTPException(404, "Material not found")
    return m


@router.get("", response_model=list[MaterialOut])
def list_materials(teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    return db.query(Material).filter_by(teacher_id=teacher.id).order_by(Material.created_at.desc()).all()


@router.post("", response_model=MaterialOut)
async def upload_material(
    file: UploadFile = File(...),
    lesson_id: int | None = Form(default=None),
    teacher: Teacher = Depends(current_teacher),
    db: Session = Depends(get_db),
):
    if lesson_id is not None:
        lesson = db.get(Lesson, lesson_id)
        if not lesson or lesson.teacher_id != teacher.id:
            raise HTTPException(400, "Unknown lesson_id")
    stored_name, size = await storage.save(file, teacher.id)
    m = Material(
        teacher_id=teacher.id, lesson_id=lesson_id, original_name=file.filename or "file",
        stored_name=stored_name, content_type=file.content_type, size_bytes=size,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.get("/{material_id}/download")
def download_material(material_id: int, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    m = _own(db, teacher, material_id)
    return FileResponse(storage.open_path(m.stored_name), filename=m.original_name, media_type=m.content_type)


@router.delete("/{material_id}")
def delete_material(material_id: int, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    m = _own(db, teacher, material_id)
    storage.delete(m.stored_name)
    db.delete(m)
    db.commit()
    return {"ok": True}
