"""
Pydantic request/response schemas for all API endpoints.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, field_validator, Field
from datetime import datetime


# ---------------------------------------------------------------------------
# Student
# ---------------------------------------------------------------------------
class StudentCreate(BaseModel):
    name: str
    email: str
    password: Optional[str] = None
    cgpa: Optional[float] = None
    target_role: Optional[str] = None
    current_skills: List[str] = []
    experience_years: float = 0.0


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    cgpa: Optional[float] = None
    target_role: Optional[str] = None
    current_skills: Optional[List[str]] = None
    experience_years: Optional[float] = None


class StudentOut(BaseModel):
    id: str
    name: str
    email: str
    cgpa: Optional[float]
    target_role: Optional[str]
    current_skills: List[str]
    experience_years: float
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Chat / Tutoring
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    student_id: str
    message: str
    conversation_id: Optional[str] = None
    use_rag: bool = True


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    intent: str = "general"              # learn | practice | answer_question | general
    suggested_topics: List[str] = []
    memory_facts_saved: int = 0


# ---------------------------------------------------------------------------
# Quiz
# ---------------------------------------------------------------------------
class QuizGenerateRequest(BaseModel):
    student_id: str
    topic: str
    domain: Optional[str] = None
    difficulty: str = "medium"           # easy | medium | hard
    num_questions: int = Field(default=5, ge=3, le=15)


class QuizQuestion(BaseModel):
    id: str
    type: str                            # mcq | true_false | short_answer
    question: str
    options: Optional[List[str]] = None  # MCQ only
    correct_answer: str
    explanation: str


class QuizOut(BaseModel):
    quiz_id: str
    topic: str
    difficulty: str
    questions: List[Dict[str, Any]]


class QuizSubmitRequest(BaseModel):
    quiz_id: str
    student_id: str
    answers: Dict[str, str]             # {question_id: answer_text}


class QuizResult(BaseModel):
    quiz_id: str
    score: float
    total: int
    correct: int
    feedback: Dict[str, Any]
    weak_concepts: List[str]
    recommendations: List[str]


# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------
class ResumeAnalysisOut(BaseModel):
    resume_id: str
    parsed: Dict[str, Any]
    ats_score: float
    ats_feedback: Dict[str, Any]
    keywords_missing: List[str]
    suggestions: List[str]


class JDMatchRequest(BaseModel):
    resume_id: str
    jd_text: str


class JDMatchOut(BaseModel):
    match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    action_items: List[str]


# ---------------------------------------------------------------------------
# Roadmap
# ---------------------------------------------------------------------------
class RoadmapRequest(BaseModel):
    student_id: str
    target_role: str
    duration_weeks: int = Field(default=8, ge=4, le=16)
    jd_text: Optional[str] = None


class WeekPlan(BaseModel):
    week: int
    focus: str
    topics: List[str]
    resources: List[str]
    milestone: str


class RoadmapOut(BaseModel):
    roadmap_id: str
    target_role: str
    duration_weeks: int
    skill_gaps: List[str]
    weeks: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# Interview
# ---------------------------------------------------------------------------
class InterviewStartRequest(BaseModel):
    student_id: str
    mode: str = "technical"             # technical | hr | resume_based
    target_role: Optional[str] = None
    num_questions: int = Field(default=5, ge=3, le=10)


class InterviewStartOut(BaseModel):
    session_id: str
    mode: str
    questions: List[str]


class InterviewEvaluateRequest(BaseModel):
    session_id: str
    student_id: str
    answers: List[str]                  # one answer per question, in order


class InterviewEvaluateOut(BaseModel):
    session_id: str
    overall_score: float
    per_question: List[Dict[str, Any]]
    strengths: List[str]
    improvements: List[str]
    summary: str


# ---------------------------------------------------------------------------
# Documents (RAG)
# ---------------------------------------------------------------------------
class DocumentOut(BaseModel):
    document_id: str = Field(alias="id")
    filename: str
    file_type: str
    chunk_count: int
    indexed: bool
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class RAGQueryRequest(BaseModel):
    student_id: str
    query: str
    top_k: int = Field(default=4, ge=1, le=10)


class RAGQueryOut(BaseModel):
    query: str
    answer: str
    sources: List[str]


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class DashboardOut(BaseModel):
    student: StudentOut
    progress: Dict[str, Any]
    recent_conversations: List[Dict[str, Any]]
    quiz_history: List[Dict[str, Any]]
    memory_facts: List[str]
    recommendations: List[str]


# ---------------------------------------------------------------------------
# Generic
# ---------------------------------------------------------------------------
class MessageOut(BaseModel):
    message: str
    success: bool = True
