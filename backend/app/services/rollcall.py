"""«Қатысу»: class journal + recognition of enrolled students on a class photo.

Recognition runs locally with OpenCV (services/faces.py); photos and face prints never leave this computer.
Only students with parental consent and at least one enrolled face photo can be recognized.
"""
import json
import logging
from datetime import datetime

import numpy as np

from ..database import SessionLocal
from ..models import FaceSample, RollCall, RollCallPhoto, StudentFace
from . import faces
from .storage_service import storage

log = logging.getLogger("rollcall")

MAX_SAMPLES = 5


def norm_name(name: str) -> str:
    return " ".join((name or "").split()).casefold()


def roster_list(rc: RollCall) -> list[str]:
    return [n for n in (rc.roster or "").split("\n") if n.strip()]


def marks_of(rc: RollCall) -> dict[str, str]:
    try:
        return json.loads(rc.marks or "{}")
    except ValueError:
        return {}


def photo_faces(p: RollCallPhoto) -> list[dict]:
    try:
        return json.loads(p.ai_faces or "[]")
    except ValueError:
        return []


# ------------------------------------------------------------------ enrollment
def faces_by_key(db, teacher_id: int) -> dict[str, StudentFace]:
    return {sf.student_key: sf for sf in db.query(StudentFace).filter_by(teacher_id=teacher_id)}


def get_or_create_face(db, teacher_id: int, name: str) -> StudentFace:
    key = norm_name(name)
    sf = db.query(StudentFace).filter_by(teacher_id=teacher_id, student_key=key).first()
    if not sf:
        sf = StudentFace(teacher_id=teacher_id, student_key=key, student_name=" ".join(name.split()))
        db.add(sf)
        db.flush()
    return sf


def delete_samples(sf: StudentFace) -> None:
    for s in list(sf.samples):
        storage.delete(s.thumb_name)
        sf.samples.remove(s)


def add_sample(db, sf: StudentFace, embedding, thumb_jpeg: bytes) -> FaceSample:
    if not sf.consent:
        raise faces.FaceError("no_consent")
    if len(sf.samples) >= MAX_SAMPLES:
        raise faces.FaceError("too_many_samples")
    thumb = storage.save_bytes(thumb_jpeg, f"faces/{sf.teacher_id}")
    sample = FaceSample(student_face_id=sf.id, embedding=json.dumps(faces.to_list(embedding)), thumb_name=thumb)
    sf.samples.append(sample)
    return sample


def enrolled_people(db, rc: RollCall) -> dict[str, list]:
    """Roster name -> list of face prints, for students with consent and samples."""
    by_key = faces_by_key(db, rc.teacher_id)
    people = {}
    for name in roster_list(rc):
        sf = by_key.get(norm_name(name))
        if sf and sf.consent and sf.samples:
            people[name] = [faces.from_list(json.loads(s.embedding)) for s in sf.samples]
    return people


# ------------------------------------------------------------------ summary + journal
def summary(rc: RollCall, db=None) -> dict:
    roster = roster_list(rc)
    marks = marks_of(rc)
    status = {n: marks.get(n, "present") for n in roster}
    done = [p for p in rc.photos if p.ai_status == "done"]
    recognized, unknown, faces_total = set(), 0, 0
    for p in done:
        for f in photo_faces(p):
            faces_total += 1
            if f.get("name"):
                recognized.add(f["name"])
            else:
                unknown += 1
    enrolled = 0
    if db is not None:
        by_key = faces_by_key(db, rc.teacher_id)
        enrolled = sum(1 for n in roster if (sf := by_key.get(norm_name(n))) and sf.consent and sf.samples)
    return {
        "total": len(roster),
        "present": sum(1 for v in status.values() if v in ("present", "late")),
        "late": sum(1 for v in status.values() if v == "late"),
        "absent": sum(1 for v in status.values() if v == "absent"),
        "photos": len(rc.photos),
        "busy": any(p.ai_status in ("pending", "checking") for p in rc.photos),
        "faces_total": faces_total if done else None,
        "recognized": sorted(recognized),
        "unknown_faces": unknown,
        "enrolled": enrolled,
    }


