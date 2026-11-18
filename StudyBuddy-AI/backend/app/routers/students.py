"""Students CRUD router."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.db_models import Student, StudentProgress
from app.models.schemas import StudentCreate, StudentUpdate, StudentOut, MessageOut

router = APIRouter(prefix="/api/students", tags=["Students"])


def _get_student_or_404(student_id: str, db: Session) -> Student:
    s = db.query(Student).filter(Student.id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    return s


@router.post("", response_model=StudentOut, status_code=201)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    if db.query(Student).filter(Student.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    student = Student(
        name=payload.name,
        email=payload.email,
        cgpa=payload.cgpa,
        target_role=payload.target_role,
        current_skills=payload.current_skills,
        experience_years=payload.experience_years,
    )
    db.add(student)
    db.flush()
    # Create empty progress record
    db.add(StudentProgress(student_id=student.id))
    db.commit()
    db.refresh(student)
    return student


@router.get("", response_model=List[StudentOut])
def list_students(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Student).offset(skip).limit(limit).all()


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: str, db: Session = Depends(get_db)):
    return _get_student_or_404(student_id, db)


@router.put("/{student_id}", response_model=StudentOut)
def update_student(student_id: str, payload: StudentUpdate, db: Session = Depends(get_db)):
    student = _get_student_or_404(student_id, db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}", response_model=MessageOut)
def delete_student(student_id: str, db: Session = Depends(get_db)):
    student = _get_student_or_404(student_id, db)
    db.delete(student)
    db.commit()
    return {"message": "Student deleted", "success": True}
