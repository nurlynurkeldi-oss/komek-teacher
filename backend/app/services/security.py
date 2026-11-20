"""Password hashing and current-teacher lookup (prototype-level auth)."""
import hashlib
import hmac
import secrets

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuthToken, Teacher

_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _ITERATIONS).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    salt, digest = stored.split("$", 1)
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _ITERATIONS).hex()
    return hmac.compare_digest(check, digest)


def new_token(db: Session, teacher: Teacher) -> str:
    token = secrets.token_hex(32)
    db.add(AuthToken(token=token, teacher_id=teacher.id))
    db.commit()
    return token


def current_teacher(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Teacher:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Not authenticated")
    row = db.get(AuthToken, authorization.split(" ", 1)[1].strip())
    if not row:
        raise HTTPException(401, "Invalid token")
    teacher = db.get(Teacher, row.teacher_id)
    if not teacher:
        raise HTTPException(401, "Invalid token")
    return teacher
