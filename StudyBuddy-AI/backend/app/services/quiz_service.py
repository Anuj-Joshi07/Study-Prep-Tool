"""
Quiz service — adaptive quiz generation + evaluation.
"""
from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional
from app.services.llm_service import simple_prompt_json, simple_prompt


_GEN_SYSTEM = """You are an expert quiz creator for technical education.
Generate a quiz and return ONLY valid JSON (no markdown fences) with this exact schema:
{
  "topic": "string",
  "difficulty": "easy|medium|hard",
  "questions": [
    {
      "id": "q1",
      "type": "mcq",
      "question": "Full question text here?",
      "options": ["A) First option", "B) Second option", "C) Third option", "D) Fourth option"],
      "correct_answer": "A",
      "explanation": "Why A is correct..."
    }
  ]
}

Rules:
- Each question MUST have a non-empty "question" field with actual question text
- MCQ must have exactly 4 options labeled A) B) C) D)
- correct_answer is just the letter: A, B, C, or D
- explanation must be meaningful (1-2 sentences)
- Generate exactly the requested number of questions
- Mix question types: mostly mcq, some true_false, optionally 1 short_answer at end
- For true_false: options are ["True", "False"], correct_answer is "True" or "False"
- Make questions educational and relevant to the topic"""


def generate_quiz(
    topic: str,
    num_questions: int = 5,
    difficulty: str = "medium",
    domain: Optional[str] = None,
    weak_concepts: Optional[List[str]] = None,
) -> Dict[str, Any]:
    focus = ""
    if weak_concepts:
        focus = f" Focus especially on these weak areas: {', '.join(weak_concepts[:5])}."
    domain_hint = f" Domain: {domain}." if domain else ""

    user = (
        f"Create a {difficulty} difficulty quiz on the topic: '{topic}'.{domain_hint}{focus}\n"
        f"Generate exactly {num_questions} questions.\n"
        "Return ONLY the JSON object, no extra text."
    )
    try:
        result = simple_prompt_json(
            system=_GEN_SYSTEM,
            user=user,
            temperature=0.7,
            max_tokens=3000,
        )
        questions = result.get("questions", [])
        # Assign stable IDs and validate
        valid_questions = []
        for i, q in enumerate(questions):
            if not q.get("question"):
                continue
            q["id"] = f"q{i+1}"
            # Ensure options exist for mcq
            if q.get("type", "mcq") == "mcq" and not q.get("options"):
                q["options"] = ["A) Option A", "B) Option B", "C) Option C", "D) Option D"]
            valid_questions.append(q)
        result["questions"] = valid_questions if valid_questions else _fallback_quiz(topic, num_questions, difficulty)["questions"]
        return result
    except Exception as e:
        return _fallback_quiz(topic, num_questions, difficulty)


def _fallback_quiz(topic: str, num_questions: int, difficulty: str) -> Dict[str, Any]:
    # Generate simple questions using direct LLM call without JSON parsing
    questions = []
    sample_questions = [
        {"q": f"What is the primary purpose of {topic}?",
         "opts": [f"A) To solve problems related to {topic}", "B) To create databases", "C) To design user interfaces", "D) To manage networks"],
         "ans": "A", "exp": f"{topic} is primarily used to solve specific computational or design problems."},
        {"q": f"Which of the following best describes {topic}?",
         "opts": ["A) A programming language", f"B) A concept/technique in computer science", "C) A hardware component", "D) An operating system"],
         "ans": "B", "exp": f"{topic} is an important concept in computer science and software engineering."},
        {"q": f"True or False: Understanding {topic} is important for software developers.",
         "opts": ["True", "False"],
         "ans": "True", "exp": f"{topic} is a fundamental concept that every developer should understand."},
        {"q": f"What is a common use case for {topic}?",
         "opts": ["A) Managing memory allocation", f"B) Solving real-world problems efficiently", "C) Designing physical circuits", "D) Writing machine code"],
         "ans": "B", "exp": f"{topic} has many practical applications in real-world software development."},
        {"q": f"Which skill is most closely related to {topic}?",
         "opts": ["A) Circuit design", "B) Project management", f"C) Problem solving and logical thinking", "D) Graphic design"],
         "ans": "C", "exp": f"Mastering {topic} requires strong problem-solving and logical thinking skills."},
    ]
    for i in range(min(num_questions, len(sample_questions))):
        sq = sample_questions[i]
        q_type = "true_false" if "True or False" in sq["q"] else "mcq"
        questions.append({
            "id": f"q{i+1}",
            "type": q_type,
            "question": sq["q"],
            "options": sq["opts"],
            "correct_answer": sq["ans"],
            "explanation": sq["exp"],
        })
    # Fill remaining with generic questions
    for i in range(len(questions), num_questions):
        questions.append({
            "id": f"q{i+1}",
            "type": "mcq",
            "question": f"Question {i+1}: Which statement about {topic} is correct?",
            "options": [
                f"A) {topic} is only used in advanced systems",
                f"B) {topic} has no practical applications",
                f"C) {topic} is a fundamental concept worth mastering",
                f"D) {topic} was invented recently",
            ],
            "correct_answer": "C",
            "explanation": f"{topic} is indeed a fundamental concept that is widely used and worth mastering.",
        })
    return {"topic": topic, "difficulty": difficulty, "questions": questions}


