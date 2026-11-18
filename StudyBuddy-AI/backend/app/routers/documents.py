"""Documents / RAG router — upload, list, delete, query."""
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.db_models import Document, Student
from app.models.schemas import DocumentOut, MessageOut, RAGQueryRequest, RAGQueryOut
from app.services.rag_service import index_document, delete_document, rag_answer

router = APIRouter(prefix="/api/documents", tags=["Documents"])

ALLOWED_TYPES = {"pdf", "txt", "md", "docx"}


@router.post("/upload", status_code=201)
async def upload_document(
    student_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    ext = Path(file.filename).suffix.lstrip(".").lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported type .{ext}. Allowed: {ALLOWED_TYPES}")

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_FILE_SIZE_MB} MB")

    doc_id = str(uuid.uuid4())
    student_dir = Path(settings.UPLOAD_DIR) / student_id
    student_dir.mkdir(parents=True, exist_ok=True)
    file_path = student_dir / f"{doc_id}.{ext}"
    file_path.write_bytes(content)

    chunk_count = 0
    indexed = False
    try:
        chunk_count = index_document(
            student_id=student_id,
            document_id=doc_id,
            file_path=str(file_path),
            file_type=ext,
        )
        indexed = chunk_count > 0
    except Exception as e:
        pass  # Store record even if indexing fails

    doc = Document(
        id=doc_id,
        student_id=student_id,
        filename=file.filename,
        file_path=str(file_path),
        file_type=ext,
        chunk_count=chunk_count,
        indexed=indexed,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Return plain dict to avoid schema alias issues on upload response
    return {
        "document_id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "chunk_count": doc.chunk_count,
        "indexed": doc.indexed,
        "created_at": doc.created_at,
        "message": f"Uploaded and indexed {chunk_count} chunks successfully.",
    }


@router.get("/{student_id}")
def list_documents(student_id: str, db: Session = Depends(get_db)):
    docs = (
        db.query(Document)
        .filter(Document.student_id == student_id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return [
        {
            "document_id": d.id,
            "filename": d.filename,
            "file_type": d.file_type,
            "chunk_count": d.chunk_count,
            "indexed": d.indexed,
            "created_at": d.created_at,
        }
        for d in docs
    ]


@router.delete("/{document_id}", response_model=MessageOut)
def remove_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_document(doc.student_id, document_id)
    try:
        Path(doc.file_path).unlink(missing_ok=True)
    except Exception:
        pass

    db.delete(doc)
    db.commit()
    return {"message": "Document deleted", "success": True}


@router.post("/query", response_model=RAGQueryOut)
def query_documents(payload: RAGQueryRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    result = rag_answer(
        student_id=payload.student_id,
        query=payload.query,
        top_k=payload.top_k,
    )
    return RAGQueryOut(
        query=payload.query,
        answer=result["answer"],
        sources=result["sources"],
    )
