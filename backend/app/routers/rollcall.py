"""«Қатысу» API: journal, face enrollment (with consent) and class-photo recognition. Teacher only."""
import json

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import FaceSample, RollCall, RollCallPhoto, StudentFace, Teacher
from ..schemas import RollCallIn, RollCallMarksIn
from ..services import faces
from ..services import rollcall as rc_service
from ..services.security import current_teacher
from ..services.storage_service import storage

router = APIRouter(prefix="/api/rollcall", tags=["attendance"])

PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
MAX_PHOTOS = 3


class ConsentIn(BaseModel):
    student_name: str = Field(min_length=1, max_length=120)
    consent: bool


class AssignIn(BaseModel):
    student_name: str | None = Field(None, max_length=120)  # None = "not a student / unknown"
    learn: bool = True


def _own(db: Session, teacher: Teacher, rc_id: int) -> RollCall:
    rc = db.get(RollCall, rc_id)
    if not rc or rc.teacher_id != teacher.id:
        raise HTTPException(404, "Not found")
    return rc


def _own_photo(db: Session, teacher: Teacher, photo_id: int) -> RollCallPhoto:
    p = db.get(RollCallPhoto, photo_id)
    if not p or p.roll_call.teacher_id != teacher.id:
        raise HTTPException(404, "Photo not found")
    return p


def _clean_roster(names: list[str]) -> str:
    seen, out = set(), []
    for n in names:
        name = " ".join((n or "").split())[:120]
        if name and name.casefold() not in seen:
            seen.add(name.casefold())
            out.append(name)
    return "\n".join(out)


def _out(db: Session, rc: RollCall, full: bool = False) -> dict:
    data = {"id": rc.id, "title": rc.title, "lesson_date": rc.lesson_date, "created_at": rc.created_at,
            **rc_service.summary(rc, db)}
    if full:
        marks = rc_service.marks_of(rc)
        by_key = rc_service.faces_by_key(db, rc.teacher_id)
        data["roster"] = []
        for n in rc_service.roster_list(rc):
            sf = by_key.get(rc_service.norm_name(n))
            data["roster"].append({
                "name": n, "status": marks.get(n, "present"),
                "consent": bool(sf and sf.consent),
                "samples": [s.id for s in sf.samples] if sf else [],
            })
        data["photo_list"] = [
            {"id": p.id, "ai_status": p.ai_status, "ai_note": p.ai_note, "ai_count": p.ai_count,
             "faces": [{k: f[k] for k in ("box", "name", "score", "level")} for f in rc_service.photo_faces(p)],
             "created_at": p.created_at}
            for p in sorted(rc.photos, key=lambda x: x.created_at)
        ]
        data["models_ready"] = faces.models_ready()
    return data


