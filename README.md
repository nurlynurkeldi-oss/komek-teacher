# Komek Teacher — мұғалімге көмектесу (AI платформа, прототип)

Мұғалімнің күнделікті жұмысын автоматтандыратын веб-платформаның қаңқасы.
Интерфейс: **қазақша / орысша**.

## Архитектура

```
Браузер (frontend/: HTML + CSS + JS, KZ/RU)
        │  REST API (JSON)
        ▼
Backend (backend/app: FastAPI)
   ├── routers/auth.py         пайдаланушылар: тіркелу, кіру, профиль
   ├── routers/lessons.py      сабақтар + басты бет статистикасы
   ├── routers/assignments.py  тапсырмалар
   ├── routers/materials.py    материалдар: жүктеу / жүктеп алу / өшіру
   ├── routers/ai.py           AI: сабақ жоспары, тапсырма генерациясы
   └── services/
        ├── ai_service.py      AI API (mock режим немесе Claude API)
        ├── storage_service.py File Storage (қазір жергілікті диск)
        └── security.py        құпиясөз хэші, токен
        │
        ├── Database: SQLite (backend/data/app.db) → кейін PostgreSQL
        └── Files:    backend/data/uploads/<teacher_id>/...
```

## Дерекқор кестелері

| Кесте | Мазмұны |
|---|---|
| `teachers` | мұғалімдер: аты-жөні, email, мектеп, пән, интерфейс тілі |
| `auth_tokens` | кіру токендері (прототип) |
| `lessons` | сабақтар: атауы, пән, сынып, тақырып, уақыты, жоспары |
| `assignments` | тапсырмалар: түрі (homework/quiz/test), мазмұны, мерзімі, сабаққа байланыс |
| `materials` | жүктелген файлдардың мета-деректері (файлдың өзі File Storage-та) |

## Іске қосу (Windows / PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python download_models.py
copy .env.example .env
.\.venv\Scripts\uvicorn app.main:app --reload
```

Браузерде: http://127.0.0.1:8000 — API құжаттамасы: http://127.0.0.1:8000/docs

## Render-ге орналастыру

1. GitHub-тағы репозиторийді Render-ге қосыңыз: **New → Blueprint** → осы репозиторий ([render.yaml](render.yaml) өзі оқылады).
2. Render сұрағанда **GEMINI_API_KEY** мәнін енгізіңіз (кілт GitHub-та сақталмайды).
3. Build: `pip install -r requirements.txt && python download_models.py`,
   Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
4. Тегін (free) жоспарда сервер қайта қосылғанда база мен жүктелген файлдар өшеді. Деректерді сақтау үшін
   render.yaml-дағы `disk` бөлігін ашып, `plan: starter` қойыңыз (`DATABASE_URL`, `STORAGE_DIR` → `/var/data`).

⚠ `backend/.env` (кілттер) және `backend/data/` (оқушылардың деректері, фотолары, бет үлгілері)
GitHub-қа ешқашан жүктелмейді — [.gitignore](.gitignore).

## AI режимі

`backend/.env` ішінде:
- `AI_MODE=mock` — API кілтсіз үлгі мәтін қайтарады (әзірлеу үшін).
- `AI_MODE=claude` + `ANTHROPIC_API_KEY=...` — Claude API арқылы нақты генерация.

## Тапсырмаларды ЖИ арқылы тексеру (5 қадам)

`Тапсырмалар → тапсырманы ашу`:

1. **Мұғалім** тақырып материалын жүктейді (PDF, DOCX, PPTX, TXT, фото) және тапсырма мәтінін жазады.
2. **ЖИ** материалды талдайды: негізгі мазмұн, формулалар, терминдер, дұрыс жауаптар, бағалау критерийлері (балл қосындысы = ең жоғары балл).
3. **Оқушы** сілтеме арқылы (`/#/s/<код>`, логинсіз) дәптер фотосын не файлын жүктейді; немесе мұғалім өзі жүктейді.
4. **ЖИ** әр жұмысты автоматты тексереді: формула, шығару жолы, есептеулер, соңғы жауап, қателер, кері байланыс.
5. **Мұғалім** нәтижелер кестесінде ЖИ бағасын өзгертіп, соңғы бағаны бекітеді; CSV-ге жүктейді.

Код: [routers/checking.py](backend/app/routers/checking.py), [routers/public.py](backend/app/routers/public.py),
[services/checker.py](backend/app/services/checker.py), [services/documents.py](backend/app/services/documents.py),
[frontend/js/checking.js](frontend/js/checking.js).

### ЖИ-ды қосу (Gemini немесе Claude)

`backend/.env` файлында:

```
AI_MODE=gemini
GEMINI_API_KEY=кілтіңіз        # https://aistudio.google.com/apikey
GEMINI_MODEL=gemini-3.5-flash  # gemini-2.5-flash жаңа аккаунттарға жабық
```

немесе Claude үшін `AI_MODE=claude` + `ANTHROPIC_API_KEY=...`. ЖИ қосылмаса (`AI_MODE=mock`), жұмыстар
қабылданады, бағаны мұғалім өзі қояды — ойдан құралған баға шықпайды.
Провайдер коды: [services/llm.py](backend/app/services/llm.py).

## Қатысу (сабаққа қатысуды тексеру)

«Журнал + бет тану» тәсілі. Бет тану **осы компьютерде** OpenCV арқылы жүреді (YuNet + SFace модельдері),
фотолар мен бет үлгілері ешқайда жіберілмейді.

1. `Қатысу → + Жаңа сабақ`: сынып/сабақ атауы, күні, оқушылар тізімі (немесе «Бұрынғы тізімді алу»).
2. **Беттерді тіркеу** (бір рет): әр оқушыға «Ата-ана келісімі бар» белгісі → 2–3 бет фотосы. Толық фото
   сақталмайды, тек 128 саннан тұратын бет үлгісі мен кішкентай сурет. Келісім алынса — деректер өшеді.
3. Сабақта мұғалім сыныпты бір рет суретке түсіреді → әр беттің үстінде аты шығады
   (жасыл — сенімді, сары — тексеріңіз, қызыл «?» — танылмады; бетті басып, кім екенін көрсетуге болады).
4. «✓ Нәтижені журналға жазу»: танылғандар — Келді, беті тіркелген бірақ фотода жоқтар — Келмеді.
5. Журналда бір басумен түзету, CSV. «Барлық бет деректерін өшіру» — оқу жылы соңында.

Модельдер `backend/models/face/` ішінде болуы керек (OpenCV Zoo) — `python download_models.py` жүктейді
(Render-де build кезінде өзі орындалады).

⚠ Бет суреті — биометриялық дерек: ата-ананың жазбаша келісімі керек (ҚР «Дербес деректер туралы» заңы).

Код: [services/faces.py](backend/app/services/faces.py), [services/rollcall.py](backend/app/services/rollcall.py),
[routers/rollcall.py](backend/app/routers/rollcall.py), [frontend/js/attendance.js](frontend/js/attendance.js).

## Келесі қадамдар (идеялар)

- JWT авторизация, рөлдер (мұғалім / әкімші)
- Alembic миграциялары, PostgreSQL
- S3/MinIO файл қоймасы
- Жүктелген құжаттан тест жасау, жұмыстарды AI арқылы тексеру, кесте
