"""Users: register, login, profile."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuthToken, Teacher
from ..schemas import LoginIn, RegisterIn, TeacherOut, TeacherUpdate, TokenOut
from ..services.security import current_teacher, hash_password, new_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.strip().lower()
    if db.query(Teacher).filter_by(email=email).first():
        raise HTTPException(400, "Email already registered")
    teacher = Teacher(
        full_name=data.full_name, email=email, password_hash=hash_password(data.password),
        school=data.school, subject=data.subject, language=data.language,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return TokenOut(token=new_token(db, teacher), teacher=teacher)


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter_by(email=data.email.strip().lower()).first()
    if not teacher or not verify_password(data.password, teacher.password_hash):
        raise HTTPException(401, "Wrong email or password")
    return TokenOut(token=new_token(db, teacher), teacher=teacher)


@router.post("/logout")
def logout(teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    db.query(AuthToken).filter_by(teacher_id=teacher.id).delete()
    db.commit()
    return {"ok": True}


@router.get("/me", response_model=TeacherOut)
def me(teacher: Teacher = Depends(current_teacher)):
    return teacher


@router.patch("/me", response_model=TeacherOut)
def update_me(data: TeacherUpdate, teacher: Teacher = Depends(current_teacher), db: Session = Depends(get_db)):
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(teacher, key, value)
    db.commit()
    db.refresh(teacher)
    return teacher