# ------------------------------------------------------------ journal
@router.get("")
def list_rollcalls(teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    rows = db.query(RollCall).filter_by(teacher_id=teacher.id).order_by(RollCall.lesson_date.desc(), RollCall.id.desc()).all()
    return [_out(db, r) for r in rows]


@router.get("/rosters")
def recent_rosters(teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    """Class lists used before, so the teacher does not retype them every lesson."""
    rows = db.query(RollCall).filter_by(teacher_id=teacher.id).order_by(RollCall.created_at.desc()).limit(50).all()
    seen, out = set(), []
    for r in rows:
        if r.title not in seen and r.roster:
            seen.add(r.title)
            out.append({"title": r.title, "roster": rc_service.roster_list(r)})
    return out


@router.post("")
def create_rollcall(data: RollCallIn, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    roster = _clean_roster(data.roster)
    if not roster:
        raise HTTPException(400, "empty_roster")
    rc = RollCall(teacher_id=teacher.id, title=data.title.strip(), lesson_date=data.lesson_date, roster=roster, marks="{}")
    db.add(rc)
    db.commit()
    db.refresh(rc)
    return _out(db, rc)


@router.get("/{rc_id}")
def get_rollcall(rc_id: int, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    return _out(db, _own(db, teacher, rc_id), full=True)


@router.put("/{rc_id}")
def update_rollcall(rc_id: int, data: RollCallIn, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    rc = _own(db, teacher, rc_id)
    roster = _clean_roster(data.roster)
    if not roster:
        raise HTTPException(400, "empty_roster")
    rc.title, rc.lesson_date, rc.roster = data.title.strip(), data.lesson_date, roster
    names = set(roster.split("\n"))
    rc.marks = json.dumps({k: v for k, v in rc_service.marks_of(rc).items() if k in names}, ensure_ascii=False)
    db.commit()
    return _out(db, rc, full=True)


@router.put("/{rc_id}/marks")
def set_marks(rc_id: int, data: RollCallMarksIn, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    rc = _own(db, teacher, rc_id)
    names = set(rc_service.roster_list(rc))
    unknown = [n for n in data.marks if n not in names]
    if unknown:
        raise HTTPException(400, f"Not on the list: {', '.join(unknown)}")
    marks = rc_service.marks_of(rc)
    marks.update(data.marks)
    rc.marks = json.dumps(marks, ensure_ascii=False)
    db.commit()
    return _out(db, rc, full=True)


@router.post("/{rc_id}/apply")
def apply_result(rc_id: int, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    """Put the recognition result into the journal."""
    rc = _own(db, teacher, rc_id)
    info = rc_service.apply_recognition(db, rc)
    db.commit()
    return {**_out(db, rc, full=True), **info}


@router.delete("/{rc_id}")
def delete_rollcall(rc_id: int, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    rc = _own(db, teacher, rc_id)
    for p in rc.photos:
        storage.delete(p.stored_name)
    db.delete(rc)
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------ class photos
@router.post("/{rc_id}/photos")
async def add_photo(rc_id: int, background: BackgroundTasks, file: UploadFile = File(...),
                    teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    rc = _own(db, teacher, rc_id)
    if len(rc.photos) >= MAX_PHOTOS:
        raise HTTPException(400, "too_many_photos")
    stored, _size = await storage.save(file, f"rollcall/{rc.id}", PHOTO_EXTENSIONS)
    p = RollCallPhoto(roll_call_id=rc.id, stored_name=stored)
    db.add(p)
    db.commit()
    background.add_task(rc_service.recognize_photo, p.id)
    return {"id": p.id}


@router.get("/photos/{photo_id}")
def photo_file(photo_id: int, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    p = _own_photo(db, teacher, photo_id)
    return FileResponse(storage.open_path(p.stored_name), media_type="image/jpeg")


@router.post("/photos/{photo_id}/recount")
def recount(photo_id: int, background: BackgroundTasks, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    p = _own_photo(db, teacher, photo_id)
    p.ai_status = "pending"
    db.commit()
    background.add_task(rc_service.recognize_photo, p.id)
    return {"ok": True}


@router.post("/photos/{photo_id}/faces/{index}")
async def assign(photo_id: int, index: int, data: AssignIn, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    p = _own_photo(db, teacher, photo_id)
    name = data.student_name
    if name and name not in rc_service.roster_list(p.roll_call):
        raise HTTPException(400, "not_on_list")
    try:
        await run_in_threadpool(rc_service.assign_face, db, p, index, name, data.learn)
    except faces.FaceError as e:
        raise HTTPException(400, str(e))
    db.commit()
    return {"ok": True}


@router.delete("/photos/{photo_id}")
def delete_photo(photo_id: int, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    p = _own_photo(db, teacher, photo_id)
    storage.delete(p.stored_name)
    db.delete(p)
    db.commit()
    return {"ok": True}


# ------------------------------------------------------------ face enrollment (biometric data, consent required)
@router.put("/faces/consent")
def set_consent(data: ConsentIn, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    sf = rc_service.set_consent(db, teacher.id, data.student_name, data.consent)
    db.commit()
    return {"consent": sf.consent, "samples": [s.id for s in sf.samples]}


@router.post("/faces/samples")
async def add_face_sample(student_name: str = Form(...), file: UploadFile = File(...),
                          teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    sf = rc_service.get_or_create_face(db, teacher.id, student_name)
    if not sf.consent:
        raise HTTPException(400, "no_consent")
    stored, _ = await storage.save(file, f"faces/{teacher.id}/tmp", PHOTO_EXTENSIONS)
    try:
        embedding, thumb = await run_in_threadpool(faces.enroll_from_photo, storage.open_path(stored))
        sample = rc_service.add_sample(db, sf, embedding, thumb)
    except faces.FaceError as e:
        raise HTTPException(400, str(e))
    finally:
        storage.delete(stored)  # the full portrait is not kept, only the face print + a small thumbnail
    db.commit()
    return {"id": sample.id, "samples": [s.id for s in sf.samples]}


@router.get("/faces/samples/{sample_id}")
def face_thumb(sample_id: int, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    s = db.get(FaceSample, sample_id)
    if not s or s.student.teacher_id != teacher.id:
        raise HTTPException(404, "Not found")
    return FileResponse(storage.open_path(s.thumb_name), media_type="image/jpeg")


@router.delete("/faces/samples/{sample_id}")
def delete_face_sample(sample_id: int, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    s = db.get(FaceSample, sample_id)
    if not s or s.student.teacher_id != teacher.id:
        raise HTTPException(404, "Not found")
    storage.delete(s.thumb_name)
    db.delete(s)
    db.commit()
    return {"ok": True}


@router.delete("/faces/all")
def delete_all_faces(teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    """Wipe every face print and consent record of this teacher (e.g. at the end of the school year)."""
    rows = db.query(StudentFace).filter_by(teacher_id=teacher.id).all()
    for sf in rows:
        rc_service.delete_samples(sf)
        db.delete(sf)
    db.commit()
    return {"deleted": len(rows)}
