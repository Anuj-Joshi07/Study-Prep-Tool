"""
Resume service — parsing, ATS scoring, and JD matching.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any, Dict, List
from app.services.llm_service import simple_prompt_json, simple_prompt


def extract_resume_text(file_path: str, file_type: str) -> str:
    file_type = file_type.lower().lstrip(".")
    path = Path(file_path)
    if file_type == "pdf":
        try:
            import fitz
            doc = fitz.open(str(path))
            return "\n".join(page.get_text() for page in doc)
        except Exception:
            pass
    if file_type in ("docx", "doc"):
        try:
            from docx import Document
            doc = Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception:
            pass
    return path.read_text(encoding="utf-8", errors="ignore")


_PARSE_SYSTEM = """You are a resume parser. Extract structured information and return ONLY valid JSON:
{
  "name": "string",
  "email": "string",
  "phone": "string",
  "location": "string",
  "summary": "string",
  "education": [{"degree": "", "institution": "", "year": "", "cgpa": ""}],
  "experience": [{"title": "", "company": "", "duration": "", "description": ""}],
  "skills": ["skill1", "skill2"],
  "certifications": ["cert1"],
  "projects": [{"name": "", "description": "", "tech_stack": []}],
  "languages": ["English"]
}
Return ONLY valid JSON. Use empty string or empty list for missing fields."""


def parse_resume(raw_text: str) -> Dict[str, Any]:
    try:
        return simple_prompt_json(
            system=_PARSE_SYSTEM,
            user=f"Parse this resume:\n\n{raw_text[:6000]}",
            temperature=0.1,
        )
    except Exception:
        return {"name": "", "email": "", "skills": [], "experience": [], "education": []}


_ATS_SYSTEM = """You are an ATS (Applicant Tracking System) expert.
Evaluate this resume and return ONLY valid JSON:
{
  "ats_score": <number 0-100>,
  "keyword_density": <number 0-100>,
  "format_score": <number 0-100>,
  "experience_relevance": <number 0-100>,
  "skills_match": <number 0-100>,
  "keywords_found": ["kw1", "kw2"],
  "keywords_missing": ["kw3", "kw4"],
  "suggestions": ["Specific actionable suggestion 1", "Suggestion 2"],
  "strengths": ["strength1"],
  "weaknesses": ["weakness1"]
}
Be thorough and specific in suggestions."""


def score_ats(raw_text: str, target_role: str = "") -> Dict[str, Any]:
    role_hint = f" for the role: {target_role}" if target_role else ""
    try:
        result = simple_prompt_json(
            system=_ATS_SYSTEM,
            user=f"Analyze this resume{role_hint}:\n\n{raw_text[:6000]}",
            temperature=0.2,
        )
        result["ats_score"] = float(result.get("ats_score", 50))
        return result
    except Exception:
        return {
            "ats_score": 50.0, "keywords_found": [], "keywords_missing": [],
            "suggestions": ["Unable to analyze resume at this time."],
            "strengths": [], "weaknesses": [],
        }


_JD_MATCH_SYSTEM = """You are a career advisor. Compare the resume against the job description.
Return ONLY valid JSON:
{
  "match_score": <number 0-100>,
  "matched_skills": ["skill1", "skill2"],
  "missing_skills": ["skill3"],
  "matched_experience": ["exp point 1"],
  "gaps": ["gap1"],
  "action_items": ["Specific action to improve match 1", "Action 2"],
  "recommendation": "2-3 sentence honest assessment of fit"
}
Be specific and actionable."""


def match_jd(resume_text: str, jd_text: str) -> Dict[str, Any]:
    prompt = (
        f"RESUME:\n{resume_text[:3000]}\n\n"
        f"JOB DESCRIPTION:\n{jd_text[:3000]}\n\n"
        "Analyze the match carefully."
    )
    try:
        result = simple_prompt_json(
            system=_JD_MATCH_SYSTEM,
            user=prompt,
            temperature=0.2,
        )
        result["match_score"] = float(result.get("match_score", 0))
        return result
    except Exception:
        return {
            "match_score": 0.0, "matched_skills": [], "missing_skills": [],
            "gaps": [], "action_items": ["Please try again."],
            "recommendation": "Analysis could not be completed.",
        }


def extract_skill_gaps(resume_skills: List[str], target_role: str) -> List[str]:
    system = (
        "You are a career coach. Given current skills and target role, "
        "list the specific skills the candidate needs to learn. "
        "Return ONLY a JSON array of skill name strings."
    )
    user = (
        f"Target role: {target_role}\n"
        f"Current skills: {', '.join(resume_skills) if resume_skills else 'unknown'}\n"
        "Return JSON array of missing skills."
    )
    try:
        gaps = simple_prompt_json(system=system, user=user, temperature=0.3)
        if isinstance(gaps, list):
            return [str(g) for g in gaps]
        return []
    except Exception:
        return []
