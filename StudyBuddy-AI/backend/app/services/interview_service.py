"""
Mock interview service — generates questions and evaluates answers.
Supports: technical, HR, and resume-based interview modes.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.services.llm_service import simple_prompt_json, simple_prompt


_TECH_SYS = """You are a senior technical interviewer at a top tech company.
Generate realistic, challenging technical interview questions for the given role.
Return ONLY valid JSON:
{
  "mode": "technical",
  "role": "string",
  "questions": ["Full question text 1?", "Full question text 2?"]
}
Make questions specific and relevant to the role. Each question should be a complete sentence."""

_HR_SYS = """You are an experienced HR manager.
Generate thoughtful behavioral and situational interview questions.
Return ONLY valid JSON:
{
  "mode": "hr",
  "role": "string",
  "questions": ["Tell me about yourself and your background.", "Describe a challenge..."]
}
Use STAR method type questions. Each question should be a complete sentence."""

_RESUME_SYS = """You are a strict senior technical interviewer. You have carefully read the candidate's resume.
Generate DEEP, SPECIFIC technical interview questions based ONLY on what is in this resume.

Rules:
- Ask about specific projects listed in their resume ("In your X project, you used Y — explain how...")
- Ask about specific skills/technologies they listed ("You mentioned React — explain useState vs useEffect")
- Ask follow-up questions about their actual work experience
- Ask them to prove depth in technologies they claim to know
- Do NOT ask generic questions — every question must reference something from their resume
- Make questions progressively harder

Return ONLY valid JSON:
{
  "mode": "resume_based",
  "role": "string",
  "questions": [
    "You listed [specific skill] on your resume — explain [specific concept] in that technology.",
    "In your [project name] project, you used [technology]. Walk me through the architecture..."
  ]
}"""


def generate_questions(
    mode: str,
    target_role: str,
    num_questions: int = 5,
    resume_skills: Optional[List[str]] = None,
    resume_text: Optional[str] = None,
) -> List[str]:
    if mode == "resume_based" and resume_text:
        system = _RESUME_SYS
        user = (
            f"Candidate's Target Role: {target_role}\n\n"
            f"=== RESUME ===\n{resume_text[:3000]}\n=== END RESUME ===\n\n"
            f"Generate exactly {num_questions} deep, resume-specific technical questions. "
            "Reference actual skills, projects, and technologies from their resume. Return only JSON."
        )
    elif mode == "technical":
        system = _TECH_SYS
        skills_hint = f"\nCandidate's skills: {', '.join(resume_skills[:10])}" if resume_skills else ""
        user = f"Role: {target_role}\nNumber of questions: {num_questions}{skills_hint}\nReturn only JSON."
    else:
        system = _HR_SYS
        user = f"Role: {target_role}\nNumber of questions: {num_questions}\nReturn only JSON."

    try:
        result = simple_prompt_json(system=system, user=user, temperature=0.8)
        qs = result.get("questions", [])
        valid = [str(q).strip() for q in qs if str(q).strip()]
        return valid[:num_questions] if valid else _fallback_questions(mode, num_questions)
    except Exception:
        return _fallback_questions(mode, num_questions)


def _fallback_questions(mode: str, n: int) -> List[str]:
    tech = [
        "Explain the difference between a stack and a queue. When would you use each?",
        "What is the time complexity of binary search and why?",
        "Explain what REST APIs are and what makes a good REST API design.",
        "What is the difference between SQL and NoSQL databases? Give examples.",
        "How does garbage collection work in Python or Java?",
        "Explain the concept of object-oriented programming with an example.",
        "What is a foreign key and why is it important in relational databases?",
        "Describe the MVC design pattern and its benefits.",
        "What is version control and why is Git important for developers?",
        "Explain the difference between synchronous and asynchronous programming.",
    ]
    hr = [
        "Tell me about yourself and your background in technology.",
        "Why are you interested in this specific role and company?",
        "Describe a challenging technical problem you solved. Walk me through your approach.",
        "Where do you see yourself in 5 years? What are your career goals?",
        "How do you handle working under tight deadlines with multiple priorities?",
        "Give an example of a time you worked effectively in a team.",
        "What are your greatest technical strengths and areas for improvement?",
        "Describe a time you had a disagreement with a team member. How did you resolve it?",
        "Tell me about a project you are most proud of.",
        "Why should we hire you over other candidates?",
    ]
    pool = tech if mode == "technical" else hr
    return pool[:n]


_EVAL_SYSTEM = """You are an expert interview coach evaluating candidate responses.
Evaluate each Q&A pair carefully and return ONLY valid JSON:
{
  "overall_score": <0-100 float>,
  "per_question": [
    {
      "question": "string",
      "answer": "string",
      "score": <0-10>,
      "feedback": "Detailed feedback on this answer",
      "ideal_points": ["Key point that should have been mentioned 1", "Point 2"]
    }
  ],
  "strengths": ["Specific strength 1", "Strength 2"],
  "improvements": ["Specific area to improve 1", "Area 2"],
  "summary": "2-3 sentence honest, constructive overall assessment"
}
Be specific and constructive in feedback."""


def evaluate_interview(
    mode: str,
    target_role: str,
    questions: List[str],
    answers: List[str],
) -> Dict[str, Any]:
    qa_pairs = []
    for i, (q, a) in enumerate(zip(questions, answers), 1):
        qa_pairs.append(f"Q{i}: {q}\nA{i}: {a.strip() if a.strip() else '(no answer given)'}")
    qa_text = "\n\n".join(qa_pairs)

    user = (
        f"Interview mode: {mode}\nRole: {target_role}\n\n"
        f"Q&A Transcript:\n{qa_text}\n\n"
        "Evaluate all answers thoroughly."
    )
    try:
        result = simple_prompt_json(
            system=_EVAL_SYSTEM,
            user=user,
            temperature=0.3,
            max_tokens=3000,
        )
        result["overall_score"] = float(result.get("overall_score", 50.0))
        return result
    except Exception:
        return {
            "overall_score": 50.0,
            "per_question": [
                {"question": q, "answer": answers[i] if i < len(answers) else "",
                 "score": 5, "feedback": "Review needed.", "ideal_points": []}
                for i, q in enumerate(questions)
            ],
            "strengths": ["Completed the interview"],
            "improvements": ["Provide more detailed answers"],
            "summary": "Evaluation temporarily unavailable. Please retry.",
        }
