# 📖 Study Prep Tool

A unified AI platform that merges three projects:

| Source | Contribution |
|---|---|
| **EduAgent** | AI tutoring, RAG over notes, memory, recommendations |
| **SkillBridge AI** | Resume ATS scoring, JD matching, learning roadmaps, mock interviews |
| **Jobyn** | Career readiness scoring, adaptive quizzes, placement prep |

**LLM:** Groq (llama3-70b-8192) · **DB:** SQLite + SQLAlchemy · **Vector:** ChromaDB · **Embeddings:** all-MiniLM-L6-v2

---

## Features

- 💬 **AI Tutor Chat** — teach mode + Q&A, intent classification, RAG-grounded answers
- 📝 **Adaptive Quiz** — generates MCQ/T-F/short-answer, grades answers, tracks weak concepts
- 📄 **Resume Analyzer** — parses PDF/DOCX, ATS score, keyword gap, suggestions
- 🔗 **JD Matcher** — compares resume vs job description, skill gap breakdown
- 🗺️ **Learning Roadmap** — week-by-week plan personalized to your skills and target role
- 🎤 **Mock Interview** — technical or HR mode, AI-scored answers, feedback report
- 📚 **Documents / RAG** — upload notes → ChromaDB → AI answers from your own files
- 🏠 **Dashboard** — quiz trend, weak areas, memory facts, recommendations, scores

---

## Quickstart

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Backend

```bat
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Backend runs at **http://localhost:8000**  
Swagger docs: **http://localhost:8000/docs**

### 2. Frontend

```bat
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:5173**

### One-click (Windows)

Double-click **`start-all.bat`** — opens both servers in separate windows.

---

## Environment

`backend/.env` is pre-configured. Keys used:

```
GROQ_API_KEY=...           # Groq LLM key
DATABASE_URL=sqlite:///./studybuddy.db
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHROMA_DB_PATH=./chroma_db
UPLOAD_DIR=./storage
```

---

## Project Structure

```
StudyBuddy-AI/
├── backend/
│   ├── app/
│   │   ├── core/          # config.py, database.py
│   │   ├── models/        # db_models.py (ORM), schemas.py (Pydantic)
│   │   ├── routers/       # students, chat, quiz, resume, roadmap, interview, documents, dashboard
│   │   └── services/      # llm_service, rag_service, resume_service, quiz_service,
│   │                      # interview_service, roadmap_service, tutor_service
│   ├── main.py            # FastAPI app entry point
│   ├── requirements.txt
│   └── .env
├── frontend/
│   └── src/
│       ├── pages/         # Login, Dashboard, Chat, Quiz, Resume, Roadmap, Interview, Documents
│       ├── components/    # Layout, Card, Btn, Badge, Spinner, etc.
│       └── api/           # client.js — all API calls
├── start-backend.bat
├── start-frontend.bat
└── start-all.bat
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/students` | Register student |
| GET | `/api/students` | List all students |
| POST | `/api/chat` | AI tutor chat |
| POST | `/api/quiz/generate` | Generate adaptive quiz |
| POST | `/api/quiz/submit` | Submit + grade quiz |
| POST | `/api/resume/upload` | Upload + ATS score resume |
| POST | `/api/resume/match-jd` | JD vs resume match |
| POST | `/api/roadmap` | Generate learning roadmap |
| POST | `/api/interview/start` | Start mock interview |
| POST | `/api/interview/evaluate` | Score interview answers |
| POST | `/api/documents/upload` | Upload + index document |
| POST | `/api/documents/query` | RAG query over documents |
| GET | `/api/dashboard/{id}` | Full student dashboard |
| GET | `/health` | Health check |
