"""
Roadmap service — personalized week-by-week learning plan with real resource links.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from app.services.llm_service import simple_prompt_json
from app.services.resume_service import extract_skill_gaps


_ROADMAP_SYSTEM = """You are an expert learning path designer and career coach.
Create a detailed, actionable week-by-week learning roadmap.
Return ONLY valid JSON (no markdown) with this exact schema:
{
  "target_role": "string",
  "duration_weeks": <int>,
  "overview": "string",
  "skill_gaps": ["gap1"],
  "weeks": [
    {
      "week": 1,
      "focus": "string",
      "topics": ["topic1"],
      "resources": [
        {"title": "Resource Title", "type": "youtube|docs|article|course", "url": "https://...", "description": "short desc"}
      ],
      "projects": ["mini project idea"],
      "milestone": "string"
    }
  ],
  "final_milestone": "string"
}

IMPORTANT for resources:
- Always include REAL, working URLs.
- YouTube playlists: use format https://www.youtube.com/results?search_query=TOPIC+tutorial
- Official docs: use the actual official documentation URL (e.g. https://docs.python.org, https://reactjs.org/docs)
- For each week include at least 1 YouTube link and 1 official docs/article link.
- Make URLs specific to the topic of that week."""


def generate_roadmap(
    target_role: str,
    current_skills: List[str],
    duration_weeks: int = 8,
    jd_text: Optional[str] = None,
    cgpa: Optional[float] = None,
    experience_years: float = 0.0,
) -> Dict[str, Any]:
    skill_gaps = extract_skill_gaps(current_skills, target_role)

    context_parts = [
        f"Target role: {target_role}",
        f"Duration: {duration_weeks} weeks",
        f"Current skills: {', '.join(current_skills) if current_skills else 'beginner'}",
        f"Experience: {experience_years} years",
    ]
    if cgpa:
        context_parts.append(f"CGPA: {cgpa}")
    if jd_text:
        context_parts.append(f"\nJob Description excerpt:\n{jd_text[:1500]}")
    if skill_gaps:
        context_parts.append(f"Identified skill gaps: {', '.join(skill_gaps[:10])}")

    user = "\n".join(context_parts)
    user += f"\n\nCreate a {duration_weeks}-week roadmap with REAL resource URLs. Return only JSON."

    try:
        result = simple_prompt_json(
            system=_ROADMAP_SYSTEM,
            user=user,
            temperature=0.6,
            max_tokens=4000,
        )
        if "weeks" not in result:
            result["weeks"] = []
        if "skill_gaps" not in result:
            result["skill_gaps"] = skill_gaps
        result["duration_weeks"] = duration_weeks
        # Normalize resources in each week
        for week in result.get("weeks", []):
            raw_res = week.get("resources", [])
            normalized = []
            for r in raw_res:
                if isinstance(r, dict):
                    normalized.append(r)
                elif isinstance(r, str):
                    # Convert bare string to dict
                    normalized.append({"title": r, "type": "article", "url": "", "description": r})
            week["resources"] = normalized
        return result
    except Exception:
        return _fallback_roadmap(target_role, duration_weeks, skill_gaps)


def _fallback_roadmap(target_role: str, duration_weeks: int, skill_gaps: List[str]) -> Dict[str, Any]:
    role_slug = target_role.lower().replace(" ", "+")
    weeks = []
    for i in range(1, duration_weeks + 1):
        topic = skill_gaps[i - 1] if i <= len(skill_gaps) else "Core concepts"
        topic_slug = topic.lower().replace(" ", "+")
        weeks.append({
            "week": i,
            "focus": f"Week {i} — {topic}",
            "topics": [topic, "Practice exercises"],
            "resources": [
                {
                    "title": f"YouTube: {topic} Tutorial",
                    "type": "youtube",
                    "url": f"https://www.youtube.com/results?search_query={topic_slug}+tutorial",
                    "description": f"Video tutorials on {topic}",
                },
                {
                    "title": f"Search: {topic} Documentation",
                    "type": "docs",
                    "url": f"https://www.google.com/search?q={topic_slug}+official+documentation",
                    "description": f"Official documentation for {topic}",
                },
            ],
            "projects": [f"Build a small demo using {topic}"],
            "milestone": f"Understand and apply {topic}",
        })
    return {
        "target_role": target_role,
        "duration_weeks": duration_weeks,
        "overview": f"A {duration_weeks}-week plan to become a {target_role}.",
        "skill_gaps": skill_gaps,
        "weeks": weeks,
        "final_milestone": f"Job-ready as a {target_role}",
    }
