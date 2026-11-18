"""
JEE Video to Notes Generator — Groq Version
Port: 8001
"""
import logging, os, time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from agents.transcript_agent import TranscriptAgent
from agents.pyq_agent import PYQAgent
from utils.llm_client import generate, check_availability

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("✅ JEE GenAI Backend started on port 8001")
    yield


app = FastAPI(title="JEE GenAI API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

transcript_agent = TranscriptAgent(whisper_model_size="tiny")
pyq_agent = PYQAgent()


class VideoRequest(BaseModel):
    url: str
    subject: Optional[str] = "Physics"
    chapter: Optional[str] = None
    mode: Optional[str] = "full"


def summarize_with_groq(transcript: str) -> str:
    prompt = f"""You are an expert JEE/NEET teacher. Convert this lecture transcript into structured notes.

Requirements:
- Clear headings and subheadings
- Theory explanation with key concepts
- Important formulas (with symbols explained)
- Worked examples
- Key exam tips and tricks
- Write in simple language for self-study

Lecture transcript:
{transcript[:4000]}"""
    return generate(prompt, timeout=120)


def generate_practice_with_groq(summary: str, num_questions: int = 5) -> str:
    prompt = f"""You are a JEE exam preparation assistant.

From the following notes, create {num_questions} practice questions.

Requirements:
1. Mix of conceptual and numerical questions
2. For each question provide:
   - Question text
   - Four options (A, B, C, D)
   - Correct answer
   - Brief explanation/solution
3. Number the questions clearly
4. Match JEE Main/Advanced difficulty

Notes:
{summary[:2000]}"""
    return generate(prompt, timeout=120)


@app.get("/health")
def health():
    status = check_availability()
    return {"status": "ok", "app": "JEE GenAI", "backend": status.get("active_backend")}


@app.post("/analyze")
def analyze(data: VideoRequest):
    logger.info("Analyze request: url=%s subject=%s", data.url, data.subject)
    total_start = time.perf_counter()

    try:
        # 1. Transcript
        transcript = transcript_agent.get_transcript(data.url)
        logger.info("Transcript: %d chars", len(transcript))

        # 2. Summarize/Notes
        summary = summarize_with_groq(transcript)
        logger.info("Summary: %d chars", len(summary))

        # 3. PYQs
        pyqs = pyq_agent.get_pyqs(
            subject=data.subject,
            chapter=data.chapter,
            topics=[],
            limit=10,
        )
        logger.info("PYQs: %d", len(pyqs))

        # 4. Practice questions
        practice_questions = ""
        if (data.mode or "full").lower() == "full":
            practice_questions = generate_practice_with_groq(summary, num_questions=5)
            logger.info("Practice Qs: %d chars", len(practice_questions))

        logger.info("Done in %.2fs", time.perf_counter() - total_start)
        return {
            "summary": summary,
            "pyqs": pyqs,
            "practice_questions": practice_questions,
            "mode": data.mode or "full",
            "transcript_length": len(transcript),
        }
    except Exception as e:
        logger.exception("Error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/generate-pyqs")
def generate_pyqs(subject: str = "Physics", chapter: str = "Mechanics", n: int = 5):
    """Generate PYQs without a video."""
    pyqs = pyq_agent.get_pyqs(subject=subject, chapter=chapter, limit=n)
    return {"pyqs": pyqs, "subject": subject, "chapter": chapter}


@app.post("/ask")
def ask_question(question: str, subject: str = "Physics"):
    """Answer a JEE/NEET subject question directly."""
    prompt = f"""You are an expert JEE/NEET teacher for {subject}.

Answer this student question clearly and completely:
{question}

Provide:
1. Clear explanation
2. Any relevant formula or theorem
3. Example if applicable
4. Quick exam tip"""
    try:
        answer = generate(prompt, timeout=60)
        return {"answer": answer, "subject": subject}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_groq:app", host="0.0.0.0", port=8001, reload=True)
