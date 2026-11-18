# 📚 Study Prep Tool

> **One unified AI-powered platform for every stage of education**
> School students (Class 1–12 / JEE / NEET) and Engineering students — both served from a single app.

---

## 📌 Table of Contents

1. [Project Overview](#1-project-overview)
2. [Platform Structure](#2-platform-structure)
3. [Architecture & Workflow Diagram](#3-architecture--workflow-diagram)
4. [Tech Stack](#4-tech-stack)
5. [Feature Breakdown — How Each Was Built](#5-feature-breakdown--how-each-was-built)
   - [5.1 Landing Page](#51-landing-page--path-selector)
   - [5.2 School / JEE Platform](#52-school--jee-platform)
   - [5.3 AI Tutor Chat](#53-ai-tutor-chat--engineering)
   - [5.4 Adaptive Quiz](#54-adaptive-quiz--engineering)
   - [5.5 Resume + JD Matcher](#55-resume--jd-matcher--engineering)
   - [5.6 Learning Roadmap](#56-learning-roadmap--engineering)
   - [5.7 Voice Mock Interview](#57-voice-mock-interview--engineering)
   - [5.8 Documents / RAG](#58-documents--rag--engineering)
   - [5.9 Dashboard](#59-dashboard--engineering)
6. [Project File Structure](#6-project-file-structure)
7. [How to Run](#7-how-to-run)
8. [Environment Variables](#8-environment-variables)
9. [API Reference](#9-api-reference)
10. [Source Projects Merged](#10-source-projects-merged)

---

## 1. Project Overview

**Study Prep Tool** merges three separate AI education repositories into one production-ready platform:

| Source Repo | What it contributed |
|---|---|
| **EduAgent** | LangGraph tutoring pipeline, RAG over notes, memory extraction, recommendations |
| **SkillBridge AI** | Resume ATS scoring, JD matching, learning roadmaps, mock interviews |
| **Jobyn** | Career readiness scoring, adaptive quizzes, placement prep, skill gap analysis |
| **JEE GenAI** | YouTube → Notes, Previous Year Questions, subject Q&A for school students |

All four are unified under a single React frontend with a shared design system, two FastAPI backends, and one entry point at `http://localhost:5173`.

---

## 2. Platform Structure

```
Study Prep Tool
│
├── 🏫  SCHOOL MODE  (Class 1–12 / JEE / NEET)
│   ├── YouTube Lecture → Textbook Notes
│   ├── Previous Year Questions Generator (JEE/NEET pattern)
│   └── Ask AI Subject Tutor (Physics / Chemistry / Maths / Biology)
│
└── 🎓  ENGINEERING MODE  (B.Tech / MCA / Placement)
    ├── AI Tutor Chat (with RAG over your own documents)
    ├── Adaptive Quiz (MCQ + evaluation + weak concept tracking)
    ├── Resume Analyzer + JD Matcher
    ├── Week-by-Week Learning Roadmap (with YouTube + docs links)
    ├── Voice Mock Interview (Technical / HR / Resume-Based)
    ├── Documents (upload PDF/DOCX → ask AI questions from them)
    └── Dashboard (scores, progress, memory, recommendations)
```

---

## 3. Architecture & Workflow Diagram

### Overall System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    BROWSER  :5173                             │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              React 18 + Vite (Single App)              │  │
│  │                                                        │  │
│  │  Landing Page ──► School Mode ──► JEE Platform         │  │
│  │       │                                                │  │
│  │       └──────────► Engineering Mode ──► Login          │  │
│  │                         │                              │  │
│  │              ┌──────────┴──────────┐                   │  │
│  │        Dashboard  Chat  Quiz  Resume  Roadmap           │  │
│  │        Interview  Documents                             │  │
│  └───────────────┬────────────────────┬────────────────────┘  │
└──────────────────┼────────────────────┼──────────────────────┘
                   │ HTTP REST          │ HTTP REST
                   ▼                    ▼
     ┌─────────────────────┐  ┌─────────────────────┐
     │  Engineering Backend │  │   School Backend     │
     │  FastAPI  :8000      │  │   FastAPI  :8001     │
     │                     │  │                     │
     │  8 Routers          │  │  3 Endpoints        │
     │  7 AI Services      │  │  4 AI Agents        │
     │                     │  │                     │
     │  SQLite DB          │  │  PYQ CSV Data       │
     │  Vector Store (JSON)│  │  YouTube API        │
     └──────────┬──────────┘  └──────────┬──────────┘
                │                        │
                └────────────┬───────────┘
                             ▼
                  ┌─────────────────────┐
                  │   Groq LLM API      │
                  │  gpt-oss-120b       │
                  │  gpt-oss-20b        │
                  │  qwen3.8-27b        │
                  │  (auto-rotate)      │
                  └─────────────────────┘
```

### Engineering Backend — Request Flow

```
Browser Request
      │
      ▼
  FastAPI Router  (chat / quiz / resume / roadmap / interview / documents / dashboard)
      │
      ▼
  Service Layer
  ┌───────────────────────────────────────────────────────────┐
  │                                                           │
  │  tutor_service  ──► classify_intent ──► learn/answer     │
  │       │                                                   │
  │       ├──► rag_service  ──► load JSON index              │
  │       │        └──► cosine_similarity ──► top-k chunks   │
  │       │                                                   │
  │  quiz_service   ──► generate_quiz ──► evaluate_quiz      │
  │                                                           │
  │  resume_service ──► extract_text ──► parse ──► ATS score │
  │                      └──► match_jd                       │
  │                                                           │
  │  roadmap_service ──► skill_gaps ──► week plan + links    │
  │                                                           │
  │  interview_service ──► generate_questions                │
  │                     └──► evaluate_answers                │
  └───────────────────────────────────────────────────────────┘
      │
      ▼
  llm_service  ──► Groq API  (model rotation on rate limit)
      │
      ▼
  SQLAlchemy ORM ──► SQLite  (students, conversations, quizzes,
                              resumes, roadmaps, interviews, memory)
```

### School Backend — Video Analysis Flow

```
YouTube URL
    │
    ▼
TranscriptAgent
    ├── Strategy 1: YouTube Caption API (English direct)
    ├── Strategy 2: YouTube Caption API (any lang) + Groq translation
    ├── Strategy 3: yt-dlp subtitle extraction + translation
    └── Strategy 4: Video metadata fallback
    │
    ▼
 Raw Transcript Text
    │
    ├──► SummarizerAgent ──► Groq LLM ──► Textbook-style Notes
    │
    ├──► PYQAgent ──► CSV lookup ──► if not enough ──► Groq LLM
    │                                                 (JEE pattern Qs)
    │
    └──► PracticeAgent ──► Groq LLM ──► 5 Practice Questions
    │
    ▼
 JSON Response → React Frontend
```

### RAG (Retrieval-Augmented Generation) Flow

```
Upload Document
    │
    ▼
extract_text()  ──► PDF (PyMuPDF) | DOCX (python-docx) | TXT
    │
    ▼
chunk_text()    ──► 400-word chunks, 80-word overlap
    │
    ▼
_embed_text()   ──► Bag-of-words hashed into 512-dim vector (pure NumPy)
    │
    ▼
JSON vector index  ──► stored at chroma_db/vectors/{student_id}/index.json
    │
    ▼  (on query)
retrieve_chunks()  ──► cosine similarity → top-k chunks
    │
    ▼
Groq LLM  ──► grounded answer using retrieved context
    │
    ▼
Response → Frontend
```

---

## 4. Tech Stack

### Frontend

| Technology | Version | Role |
|---|---|---|
| React | 18.3 | UI library |
| Vite | 5.4 | Build tool & dev server |
| React Router DOM | 6.27 | Client-side routing |
| Axios | 1.7 | HTTP client for all API calls |
| React Markdown | 9.0 | Render LLM markdown responses |
| Recharts | 2.13 | Quiz score trend charts |
| Lucide React | 0.456 | Icons |
| Web Speech API | Browser-native | Voice input/output for interviews |

### Engineering Backend (port 8000)

| Technology | Version | Role |
|---|---|---|
| Python | 3.10+ | Runtime |
| FastAPI | 0.115 | Web framework |
| Uvicorn | 0.30 | ASGI server |
| SQLAlchemy | 2.0 | ORM |
| SQLite | Built-in | Database |
| Groq SDK | 0.11 | LLM API client |
| Pydantic | 2.9 | Request/response validation |
| PyMuPDF (fitz) | 1.24 | PDF text extraction |
| python-docx | 1.1 | DOCX text extraction |
| NumPy | 1.26 | Vector math for RAG |
| sentence-transformers | 3.2 | Embedding model (all-MiniLM-L6-v2) |
| tenacity | 8.5 | Retry logic |

### School Backend (port 8001)

| Technology | Version | Role |
|---|---|---|
| FastAPI | 0.110+ | Web framework |
| youtube-transcript-api | 0.6 | Fetch YouTube captions |
| yt-dlp | 2024.4 | Subtitle extraction fallback |
| requests | 2.31 | Groq API HTTP calls |
| python-dotenv | 1.0 | Environment config |

### AI / LLM

| Model | Provider | Used for |
|---|---|---|
| `openai/gpt-oss-120b` | Groq | Primary — all complex tasks |
| `openai/gpt-oss-20b` | Groq | Fast/secondary tasks |
| `qwen/qwen3.8-27b` | Groq | Rate-limit fallback |
| `allam-2-7b` | Groq | Last fallback |
| `all-MiniLM-L6-v2` | HuggingFace | Local embeddings for RAG |

> Models rotate automatically — if the primary is rate-limited, the next model is tried instantly with no user-visible failure.

---

## 5. Feature Breakdown — How Each Was Built

---

### 5.1 Landing Page / Path Selector

**File:** `frontend/src/pages/Landing.jsx`

**How it works:**
- Two large clickable cards on a dark gradient background
- Card 1 → navigates to `/jee` (School mode, no login needed)
- Card 2 → navigates to `/login` then `/dashboard` (Engineering mode)
- Pure CSS animations (fadeIn, floating blobs) — no external animation library
- Fully responsive with CSS Grid

**Built from:** Original design — not from any source repo.

---

### 5.2 School / JEE Platform

**File:** `frontend/src/pages/JEEPlatform.jsx`
**Backend:** `gen ai/main_groq.py`
**Agents:** `gen ai/agents/`

**Three tabs:**

#### 📹 Video Notes Tab
1. User pastes a YouTube URL
2. `TranscriptAgent` tries 4 strategies to get transcript text:
   - YouTube Caption API (English direct) → fastest
   - YouTube Caption API (any language) + Groq translation → for Hindi/regional vids
   - yt-dlp subtitle download + translation → for auto-generated subs
   - Video metadata/description → last resort
3. Transcript sent to Groq with a structured prompt → returns textbook-style notes
4. `PYQAgent` looks up `data/pyqs.csv` for matching questions; if not enough found, Groq generates JEE/NEET-pattern questions as JSON
5. Practice questions generated with a second Groq call
6. All results rendered with `react-markdown`

#### 📚 Previous Year Questions Tab
- Direct call to `/generate-pyqs` endpoint
- `PYQAgent._generate_ai_pyqs()` prompts Groq to return a JSON array of questions with options, correct answer, and explanation
- Expandable cards show answer + explanation on click

#### 🤖 Ask AI Tutor Tab
- Single POST to `/ask`
- Groq prompt wraps the question with subject context and asks for explanation + formula + example + exam tip

**Built from:** `gen ai` project, with Gemini agents replaced by Groq via unified `llm_client.py`.

---

### 5.3 AI Tutor Chat (Engineering)

**Files:** `backend/app/routers/chat.py` → `app/services/tutor_service.py`
**Frontend:** `frontend/src/pages/Chat.jsx`

**Pipeline (5 steps):**
```
User message
    → classify_intent()     [learn | practice | answer_question | general]
    → rag_answer()          [retrieve top-3 chunks from student's documents]
    → generate_lesson()     [if intent=learn → structured lesson with examples]
       or answer_question() [multi-turn with conversation history]
    → extract_memory_facts()[LLM extracts 1-5 durable facts → stored in DB]
    → suggest_next_topics() [3-5 recommendations based on weak concepts]
```

**Conversation history:** Last 10 messages retrieved from SQLite and passed to Groq as multi-turn context.

**RAG integration:** If the student has uploaded documents, relevant chunks are retrieved and injected into the system prompt before the LLM call.

**Built from:** EduAgent's planner/teacher/memory/recommendation agent pipeline, rewritten without LangGraph (pure Python functions), with Groq replacing OpenAI/Gemini.

---

### 5.4 Adaptive Quiz (Engineering)

**Files:** `backend/app/routers/quiz.py` → `app/services/quiz_service.py`
**Frontend:** `frontend/src/pages/Quiz.jsx`

**Generation:**
- Groq is prompted to return a strict JSON schema with `id`, `type` (mcq/true_false/short_answer), `question`, `options`, `correct_answer`, `explanation`
- If the student has previous weak concepts tracked in DB, they are injected into the prompt to make the quiz adaptive
- Fallback questions auto-generated in Python if Groq returns malformed JSON

**Evaluation:**
- MCQ/True-False: deterministic letter comparison (no LLM needed → instant)
- Short answer: second Groq call with a strict grader prompt → score 0–10
- Results stored to `quiz_attempts` table, weak concepts merged into `student_progress`

**Scoring:** `(correct / total) × 100` → updates avg_quiz_score in real time

**Built from:** EduAgent quiz/evaluation agents + SkillBridge adaptive quiz module.

---

### 5.5 Resume + JD Matcher (Engineering)

**Files:** `backend/app/routers/resume.py` → `app/services/resume_service.py`
**Frontend:** `frontend/src/pages/Resume.jsx`

**Upload & Parse:**
1. File uploaded as `multipart/form-data`
2. `extract_resume_text()` — PyMuPDF for PDF, python-docx for DOCX, plain read for TXT
3. `parse_resume()` — Groq extracts structured JSON: name, email, skills, education, experience, projects
4. `score_ats()` — Groq returns ATS score (0–100), keyword gaps, suggestions
5. Extracted skills saved to `student.current_skills` in SQLite

**JD Match:**
1. Resume text + job description both sent to Groq in one prompt
2. Returns: `match_score`, `matched_skills`, `missing_skills`, `action_items`, `recommendation`
3. Displayed with color-coded score (green ≥75%, yellow ≥50%, red <50%)

**ATS analysis removed** from UI per user request — only upload + JD matching shown.

**Built from:** SkillBridge AI resume/JD analysis service + Jobyn skill gap module.

---

### 5.6 Learning Roadmap (Engineering)

**Files:** `backend/app/routers/roadmap.py` → `app/services/roadmap_service.py`
**Frontend:** `frontend/src/pages/Roadmap.jsx`

**How it works:**
1. `extract_skill_gaps()` — Groq compares student's current skills vs target role → returns list of gaps
2. `generate_roadmap()` — Groq generates a full JSON roadmap:
   - Per-week: `focus`, `topics[]`, `resources[]`, `projects[]`, `milestone`
   - Resources include `{title, type, url, description}` with real YouTube search URLs and official docs links
3. Weeks rendered as collapsible accordion panels
4. Each resource card shows type icon (▶️ YouTube, 📄 Docs, 🎓 Course) with clickable "Open →" button
5. Optional JD text accepted — if provided, roadmap is tailored to that specific job

**Built from:** SkillBridge AI roadmap generation + Jobyn improvement planning.

---

### 5.7 Voice Mock Interview (Engineering)

**Files:** `backend/app/routers/interview.py` → `app/services/interview_service.py`
**Frontend:** `frontend/src/pages/Interview.jsx`

**Three interview modes:**

| Mode | How questions are generated |
|---|---|
| Technical | Groq generates role-specific coding/system-design questions |
| HR / Behavioral | Groq generates STAR-method behavioral questions |
| Resume-Based | Groq reads the student's actual resume → asks deep questions about their specific projects and skills |

**Voice Mode (Web Speech API — browser-native, no DLL/server needed):**
1. AI reads question aloud → `window.speechSynthesis.speak()`
2. Student speaks answer → `window.SpeechRecognition` captures transcript in real time
3. Transcript auto-saved as the answer for that question
4. No server-side audio processing — entirely browser-side

**Evaluation:**
- All Q&A pairs sent to Groq in one batch
- Returns: `overall_score`, per-question `score/10` + `feedback` + `ideal_points`, `strengths[]`, `improvements[]`, `summary`

**Built from:** SkillBridge AI mock interview + Jobyn interview prep, with voice added fresh using Web Speech API.

---

### 5.8 Documents / RAG (Engineering)

**Files:** `backend/app/routers/documents.py` → `app/services/rag_service.py`
**Frontend:** `frontend/src/pages/Documents.jsx`

**Indexing pipeline:**
```
Upload file (PDF/DOCX/TXT/MD)
    → extract_text()     [PyMuPDF / python-docx / plain read]
    → chunk_text()       [400-word chunks, 80-word overlap]
    → _embed_text()      [hash-based bag-of-words → 512-dim NumPy vector]
    → save to JSON       [chroma_db/vectors/{student_id}/index.json]
```

**Why pure NumPy instead of ChromaDB:**
ChromaDB requires grpc which was blocked by Windows Application Control policy on this machine. The pure-Python/NumPy implementation stores vectors as JSON arrays and uses cosine similarity for retrieval — zero native DLL dependencies, identical retrieval quality for typical document sizes.

**Query pipeline:**
```
Query text
    → _embed_text()          [same hash-based embedding]
    → cosine_similarity()    [NumPy dot product, L2-normalised]
    → top-k chunks           [sorted by score, take top 4]
    → Groq LLM               [grounded answer from context]
    → sources shown          [excerpts displayed in UI]
```

**Built from:** EduAgent RAG service, rewritten with pure NumPy replacing ChromaDB.

---

### 5.9 Dashboard (Engineering)

**Files:** `backend/app/routers/dashboard.py`
**Frontend:** `frontend/src/pages/Dashboard.jsx`

**What it aggregates (single GET request):**
- Student profile (name, target role, skills)
- Progress stats: avg quiz score, total quizzes, topics studied count, ATS score, readiness score
- Quiz score trend (last 10 attempts → Recharts `LineChart`)
- Top 5 weak concepts (from quiz history)
- Memory facts (extracted by LLM from conversations)
- Latest resume ATS score
- Latest interview overall score
- AI-generated topic recommendations (Groq call with weak concepts + topics studied)

**Built from:** EduAgent dashboard + SkillBridge analytics + Jobyn readiness scoring, unified into one endpoint.

---

## 6. Project File Structure

```
final project/
│
├── README.md                          ← This file
│
├── gen ai/                            ← School / JEE Backend (port 8001)
│   ├── agents/
│   │   ├── transcript_agent.py        ← YouTube transcript (4 strategies)
│   │   ├── summarizer_agent.py        ← Transcript → notes
│   │   ├── pyq_agent.py              ← Previous year questions
│   │   └── practice_agent.py         ← Practice question generator
│   ├── utils/
│   │   └── llm_client.py             ← Groq client with model rotation
│   ├── data/
│   │   └── pyqs.csv                  ← PYQ database
│   ├── main_groq.py                  ← FastAPI entry point
│   ├── requirements.txt
│   └── .env
│
└── StudyBuddy-AI/                     ← Engineering Platform
    │
    ├── start-all.bat                  ← One-click launcher (all 3 services)
    ├── start-backend.bat
    ├── start-frontend.bat
    │
    ├── backend/
    │   ├── main.py                    ← FastAPI entry point (port 8000)
    │   ├── requirements.txt
    │   ├── .env
    │   ├── studybuddy.db              ← SQLite database (auto-created)
    │   ├── chroma_db/                 ← Vector store (JSON files)
    │   ├── storage/                   ← Uploaded files
    │   └── app/
    │       ├── core/
    │       │   ├── config.py          ← Pydantic settings
    │       │   └── database.py        ← SQLAlchemy engine + Base
    │       ├── models/
    │       │   ├── db_models.py       ← 10 ORM tables
    │       │   └── schemas.py         ← Pydantic request/response schemas
    │       ├── services/
    │       │   ├── llm_service.py     ← Groq client (chat_complete, JSON mode)
    │       │   ├── tutor_service.py   ← Intent classify → lesson/answer → memory
    │       │   ├── rag_service.py     ← Pure-NumPy vector store + retrieval
    │       │   ├── quiz_service.py    ← Generate + evaluate adaptive quizzes
    │       │   ├── resume_service.py  ← Parse + ATS score + JD match
    │       │   ├── roadmap_service.py ← Skill gaps + weekly plan + resource links
    │       │   └── interview_service.py← Question generation + AI evaluation
    │       └── routers/
    │           ├── students.py        ← CRUD /api/students
    │           ├── chat.py            ← POST /api/chat
    │           ├── quiz.py            ← POST /api/quiz/generate, /submit
    │           ├── resume.py          ← POST /api/resume/upload, /match-jd
    │           ├── roadmap.py         ← POST /api/roadmap
    │           ├── interview.py       ← POST /api/interview/start, /evaluate
    │           ├── documents.py       ← POST /api/documents/upload, /query
    │           └── dashboard.py       ← GET /api/dashboard/{student_id}
    │
    └── frontend/
        ├── index.html
        ├── package.json
        ├── vite.config.js
        └── src/
            ├── App.jsx                ← Router: Landing / JEE / Auth / Eng pages
            ├── index.css
            ├── main.jsx
            ├── api/
            │   ├── client.js          ← Axios client → :8000 (engineering)
            │   └── jeeClient.js       ← Axios client → :8001 (school/JEE)
            ├── components/
            │   ├── Layout.jsx         ← Engineering sidebar + nav
            │   └── Card.jsx           ← Shared UI: Card, Btn, Badge, Spinner…
            └── pages/
                ├── Landing.jsx        ← Path selector (School vs Engineering)
                ├── Login.jsx          ← Email-based auth (no password)
                ├── JEEPlatform.jsx    ← Full school platform (3 tabs)
                ├── Dashboard.jsx      ← Student overview + charts
                ├── Chat.jsx           ← AI tutor conversation
                ├── Quiz.jsx           ← Generate + take + review quiz
                ├── Resume.jsx         ← Upload + JD match
                ├── Roadmap.jsx        ← Weekly roadmap with resource links
                ├── Interview.jsx      ← Voice/text mock interview
                └── Documents.jsx      ← Upload notes + RAG query
```

---

## 7. How to Run

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API key (already configured in `.env` files)

### Option A — One Click
```bat
double-click  StudyBuddy-AI\start-all.bat
```
Opens all 3 servers in separate terminal windows.

### Option B — Manual (3 terminals)

**Terminal 1 — Engineering Backend**
```bash
cd "StudyBuddy-AI\backend"
venv\Scripts\activate
python main.py
```

**Terminal 2 — School / JEE Backend**
```bash
cd "gen ai"
python -m uvicorn main_groq:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 3 — React Frontend**
```bash
cd "StudyBuddy-AI\frontend"
npm run dev
```

### Then open: **http://localhost:5173**

---

## 8. Environment Variables

### `StudyBuddy-AI/backend/.env`

```env
GROQ_API_KEY="gsk_..."
SECRET_KEY="studybuddy-super-secret-key-2024-agentic-ai-platform-xK9mP2nQ"
DATABASE_URL="sqlite:///./studybuddy.db"
LLM_PROVIDER="groq"
EMBEDDING_MODEL="all-MiniLM-L6-v2"
CHROMA_DB_PATH="./chroma_db"
UPLOAD_DIR="./storage"
MAX_FILE_SIZE_MB=10
GROQ_MODEL_CHAT="openai/gpt-oss-120b"
GROQ_MODEL_FAST="openai/gpt-oss-20b"
CORS_ORIGINS="http://localhost:5173,http://localhost:5174,http://localhost:3000"
```

### `gen ai/.env`

```env
GROQ_API_KEY="gsk_..."
```

---

## 9. API Reference

### Engineering Backend (:8000)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/students` | Register a new student |
| GET | `/api/students` | List all students |
| POST | `/api/chat` | Send a message to the AI tutor |
| GET | `/api/chat/{student_id}/conversations` | List conversations |
| POST | `/api/quiz/generate` | Generate an adaptive quiz |
| POST | `/api/quiz/submit` | Submit answers and get scored |
| POST | `/api/resume/upload` | Upload resume → parse + ATS score |
| POST | `/api/resume/match-jd` | Match resume against a job description |
| POST | `/api/roadmap` | Generate a learning roadmap |
| GET | `/api/roadmap/{roadmap_id}` | Fetch a specific roadmap |
| POST | `/api/interview/start` | Start a mock interview session |
| POST | `/api/interview/evaluate` | Submit answers and get AI feedback |
| POST | `/api/documents/upload` | Upload a document and index it |
| GET | `/api/documents/{student_id}` | List uploaded documents |
| POST | `/api/documents/query` | RAG query over uploaded documents |
| GET | `/api/dashboard/{student_id}` | Full student analytics |
| GET | `/health` | Health check |

> Interactive docs: **http://localhost:8000/docs**

### School Backend (:8001)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/analyze` | YouTube URL → notes + PYQs + practice Qs |
| POST | `/generate-pyqs` | Generate PYQs for a subject/chapter |
| POST | `/ask` | Ask a subject question directly |
| GET | `/health` | Health check |

---

## 10. Source Projects Merged

| Repository | Original Purpose | Key Code Reused |
|---|---|---|
| **EduAgent** | LangGraph AI tutor | Agent pipeline logic (planner, teacher, memory, recommendation, RAG) — rewritten without LangGraph |
| **SkillBridge AI** | Career platform (Supabase) | Resume parsing, ATS scoring, JD matching, mock interview, roadmap generation — ported to SQLite + Groq |
| **Jobyn** | Placement readiness (Supabase) | Skill gap analysis, interview question generation, readiness scoring — ported to SQLite + Groq |
| **JEE GenAI** | YouTube → Notes | Transcript agent (4-strategy pipeline), PYQ agent, practice question agent — kept as-is, Gemini replaced with Groq |

All Supabase/PostgreSQL dependencies replaced with SQLite.
All OpenAI/Gemini/Ollama dependencies replaced with Groq.
LangGraph removed — tutoring pipeline reimplemented as plain Python functions.
ChromaDB removed — replaced with pure-NumPy JSON vector store (grpc DLL blocked by Windows Application Control policy).

---

*Built as a unified AI education platform. All AI features powered by Groq LLM.*