def apply_recognition(db, rc: RollCall) -> dict:
    """Write the photo result into the journal: recognized -> present, enrolled but not seen -> absent.
    Students without enrolled faces are left as they are (the teacher decides)."""
    s = summary(rc, db)
    recognized = set(s["recognized"])
    people = enrolled_people(db, rc)
    marks = marks_of(rc)
    for name in roster_list(rc):
        if name in recognized:
            if marks.get(name) != "late":
                marks[name] = "present"
        elif name in people:
            marks[name] = "absent"
    rc.marks = json.dumps(marks, ensure_ascii=False)
    return {"not_enrolled": [n for n in roster_list(rc) if n not in people]}


# ------------------------------------------------------------------ recognition job
def recognize_photo(photo_id: int) -> None:
    """Background job: find every face on the class photo and match it to enrolled students."""
    db = SessionLocal()
    try:
        p = db.get(RollCallPhoto, photo_id)
        if not p:
            return
        p.ai_status = "checking"
        db.commit()
        try:
            img = faces.load_image(storage.open_path(p.stored_name))
            found = faces.detect(img)
            prints = [faces.embed(img, f) for f in found]
            people = enrolled_people(db, p.roll_call)
            matches = faces.match(prints, people)
            result = []
            for f, (name, score) in zip(found, matches):
                level = "unknown" if not name else ("sure" if score >= faces.SURE_THRESHOLD else "check")
                result.append({"box": faces.box_1000(f, img), "det": faces.to_list(f), "name": name,
                               "score": round(score, 3), "level": level})
            p.ai_faces = json.dumps(result, ensure_ascii=False)
            p.ai_boxes = json.dumps([r["box"] for r in result])
            p.ai_count = len(result)
            p.ai_unclear = sum(1 for r in result if r["level"] != "sure")
            known = sum(1 for r in result if r["name"])
            p.ai_note = f"{len(result)} бет табылды, {known} оқушы танылды, {len(result) - known} бет танылмады."
            p.ai_status = "done"
        except faces.FaceError as e:
            p.ai_status, p.ai_note = "error", str(e)
        except Exception as e:
            log.exception("recognition failed")
            p.ai_status, p.ai_note = "error", str(e) or e.__class__.__name__
        db.commit()
    finally:
        db.close()


def assign_face(db, p: RollCallPhoto, index: int, name: str | None, learn: bool) -> None:
    """Teacher says who an unrecognized (or wrong) face is; optionally learn it as a new sample."""
    data = photo_faces(p)
    if not (0 <= index < len(data)):
        raise faces.FaceError("bad_face")
    if name:
        for i, f in enumerate(data):  # one person can only be on one face
            if i != index and f.get("name") == name:
                f["name"], f["level"] = None, "unknown"
    data[index]["name"] = name
    data[index]["level"] = "manual" if name else "unknown"
    p.ai_faces = json.dumps(data, ensure_ascii=False)
    if name and learn:
        sf = get_or_create_face(db, p.roll_call.teacher_id, name)
        if sf.consent and len(sf.samples) < MAX_SAMPLES:
            img = faces.load_image(storage.open_path(p.stored_name))
            det = np.asarray(data[index]["det"], dtype=np.float32)
            add_sample(db, sf, faces.embed(img, det), faces.thumbnail_jpeg(img, det))


def set_consent(db, teacher_id: int, name: str, consent: bool) -> StudentFace:
    sf = get_or_create_face(db, teacher_id, name)
    sf.consent = consent
    sf.consent_at = datetime.now() if consent else None
    if not consent:
        delete_samples(sf)  # no consent -> no biometric data kept
    return sf
