"""Dashboard / analytics router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.db_models import (
    Student, StudentProgress, Conversation, QuizAttempt,
    MemoryFact, InterviewSession, Resume
)
from app.services.tutor_service import suggest_next_topics

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/{student_id}")
def get_dashboard(student_id: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    progress = db.query(StudentProgress).filter(
        StudentProgress.student_id == student_id
    ).first()

    # Recent conversations
    conversations = (
        db.query(Conversation)
        .filter(Conversation.student_id == student_id)
        .order_by(Conversation.created_at.desc())
        .limit(5)
        .all()
    )

    # Quiz history (last 10)
    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.student_id == student_id)
        .order_by(QuizAttempt.completed_at.desc())
        .limit(10)
        .all()
    )

    # Memory facts
    facts = (
        db.query(MemoryFact)
        .filter(MemoryFact.student_id == student_id)
        .order_by(MemoryFact.created_at.desc())
        .limit(10)
        .all()
    )

    # Latest resume
    latest_resume = (
        db.query(Resume)
        .filter(Resume.student_id == student_id)
        .order_by(Resume.created_at.desc())
        .first()
    )

    # Latest interview
    latest_interview = (
        db.query(InterviewSession)
        .filter(InterviewSession.student_id == student_id, InterviewSession.completed == True)
        .order_by(InterviewSession.created_at.desc())
        .first()
    )

    # AI recommendations
    recommendations = suggest_next_topics(
        topics_studied=progress.topics_studied if progress else [],
        weak_concepts=progress.weak_concepts if progress else [],
        target_role=student.target_role or "",
    )

    # Quiz score trend (last 10)
    quiz_trend = [
        {"score": a.score, "date": a.completed_at.isoformat()}
        for a in reversed(attempts)
    ]

    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "cgpa": student.cgpa,
            "target_role": student.target_role,
            "current_skills": student.current_skills,
            "experience_years": student.experience_years,
        },
        "progress": {
            "topics_studied": len(progress.topics_studied) if progress else 0,
            "avg_quiz_score": progress.avg_quiz_score if progress else 0,
            "total_quizzes": progress.total_quizzes if progress else 0,
            "weak_concepts": progress.weak_concepts[:5] if progress else [],
            "strong_concepts": progress.strong_concepts[:5] if progress else [],
            "ats_score": progress.ats_score if progress else None,
            "readiness_score": progress.readiness_score if progress else None,
        },
        "quiz_trend": quiz_trend,
        "recent_conversations": [
            {"id": c.id, "title": c.title, "created_at": c.created_at.isoformat()}
            for c in conversations
        ],
        "memory_facts": [f.fact for f in facts],
        "recommendations": recommendations,
        "latest_resume": {
            "resume_id": latest_resume.id,
            "filename": latest_resume.filename,
            "ats_score": latest_resume.ats_score,
        } if latest_resume else None,
        "latest_interview": {
            "session_id": latest_interview.id,
            "mode": latest_interview.mode,
            "overall_score": latest_interview.overall_score,
        } if latest_interview else None,
    }


@router.get("/admin/students")
def admin_students(db: Session = Depends(get_db)):
    """Admin endpoint: all students with their progress summary."""
    students = db.query(Student).all()
    result = []
    for s in students:
        progress = db.query(StudentProgress).filter(
            StudentProgress.student_id == s.id
        ).first()
        result.append({
            "id": s.id,
            "name": s.name,
            "email": s.email,
            "cgpa": s.cgpa,
            "target_role": s.target_role,
            "avg_quiz_score": progress.avg_quiz_score if progress else 0,
            "total_quizzes": progress.total_quizzes if progress else 0,
            "ats_score": progress.ats_score if progress else None,
            "readiness_score": progress.readiness_score if progress else None,
        })
    return result
