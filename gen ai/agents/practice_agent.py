"""
PracticeAgent — generates JEE-level MCQ practice questions from lecture notes.
Answer + explanation are returned but hidden in UI until user clicks "Show Answer".
"""
import json
import logging
import re
from typing import List, Dict

from utils.llm_client import generate

logger = logging.getLogger(__name__)

PRACTICE_PROMPT = """You are a JEE/NEET question paper setter with 20 years of experience.

Based on the following study notes, generate exactly {n} high-quality MCQ practice questions.

STRICT OUTPUT FORMAT — return ONLY valid JSON array, no extra text:
[
  {{
    "id": 1,
    "question": "Full question text here?",
    "options": {{
      "A": "Option A text",
      "B": "Option B text",
      "C": "Option C text",
      "D": "Option D text"
    }},
    "correct": "A",
    "explanation": "Step-by-step explanation of why A is correct and why others are wrong. Show full working for numerical problems."
  }}
]

REQUIREMENTS:
- Mix: 40% conceptual, 40% numerical, 20% application-based
- JEE Main / Advanced difficulty level
- Each explanation must be 3-5 lines minimum
- Numerical questions must show complete working in explanation
- All 4 options must be plausible (no obviously wrong options)
- Do NOT repeat questions

STUDY NOTES:
{notes}"""


class PracticeAgent:

    def generate_questions(self, summary: str, num_questions: int = 10) -> List[Dict]:
        """Returns list of question dicts with hidden answers."""

        if not summary or not summary.strip():
            logger.warning("PracticeAgent called with empty summary")
            return []

        num_questions = max(5, min(num_questions, 15))
        logger.info("Generating %d practice questions", num_questions)

        prompt = PRACTICE_PROMPT.format(n=num_questions, notes=summary[:3000])

        try:
            raw = generate(prompt, timeout=120)
            questions = self._parse_questions(raw)
            logger.info("Generated %d practice questions", len(questions))
            return questions
        except Exception as e:
            logger.exception("PracticeAgent failed: %s", e)
            return []

    def _parse_questions(self, raw: str) -> List[Dict]:
        """Robustly parse JSON from LLM output."""
        raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()

        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start == -1 or end == 0:
            logger.warning("No JSON array found in practice response")
            return []

        json_str = raw[start:end]
        try:
            data = json.loads(json_str)
            valid = []
            for i, q in enumerate(data):
                if all(k in q for k in ("question", "options", "correct", "explanation")):
                    q["id"] = i + 1
                    valid.append(q)
            return valid
        except json.JSONDecodeError as e:
            logger.warning("JSON parse failed: %s — attempting repair", e)
            return self._parse_partial(json_str)

    def _parse_partial(self, raw: str) -> List[Dict]:
        """Extract complete JSON objects one by one, stopping at truncation."""
        valid = []
        depth = 0
        obj_start = None

        for i, ch in enumerate(raw):
            if ch == "{":
                if depth == 0:
                    obj_start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and obj_start is not None:
                    try:
                        obj = json.loads(raw[obj_start:i + 1])
                        if all(k in obj for k in ("question", "options", "correct", "explanation")):
                            obj["id"] = len(valid) + 1
                            valid.append(obj)
                    except json.JSONDecodeError:
                        pass
                    obj_start = None

        if valid:
            logger.info("Partial practice parse recovered %d questions", len(valid))
        return valid
