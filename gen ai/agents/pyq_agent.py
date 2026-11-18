"""
PYQAgent — Previous Year Questions.
Loads from CSV if available, otherwise generates AI-powered PYQs via LLM.
"""
import csv
import json
import logging
import os
import re
from typing import Dict, List, Optional

from utils.llm_client import generate

logger = logging.getLogger(__name__)

PYQ_PROMPT = """You are a JEE/NEET expert. Generate {n} previous-year style questions for:
Subject: {subject}
Chapter: {chapter}

These should be based on actual JEE Main/Advanced patterns from 2018-2024.

Return ONLY a valid JSON array:
[
  {{
    "id": 1,
    "year": "JEE Main 2023",
    "exam": "JEE Main",
    "subject": "{subject}",
    "chapter": "{chapter}",
    "question": "Full question text?",
    "options": {{
      "A": "option text",
      "B": "option text",
      "C": "option text",
      "D": "option text"
    }},
    "correct": "A",
    "explanation": "Detailed step-by-step solution showing complete working."
  }}
]

Requirements:
- Authentic JEE/NEET difficulty
- Numerical questions must have proper values and units
- Explanations must show complete working
- Mix of years: 2018, 2019, 2020, 2021, 2022, 2023, 2024"""


class PYQAgent:

    def __init__(self, csv_path: Optional[str] = None):
        if csv_path is None:
            base = os.path.dirname(os.path.dirname(__file__))
            csv_path = os.path.join(base, "data", "pyqs.csv")
        self.csv_path = csv_path
        self._questions: List[Dict] = []

        if os.path.exists(self.csv_path):
            self._load_csv()
        else:
            logger.info("No PYQ CSV found — will use AI generation")

    def _load_csv(self) -> None:
        with open(self.csv_path, "r", encoding="utf-8") as f:
            self._questions = list(csv.DictReader(f))
        logger.info("Loaded %d PYQs from CSV", len(self._questions))

    def get_pyqs(
        self,
        subject: Optional[str] = "Physics",
        chapter: Optional[str] = None,
        topics: Optional[List[str]] = None,
        limit: int = 15,
    ) -> List[Dict]:
        """Return PYQs from CSV first, then AI generation if not enough found."""

        csv_results = []
        if self._questions:
            csv_results = self._filter_csv(subject, chapter, topics, limit)
            logger.info("CSV filter returned %d PYQs", len(csv_results))

        # If CSV has enough, return it
        if len(csv_results) >= 5:
            return csv_results

        # Not enough from CSV — generate with AI
        needed = limit - len(csv_results)
        ai_results = self._generate_ai_pyqs(
            subject or "Physics",
            chapter or "General",
            needed
        )

        return csv_results + ai_results

    def _filter_csv(self, subject, chapter, topics, limit) -> List[Dict]:
        results = []
        for q in self._questions:
            if subject and q.get("subject", "").lower() != subject.lower():
                continue
            if chapter and q.get("chapter", "").lower() != chapter.lower():
                continue
            if topics:
                text = (q.get("topic", "") + " " + q.get("question", "")).lower()
                if not any(t.lower() in text for t in topics):
                    continue
            results.append(q)
            if len(results) >= limit:
                break
        return results

    def _generate_ai_pyqs(self, subject: str, chapter: str, n: int) -> List[Dict]:
        logger.info("Generating %d AI PYQs for %s / %s", n, subject, chapter)
        prompt = PYQ_PROMPT.format(n=n, subject=subject, chapter=chapter)
        try:
            raw = generate(prompt, timeout=120)
            return self._parse(raw)
        except Exception as e:
            logger.exception("PYQ AI generation failed: %s", e)
            return []

    def _parse(self, raw: str) -> List[Dict]:
        raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        start, end = raw.find("["), raw.rfind("]") + 1
        if start == -1 or end == 0:
            return []
        json_str = raw[start:end]
        try:
            data = json.loads(json_str)
            valid = []
            for i, q in enumerate(data):
                if "question" in q:
                    q["id"] = i + 1
                    valid.append(q)
            return valid
        except json.JSONDecodeError as e:
            logger.warning("PYQ JSON parse failed: %s — attempting repair", e)
            # Try to salvage complete objects before the truncation point
            return self._parse_partial(json_str)

    def _parse_partial(self, raw: str) -> List[Dict]:
        """Extract complete JSON objects one by one, stopping at first truncated one."""
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
                        if "question" in obj:
                            obj["id"] = len(valid) + 1
                            valid.append(obj)
                    except json.JSONDecodeError:
                        pass
                    obj_start = None

        if valid:
            logger.info("Partial PYQ parse recovered %d questions", len(valid))
        return valid
