"""Roadmap generation router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.db_models import Roadmap, Student
from app.models.schemas import RoadmapRequest, RoadmapOut
from app.services.roadmap_service import generate_roadmap

router = APIRouter(prefix="/api/roadmap", tags=["Roadmap"])


@router.post("", response_model=RoadmapOut, status_code=201)
def create_roadmap(payload: RoadmapRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    roadmap_data = generate_roadmap(
        target_role=payload.target_role,
        current_skills=student.current_skills or [],
        duration_weeks=payload.duration_weeks,
        jd_text=payload.jd_text,
        cgpa=student.cgpa,
        experience_years=student.experience_years or 0.0,
    )

    roadmap = Roadmap(
        student_id=payload.student_id,
        target_role=payload.target_role,
        duration_weeks=payload.duration_weeks,
        weeks=roadmap_data.get("weeks", []),
        jd_text=payload.jd_text,
        skill_gaps=roadmap_data.get("skill_gaps", []),
        match_score=None,
    )
    db.add(roadmap)
    db.commit()
    db.refresh(roadmap)

    return RoadmapOut(
        roadmap_id=roadmap.id,
        target_role=roadmap.target_role,
        duration_weeks=roadmap.duration_weeks,
        skill_gaps=roadmap.skill_gaps,
        weeks=roadmap.weeks,
    )


@router.get("/{student_id}/list")
def list_roadmaps(student_id: str, db: Session = Depends(get_db)):
    roadmaps = (
        db.query(Roadmap)
        .filter(Roadmap.student_id == student_id)
        .order_by(Roadmap.created_at.desc())
        .all()
    )
    return [
        {
            "roadmap_id": r.id,
            "target_role": r.target_role,
            "duration_weeks": r.duration_weeks,
            "created_at": r.created_at,
        }
        for r in roadmaps
    ]


@router.get("/{roadmap_id}", response_model=RoadmapOut)
def get_roadmap(roadmap_id: str, db: Session = Depends(get_db)):
    roadmap = db.query(Roadmap).filter(Roadmap.id == roadmap_id).first()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    return RoadmapOut(
        roadmap_id=roadmap.id,
        target_role=roadmap.target_role,
        duration_weeks=roadmap.duration_weeks,
        skill_gaps=roadmap.skill_gaps or [],
        weeks=roadmap.weeks or [],
    )
