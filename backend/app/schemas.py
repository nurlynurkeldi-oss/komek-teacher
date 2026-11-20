"""Request/response shapes for the API."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Lang = Literal["kk", "ru"]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- Auth / teachers ----
class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=6, max_length=128)
    school: str | None = None
    subject: str | None = None
    language: Lang = "kk"


class LoginIn(BaseModel):
    email: str
    password: str


class TeacherOut(ORM):
    id: int
    full_name: str
    email: str
    school: str | None
    subject: str | None
    language: str
    created_at: datetime


class TeacherUpdate(BaseModel):
    full_name: str | None = None
    school: str | None = None
    subject: str | None = None
    language: Lang | None = None


class TokenOut(BaseModel):
    token: str
    teacher: TeacherOut


# ---- Lessons ----
class LessonIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    subject: str | None = None
    grade: str | None = None
    topic: str | None = None
    duration_min: int = 45
    scheduled_at: datetime | None = None
    plan: str | None = None


class LessonOut(ORM, LessonIn):
    id: int
    created_at: datetime


# ---- Assignments ----
class AssignmentIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    kind: Literal["homework", "quiz", "test"] = "homework"
    content: str | None = None
    lesson_id: int | None = None
    due_date: datetime | None = None
    subject: str | None = None
    grade: str | None = None
    language: Lang = "kk"
    max_score: int = Field(10, ge=1, le=100)


class AssignmentOut(ORM, AssignmentIn):
    id: int
    created_at: datetime
    analysis_status: str = "none"
    share_code: str | None = None


# ---- AI checking workflow ----
class RubricItem(BaseModel):
    criterion: str
    description: str
    points: float


class MaterialAnalysis(BaseModel):
    """Step 2 output: what the AI understood from the teacher's material."""
    summary: str
    key_concepts: list[str]
    formulas: list[str]
    terms: list[str]
    expected_answers: list[str]   # what a correct answer to each task should contain
    rubric: list[RubricItem]      # points must add up to the assignment's max_score


class CriterionScore(BaseModel):
    criterion: str
    max_points: float
    points: float
    comment: str


class AspectCheck(BaseModel):
    status: Literal["correct", "partial", "incorrect", "missing"]
    comment: str


class Mistake(BaseModel):
    where: str        # task number / line where the mistake is
    what: str         # what is wrong
    correct: str      # how it should be


class GradingResult(BaseModel):
    """Step 4 output: AI check of one student's work."""
    recognized_text: str          # transcription of the student's handwriting / file
    formula_usage: AspectCheck
    solution_path: AspectCheck
    calculations: AspectCheck
    final_answer: AspectCheck
    criteria: list[CriterionScore]
    mistakes: list[Mistake]
    total_score: float
    feedback_for_student: str
    note_for_teacher: str
    confidence: Literal["high", "medium", "low"]  # low = photo unreadable / off-topic work


# ---- Attendance («Қатысу»): journal + class photo head-count ----
class RollCallIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    lesson_date: datetime
    roster: list[str] = Field(default_factory=list, max_length=300)


class RollCallMarksIn(BaseModel):
    marks: dict[str, Literal["present", "late", "absent"]]


class PersonBox(BaseModel):
    box_2d: list[int]   # [ymin, xmin, ymax, xmax], each 0..1000 of the image size


class ClassPhotoCount(BaseModel):
    """AI answer for a class photo: how many people (students) are in it."""
    people_count: int
    unclear_count: int          # partly hidden / blurry people, included in people_count
    boxes: list[PersonBox]      # one box around each counted person's head/face
    note: str                   # short note in Kazakh


class TeacherGradeIn(BaseModel):
    teacher_score: float | None = None
    teacher_comment: str | None = None
    finalized: bool = False


# ---- Materials ----
class MaterialOut(ORM):
    id: int
    lesson_id: int | None
    original_name: str
    content_type: str | None
    size_bytes: int
    created_at: datetime


# ---- AI ----
class LessonPlanRequest(BaseModel):
    subject: str
    grade: str
    topic: str
    duration_min: int = 45
    language: Lang = "kk"
    notes: str | None = None
    save: bool = False  # save result as a Lesson


class AssignmentRequest(BaseModel):
    subject: str
    grade: str
    topic: str
    kind: Literal["homework", "quiz", "test"] = "quiz"
    count: int = Field(5, ge=1, le=30)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    language: Lang = "kk"
    lesson_id: int | None = None
    save: bool = False  # save result as an Assignment


class AIResult(BaseModel):
    content: str
    mode: str                 # "mock" or "claude"
    saved_id: int | None = None


class DashboardOut(BaseModel):
    lessons: int
    assignments: int
    materials: int
    upcoming: list[LessonOut]
