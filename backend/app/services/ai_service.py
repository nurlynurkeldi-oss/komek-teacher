"""AI API: generates lesson plans and assignments.

AI_MODE=mock           -> returns a template (no API key needed, good for UI work).
AI_MODE=claude/gemini  -> calls that provider (see llm.py).
"""
from fastapi import HTTPException

from . import llm

LANG_NAME = {"kk": "Kazakh (қазақ тілі)", "ru": "Russian (русский язык)"}

SYSTEM_PROMPT = (
    "You are an experienced methodologist helping school teachers in Kazakhstan. "
    "Follow the state curriculum (ГОСО / МЖМБС) style. Write clear, practical, ready-to-use "
    "material in Markdown. Always answer entirely in the language the teacher asks for."
)


def _lesson_plan_prompt(r) -> str:
    return (
        f"Write a lesson plan in {LANG_NAME[r.language]}.\n"
        f"Subject: {r.subject}\nGrade: {r.grade}\nTopic: {r.topic}\n"
        f"Duration: {r.duration_min} minutes\n"
        f"Teacher notes: {r.notes or '-'}\n\n"
        "Include: learning objectives, expected results, materials, lesson stages with "
        "timing (organizational moment, warm-up, new material, practice, reflection), "
        "differentiation ideas, assessment criteria, and homework."
    )


def _assignment_prompt(r) -> str:
    return (
        f"Create a {r.kind} in {LANG_NAME[r.language]}.\n"
        f"Subject: {r.subject}\nGrade: {r.grade}\nTopic: {r.topic}\n"
        f"Number of tasks: {r.count}\nDifficulty: {r.difficulty}\n\n"
        "Number each task. For multiple-choice questions give options A-D. "
        "Put an answer key at the end under a separate heading."
    )


def _call_ai(user_prompt: str) -> str:
    """Claude or Gemini, depending on AI_MODE (see llm.py)."""
    try:
        return llm.text(SYSTEM_PROMPT, user_prompt)
    except llm.AIError as e:
        raise HTTPException(502, str(e))


# ---------- mock templates ----------
def _mock_lesson_plan(r) -> str:
    if r.language == "ru":
        return (
            f"# План урока: {r.topic}\n\n**Предмет:** {r.subject} · **Класс:** {r.grade} · "
            f"**Длительность:** {r.duration_min} мин\n\n## Цели обучения\n- ...\n\n"
            "## Ход урока\n1. Организационный момент (3 мин)\n2. Актуализация знаний (7 мин)\n"
            "3. Новый материал (15 мин)\n4. Практика (15 мин)\n5. Рефлексия (5 мин)\n\n"
            "## Домашнее задание\n- ...\n\n_(демо-режим: AI_MODE=mock)_"
        )
    return (
        f"# Сабақ жоспары: {r.topic}\n\n**Пән:** {r.subject} · **Сынып:** {r.grade} · "
        f"**Ұзақтығы:** {r.duration_min} мин\n\n## Оқу мақсаттары\n- ...\n\n"
        "## Сабақ барысы\n1. Ұйымдастыру кезеңі (3 мин)\n2. Білімді өзектендіру (7 мин)\n"
        "3. Жаңа материал (15 мин)\n4. Практика (15 мин)\n5. Рефлексия (5 мин)\n\n"
        "## Үй тапсырмасы\n- ...\n\n_(демо режим: AI_MODE=mock)_"
    )


def _mock_assignment(r) -> str:
    head = "Тапсырма" if r.language == "kk" else "Задание"
    title = f"# {r.topic} — {r.kind}\n\n"
    items = "\n".join(f"{i}. {head} {i} ...\n   A) ...  B) ...  C) ...  D) ..." for i in range(1, r.count + 1))
    key = "## Жауаптар" if r.language == "kk" else "## Ответы"
    return f"{title}{items}\n\n{key}\n- ...\n\n_(AI_MODE=mock)_"


# ---------- public API ----------
def generate_lesson_plan(req) -> tuple[str, str]:
    if llm.provider():
        return _call_ai(_lesson_plan_prompt(req)), llm.provider()
    return _mock_lesson_plan(req), "mock"


def generate_assignment(req) -> tuple[str, str]:
    if llm.provider():
        return _call_ai(_assignment_prompt(req)), llm.provider()
    return _mock_assignment(req), "mock"
