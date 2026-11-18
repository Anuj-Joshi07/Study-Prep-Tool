"""Resume upload, analysis, and JD matching router."""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.db_models import Resume, Student, StudentProgress
from app.models.schemas import ResumeAnalysisOut, JDMatchRequest, JDMatchOut, MessageOut
from app.services.resume_service import (
    extract_resume_text, parse_resume, score_ats, match_jd
)

router = APIRouter(prefix="/api/resume", tags=["Resume"])

ALLOWED_TYPES = {"pdf", "docx", "txt"}


@router.post("/upload", status_code=201)
async def upload_resume(
    student_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    ext = Path(file.filename).suffix.lstrip(".").lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported type .{ext}")

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")

    resume_id = str(uuid.uuid4())
    resume_dir = Path(settings.UPLOAD_DIR) / "resumes" / student_id
    resume_dir.mkdir(parents=True, exist_ok=True)
    file_path = resume_dir / f"{resume_id}.{ext}"
    file_path.write_bytes(content)

    # Extract and parse
    raw_text = extract_resume_text(str(file_path), ext)
    parsed = parse_resume(raw_text)

    # ATS score
    ats_result = score_ats(raw_text, target_role=student.target_role or "")

    resume = Resume(
        id=resume_id,
        student_id=student_id,
        filename=file.filename,
        file_path=str(file_path),
        raw_text=raw_text,
        parsed_data=parsed,
        ats_score=ats_result.get("ats_score", 0.0),
        ats_feedback=ats_result,
    )
    db.add(resume)

    # Update student skills from resume
    extracted_skills = parsed.get("skills", [])
    if extracted_skills:
        student.current_skills = list(set(student.current_skills + extracted_skills))[:50]

    # Update progress ATS score
    progress = db.query(StudentProgress).filter(
        StudentProgress.student_id == student_id
    ).first()
    if progress:
        progress.ats_score = ats_result.get("ats_score", 0.0)

    db.commit()
    db.refresh(resume)

    return ResumeAnalysisOut(
        resume_id=resume.id,
        parsed=parsed,
        ats_score=ats_result.get("ats_score", 0.0),
        ats_feedback=ats_result,
        keywords_missing=ats_result.get("keywords_missing", []),
        suggestions=ats_result.get("suggestions", []),
    )


@router.post("/analyze/{resume_id}", response_model=ResumeAnalysisOut)
def analyze_resume(
    resume_id: str,
    target_role: str = "",
    db: Session = Depends(get_db),
):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    ats_result = score_ats(resume.raw_text or "", target_role=target_role)
    resume.ats_score = ats_result.get("ats_score", 0.0)
    resume.ats_feedback = ats_result
    db.commit()

    return ResumeAnalysisOut(
        resume_id=resume.id,
        parsed=resume.parsed_data or {},
        ats_score=resume.ats_score,
        ats_feedback=ats_result,
        keywords_missing=ats_result.get("keywords_missing", []),
        suggestions=ats_result.get("suggestions", []),
    )


@router.post("/match-jd", response_model=JDMatchOut)
def match_job_description(payload: JDMatchRequest, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == payload.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    result = match_jd(resume.raw_text or "", payload.jd_text)
    return JDMatchOut(
        match_score=result.get("match_score", 0.0),
        matched_skills=result.get("matched_skills", []),
        missing_skills=result.get("missing_skills", []),
        action_items=result.get("action_items", []),
    )


@router.get("/{student_id}/list")
def list_resumes(student_id: str, db: Session = Depends(get_db)):
    resumes = (
        db.query(Resume)
        .filter(Resume.student_id == student_id)
        .order_by(Resume.created_at.desc())
        .all()
    )
    return [
        {
            "resume_id": r.id,
            "filename": r.filename,
            "ats_score": r.ats_score,
            "created_at": r.created_at,
        }
        for r in resumes
    ]
