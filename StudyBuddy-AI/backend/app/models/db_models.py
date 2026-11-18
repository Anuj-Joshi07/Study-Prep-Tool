"""
SQLAlchemy ORM models for Study Prep Tool.
Covers: students, conversations, messages, documents, quizzes, quiz attempts,
        resumes, roadmaps, interview sessions.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, Text, Boolean,
    DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def _uuid():
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Student
# ---------------------------------------------------------------------------
class Student(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String(120), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    cgpa = Column(Float, nullable=True)
    target_role = Column(String(200), nullable=True)
    current_skills = Column(JSON, default=list)       # ["Python", "SQL", ...]
    experience_years = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- relationships ---
    conversations = relationship("Conversation", back_populates="student", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="student", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="student", cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="student", cascade="all, delete-orphan")
    roadmaps = relationship("Roadmap", back_populates="student", cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewSession", back_populates="student", cascade="all, delete-orphan")
    memory_facts = relationship("MemoryFact", back_populates="student", cascade="all, delete-orphan")
    progress = relationship("StudentProgress", back_populates="student", uselist=False, cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Student Progress (aggregate scores)
# ---------------------------------------------------------------------------
class StudentProgress(Base):
    __tablename__ = "student_progress"

    id = Column(String, primary_key=True, default=_uuid)
    student_id = Column(String, ForeignKey("students.id"), unique=True, nullable=False)
    topics_studied = Column(JSON, default=list)
    weak_concepts = Column(JSON, default=list)
    strong_concepts = Column(JSON, default=list)
    quiz_scores = Column(JSON, default=list)        # list of floats
    avg_quiz_score = Column(Float, default=0.0)
    total_quizzes = Column(Integer, default=0)
    ats_score = Column(Float, nullable=True)
    readiness_score = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", back_populates="progress")


# ---------------------------------------------------------------------------
# Conversation & Message  (tutoring chat)
# ---------------------------------------------------------------------------
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=_uuid)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    title = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)       # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


# ---------------------------------------------------------------------------
# Document  (RAG source files)
# ---------------------------------------------------------------------------
class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=_uuid)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    filename = Column(String(300), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)   # pdf | txt | md | docx
    chunk_count = Column(Integer, default=0)
    indexed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="documents")


# ---------------------------------------------------------------------------
# Memory Facts  (extracted from chat)
# ---------------------------------------------------------------------------
class MemoryFact(Base):
    __tablename__ = "memory_facts"

    id = Column(String, primary_key=True, default=_uuid)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    fact = Column(Text, nullable=False)
    source_conversation_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="memory_facts")


# ---------------------------------------------------------------------------
# Quiz  (generated questions bank)
# ---------------------------------------------------------------------------
class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String, primary_key=True, default=_uuid)
    topic = Column(String(200), nullable=False)
    domain = Column(String(100), nullable=True)      # DSA | Web Dev | Python…
    difficulty = Column(String(20), default="medium")
    questions = Column(JSON, nullable=False)         # list of question dicts
    created_at = Column(DateTime, default=datetime.utcnow)

    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(String, primary_key=True, default=_uuid)
    quiz_id = Column(String, ForeignKey("quizzes.id"), nullable=False)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    answers = Column(JSON, nullable=False)           # {question_id: answer}
    score = Column(Float, nullable=False)
    feedback = Column(JSON, default=dict)            # per-question feedback
    weak_concepts = Column(JSON, default=list)
    completed_at = Column(DateTime, default=datetime.utcnow)

    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("Student", back_populates="quiz_attempts")


# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------
class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, default=_uuid)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    filename = Column(String(300), nullable=False)
    file_path = Column(String(500), nullable=False)
    raw_text = Column(Text, nullable=True)
    parsed_data = Column(JSON, nullable=True)        # structured extraction
    ats_score = Column(Float, nullable=True)
    ats_feedback = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="resumes")


# ---------------------------------------------------------------------------
# Roadmap
# ---------------------------------------------------------------------------
class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(String, primary_key=True, default=_uuid)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    target_role = Column(String(200), nullable=False)
    duration_weeks = Column(Integer, default=8)
    weeks = Column(JSON, nullable=False)             # list of week objects
    jd_text = Column(Text, nullable=True)
    skill_gaps = Column(JSON, default=list)
    match_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="roadmaps")


# ---------------------------------------------------------------------------
# Interview Session
# ---------------------------------------------------------------------------
class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(String, primary_key=True, default=_uuid)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    mode = Column(String(20), nullable=False)        # technical | hr
    target_role = Column(String(200), nullable=True)
    questions = Column(JSON, default=list)
    answers = Column(JSON, default=list)
    evaluation = Column(JSON, nullable=True)         # scores + feedback
    overall_score = Column(Float, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="interview_sessions")
