"""Mock interview router — supports technical, HR, and resume-based modes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.db_models import InterviewSession, Student, StudentProgress, Resume
from app.models.schemas import (
    InterviewStartRequest, InterviewStartOut,
    InterviewEvaluateRequest, InterviewEvaluateOut,
)
from app.services.interview_service import generate_questions, evaluate_interview

router = APIRouter(prefix="/api/interview", tags=["Interview"])


@router.post("/start", response_model=InterviewStartOut, status_code=201)
def start_interview(payload: InterviewStartRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    target_role = payload.target_role or student.target_role or "Software Engineer"

    # For resume-based mode, fetch latest resume text
    resume_text = None
    if payload.mode == "resume_based":
        latest_resume = (
            db.query(Resume)
            .filter(Resume.student_id == payload.student_id)
            .order_by(Resume.created_at.desc())
            .first()
        )
        if latest_resume:
            resume_text = latest_resume.raw_text

    questions = generate_questions(
        mode=payload.mode,
        target_role=target_role,
        num_questions=payload.num_questions,
        resume_skills=student.current_skills,
        resume_text=resume_text,
    )

    session = InterviewSession(
        student_id=payload.student_id,
        mode=payload.mode,
        target_role=target_role,
        questions=questions,
        answers=[],
        completed=False,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return InterviewStartOut(
        session_id=session.id,
        mode=session.mode,
        questions=questions,
    )


@router.post("/evaluate", response_model=InterviewEvaluateOut)
def evaluate_session(payload: InterviewEvaluateRequest, db: Session = Depends(get_db)):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == payload.session_id,
        InterviewSession.student_id == payload.student_id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")

    result = evaluate_interview(
        mode=session.mode,
        target_role=session.target_role or "Software Engineer",
        questions=session.questions,
        answers=payload.answers,
    )

    session.answers = payload.answers
    session.evaluation = result
    session.overall_score = result.get("overall_score", 0.0)
    session.completed = True

    progress = db.query(StudentProgress).filter(
        StudentProgress.student_id == payload.student_id
    ).first()
    if progress:
        progress.readiness_score = result.get("overall_score", 0.0)

    db.commit()

    return InterviewEvaluateOut(
        session_id=session.id,
        overall_score=result.get("overall_score", 0.0),
        per_question=result.get("per_question", []),
        strengths=result.get("strengths", []),
        improvements=result.get("improvements", []),
        summary=result.get("summary", ""),
    )


@router.get("/{student_id}/history")
def interview_history(student_id: str, db: Session = Depends(get_db)):
    sessions = (
        db.query(InterviewSession)
        .filter(InterviewSession.student_id == student_id)
        .order_by(InterviewSession.created_at.desc())
        .limit(10)
        .all()
    )
    return [
        {
            "session_id": s.id,
            "mode": s.mode,
            "target_role": s.target_role,
            "overall_score": s.overall_score,
            "completed": s.completed,
            "created_at": s.created_at,
        }
        for s in sessions
    ]
