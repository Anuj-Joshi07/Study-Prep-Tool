"""Quiz generation and submission router."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.db_models import Quiz, QuizAttempt, Student, StudentProgress
from app.models.schemas import (
    QuizGenerateRequest, QuizOut, QuizSubmitRequest, QuizResult
)
from app.services.quiz_service import generate_quiz, evaluate_quiz

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])


@router.post("/generate", response_model=QuizOut, status_code=201)
def create_quiz(payload: QuizGenerateRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Fetch weak concepts to make quiz adaptive
    progress = db.query(StudentProgress).filter(
        StudentProgress.student_id == payload.student_id
    ).first()
    weak = progress.weak_concepts if progress else []

    quiz_data = generate_quiz(
        topic=payload.topic,
        num_questions=payload.num_questions,
        difficulty=payload.difficulty,
        domain=payload.domain,
        weak_concepts=weak,
    )

    quiz = Quiz(
        topic=payload.topic,
        domain=payload.domain,
        difficulty=payload.difficulty,
        questions=quiz_data.get("questions", []),
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    return QuizOut(
        quiz_id=quiz.id,
        topic=quiz.topic,
        difficulty=quiz.difficulty,
        questions=quiz.questions,
    )


@router.post("/submit", response_model=QuizResult)
def submit_quiz(payload: QuizSubmitRequest, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == payload.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    result = evaluate_quiz(quiz.questions, payload.answers)

    # Persist attempt
    attempt = QuizAttempt(
        quiz_id=quiz.id,
        student_id=payload.student_id,
        answers=payload.answers,
        score=result["score"],
        feedback=result["feedback"],
        weak_concepts=result["weak_concepts"],
    )
    db.add(attempt)

    # Update progress
    progress = db.query(StudentProgress).filter(
        StudentProgress.student_id == payload.student_id
    ).first()
    if progress:
        scores = list(progress.quiz_scores or []) + [result["score"]]
        progress.quiz_scores = scores[-100:]
        progress.avg_quiz_score = round(sum(scores) / len(scores), 1)
        progress.total_quizzes = (progress.total_quizzes or 0) + 1
        # Merge weak concepts
        all_weak = list(set((progress.weak_concepts or []) + result["weak_concepts"]))
        progress.weak_concepts = all_weak[:20]

    db.commit()

    return QuizResult(
        quiz_id=quiz.id,
        score=result["score"],
        total=result["total"],
        correct=result["correct"],
        feedback=result["feedback"],
        weak_concepts=result["weak_concepts"],
        recommendations=result["recommendations"],
    )


@router.get("/{student_id}/history")
def quiz_history(student_id: str, limit: int = 10, db: Session = Depends(get_db)):
    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.student_id == student_id)
        .order_by(QuizAttempt.completed_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "attempt_id": a.id,
            "quiz_id": a.quiz_id,
            "score": a.score,
            "weak_concepts": a.weak_concepts,
            "completed_at": a.completed_at,
        }
        for a in attempts
    ]