_EVAL_SHORT_SYSTEM = """You are a strict but fair grader.
Score the student's short answer 0-10 based on correctness and understanding.
Return ONLY valid JSON: {"score": <0-10>, "feedback": "string", "correct": <bool>}"""


def evaluate_quiz(
    questions: List[Dict[str, Any]],
    answers: Dict[str, str],
) -> Dict[str, Any]:
    total_points = 0.0
    max_points = 0.0
    per_question: List[Dict[str, Any]] = []
    weak_concepts: List[str] = []

    for q in questions:
        qid = q["id"]
        student_answer = (answers.get(qid) or "").strip()
        correct = str(q.get("correct_answer", "")).strip()
        q_type = q.get("type", "mcq")
        explanation = q.get("explanation", "")

        if q_type in ("mcq", "true_false"):
            # Normalize both sides for comparison
            sa_norm = student_answer.upper().strip().lstrip("ABCD) ").strip()[:1]
            co_norm = correct.upper().strip().lstrip("ABCD) ").strip()[:1]
            # Also try direct comparison
            is_correct = (
                sa_norm == co_norm and bool(sa_norm)
            ) or (
                student_answer.upper().strip() == correct.upper().strip()
            )
            pts = 1.0 if is_correct else 0.0
            feedback = (
                f"✅ Correct! {explanation}" if is_correct
                else f"❌ Incorrect. The correct answer is **{correct}**. {explanation}"
            )
        else:
            try:
                grade = simple_prompt_json(
                    system=_EVAL_SHORT_SYSTEM,
                    user=(
                        f"Question: {q['question']}\n"
                        f"Expected: {correct}\n"
                        f"Student answered: {student_answer or '(no answer)'}"
                    ),
                    temperature=0.1,
                    fast=True,
                )
                raw_score = float(grade.get("score", 0))
                pts = raw_score / 10.0
                feedback = grade.get("feedback", explanation)
                is_correct = grade.get("correct", pts >= 0.6)
            except Exception:
                pts = 0.0
                feedback = f"Could not auto-grade. Expected: {correct}"
                is_correct = False

        max_points += 1.0
        total_points += pts
        if not is_correct:
            weak_concepts.append(q.get("question", "")[:60])

        per_question.append({
            "question_id": qid,
            "question": q["question"],
            "student_answer": student_answer,
            "correct_answer": correct,
            "is_correct": is_correct,
            "points": pts,
            "feedback": feedback,
        })

    score_pct = round((total_points / max_points) * 100, 1) if max_points else 0.0
    return {
        "score": score_pct,
        "total": int(max_points),
        "correct": sum(1 for pq in per_question if pq["is_correct"]),
        "feedback": {qr["question_id"]: qr for qr in per_question},
        "weak_concepts": list(set(weak_concepts))[:5],
        "recommendations": _build_recommendations(score_pct, weak_concepts),
    }


def _build_recommendations(score: float, weak: List[str]) -> List[str]:
    if score >= 90:
        return ["Excellent! Move on to advanced topics.", "Try a harder difficulty level."]
    recs = ["Review the questions you missed carefully."] if score >= 70 else [
        "Review the fundamentals before retrying.", "Watch tutorial videos on these topics."]
    for concept in weak[:3]:
        recs.append(f"Study: {concept[:80]}")
    return recs
