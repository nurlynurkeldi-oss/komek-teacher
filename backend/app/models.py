"""Database tables: teachers, lessons, assignments, materials (files)."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    school: Mapped[str | None] = mapped_column(String(200))
    subject: Mapped[str | None] = mapped_column(String(100))
    language: Mapped[str] = mapped_column(String(2), default="kk")  # kk | ru
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    lessons: Mapped[list["Lesson"]] = relationship(back_populates="teacher", cascade="all, delete-orphan")
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="teacher", cascade="all, delete-orphan")
    materials: Mapped[list["Material"]] = relationship(back_populates="teacher", cascade="all, delete-orphan")


class AuthToken(Base):
    """Simple bearer token for the prototype (replace with JWT later)."""
    __tablename__ = "auth_tokens"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    subject: Mapped[str | None] = mapped_column(String(100))
    grade: Mapped[str | None] = mapped_column(String(20))       # e.g. "7"
    topic: Mapped[str | None] = mapped_column(String(300))
    duration_min: Mapped[int] = mapped_column(Integer, default=45)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime)
    plan: Mapped[str | None] = mapped_column(Text)              # lesson plan (Markdown)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    teacher: Mapped[Teacher] = relationship(back_populates="lessons")
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="lesson")
    materials: Mapped[list["Material"]] = relationship(back_populates="lesson")


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[int | None] = mapped_column(ForeignKey("lessons.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(20), default="homework")  # homework | quiz | test
    content: Mapped[str | None] = mapped_column(Text)                  # task text students must solve
    due_date: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # AI checking workflow
    subject: Mapped[str | None] = mapped_column(String(100))
    grade: Mapped[str | None] = mapped_column(String(20))
    language: Mapped[str] = mapped_column(String(2), default="kk")
    max_score: Mapped[int] = mapped_column(Integer, default=10)
    analysis: Mapped[str | None] = mapped_column(Text)        # step 2: AI analysis of the material (JSON)
    analysis_status: Mapped[str] = mapped_column(String(20), default="none")  # none | running | done | error
    analysis_error: Mapped[str | None] = mapped_column(Text)
    share_code: Mapped[str | None] = mapped_column(String(16), unique=True, index=True)  # student link

    teacher: Mapped[Teacher] = relationship(back_populates="assignments")
    lesson: Mapped[Lesson | None] = relationship(back_populates="assignments")
    sources: Mapped[list["Material"]] = relationship(back_populates="assignment")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="assignment", cascade="all, delete-orphan")


class Submission(Base):
    """Step 3-5: one student's work for an assignment."""
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    student_name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | checking | checked | error
    error: Mapped[str | None] = mapped_column(Text)
    ai_score: Mapped[float | None] = mapped_column(Float)
    ai_result: Mapped[str | None] = mapped_column(Text)        # step 4: AI check details (JSON)
    teacher_score: Mapped[float | None] = mapped_column(Float)
    teacher_comment: Mapped[str | None] = mapped_column(Text)
    finalized: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime)

    assignment: Mapped[Assignment] = relationship(back_populates="submissions")
    files: Mapped[list["SubmissionFile"]] = relationship(back_populates="submission", cascade="all, delete-orphan")


class RollCall(Base):
    """«Қатысу»: one lesson's attendance journal (class list + marks + class photos)."""
    __tablename__ = "roll_calls"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))                  # e.g. "8А · Алгебра"
    lesson_date: Mapped[datetime] = mapped_column(DateTime)
    roster: Mapped[str | None] = mapped_column(Text)                 # one student per line
    marks: Mapped[str | None] = mapped_column(Text)                  # JSON {student: present|late|absent}
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    photos: Mapped[list["RollCallPhoto"]] = relationship(back_populates="roll_call", cascade="all, delete-orphan")


class RollCallPhoto(Base):
    """A photo of the whole class; the AI counts the people in it (no face recognition)."""
    __tablename__ = "roll_call_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    roll_call_id: Mapped[int] = mapped_column(ForeignKey("roll_calls.id", ondelete="CASCADE"), index=True)
    stored_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    ai_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|checking|done|no_ai|error
    ai_count: Mapped[int | None] = mapped_column(Integer)
    ai_unclear: Mapped[int | None] = mapped_column(Integer)          # partly hidden / uncertain people
    ai_boxes: Mapped[str | None] = mapped_column(Text)               # JSON [[ymin,xmin,ymax,xmax], ...] 0..1000
    ai_note: Mapped[str | None] = mapped_column(Text)
    ai_faces: Mapped[str | None] = mapped_column(Text)  # JSON [{box, det, name, score}] from face recognition

    roll_call: Mapped[RollCall] = relationship(back_populates="photos")


class StudentFace(Base):
    """A student whose face may be recognized. Biometric data is kept only with parental consent."""
    __tablename__ = "student_faces"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id", ondelete="CASCADE"), index=True)
    student_key: Mapped[str] = mapped_column(String(120), index=True)   # normalized name
    student_name: Mapped[str] = mapped_column(String(120))
    consent: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    samples: Mapped[list["FaceSample"]] = relationship(back_populates="student", cascade="all, delete-orphan")


class FaceSample(Base):
    """One enrolled face print (128 numbers) + a small face picture for the teacher."""
    __tablename__ = "face_samples"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_face_id: Mapped[int] = mapped_column(ForeignKey("student_faces.id", ondelete="CASCADE"), index=True)
    embedding: Mapped[str] = mapped_column(Text)        # JSON list of 128 floats
    thumb_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    student: Mapped[StudentFace] = relationship(back_populates="samples")


class SubmissionFile(Base):
    __tablename__ = "submission_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), index=True)
    original_name: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255), unique=True)
    content_type: Mapped[str | None] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)

    submission: Mapped[Submission] = relationship(back_populates="files")


class Material(Base):
    """Metadata of an uploaded file; the bytes live in File Storage."""
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[int | None] = mapped_column(ForeignKey("lessons.id", ondelete="SET NULL"))
    assignment_id: Mapped[int | None] = mapped_column(ForeignKey("assignments.id", ondelete="SET NULL"))  # step 1 source
    original_name: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255), unique=True)
    content_type: Mapped[str | None] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    teacher: Mapped[Teacher] = relationship(back_populates="materials")
    lesson: Mapped[Lesson | None] = relationship(back_populates="materials")
    assignment: Mapped["Assignment | None"] = relationship(back_populates="sources")
