"""Tutoring chat router."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.db_models import (
    Student, Conversation, Message, MemoryFact, StudentProgress
)
from app.models.schemas import ChatRequest, ChatResponse
from app.services.tutor_service import process_chat

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    # Validate student
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Get or create conversation
    if payload.conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == payload.conversation_id,
            Conversation.student_id == payload.student_id,
        ).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conv = Conversation(
            student_id=payload.student_id,
            title=payload.message[:60],
        )
        db.add(conv)
        db.flush()

    # Build history from last 10 messages
    past = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .order_by(Message.created_at.desc())
        .limit(10)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in reversed(past)]

    # Build student context for recommendations
    progress = db.query(StudentProgress).filter(
        StudentProgress.student_id == student.id
    ).first()
    student_context = {
        "topics_studied": progress.topics_studied if progress else [],
        "weak_concepts": progress.weak_concepts if progress else [],
        "target_role": student.target_role or "",
    }

    # Run tutoring pipeline
    result = process_chat(
        message=payload.message,
        student_id=payload.student_id,
        history=history,
        use_rag=payload.use_rag,
        student_context=student_context,
    )

    # Persist messages
    db.add(Message(
        conversation_id=conv.id, role="user", content=payload.message
    ))
    db.add(Message(
        conversation_id=conv.id, role="assistant", content=result["reply"]
    ))

    # Persist memory facts
    for fact in result.get("memory_facts", []):
        db.add(MemoryFact(
            student_id=payload.student_id,
            fact=fact,
            source_conversation_id=conv.id,
        ))

    # Update progress topics
    if progress and result["intent"] == "learn":
        topics = list(set(progress.topics_studied + [payload.message[:60]]))
        progress.topics_studied = topics[-50:]  # keep last 50

    db.commit()

    return ChatResponse(
        conversation_id=conv.id,
        reply=result["reply"],
        intent=result["intent"],
        suggested_topics=result["suggested_topics"],
        memory_facts_saved=len(result.get("memory_facts", [])),
    )


@router.get("/{student_id}/conversations")
def list_conversations(student_id: str, db: Session = Depends(get_db)):
    convs = (
        db.query(Conversation)
        .filter(Conversation.student_id == student_id)
        .order_by(Conversation.created_at.desc())
        .limit(20)
        .all()
    )
    return [{"id": c.id, "title": c.title, "created_at": c.created_at} for c in convs]


@router.get("/conversation/{conversation_id}/messages")
def get_messages(conversation_id: str, db: Session = Depends(get_db)):
    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )
    return [{"role": m.role, "content": m.content, "created_at": m.created_at} for m in msgs]
