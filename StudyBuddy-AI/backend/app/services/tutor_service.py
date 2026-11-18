"""
Tutoring agent service — planner → teacher/answer → memory → recommendation.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.services.llm_service import simple_prompt, simple_prompt_json, multi_turn
from app.services.rag_service import rag_answer


# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------
_PLANNER_SYSTEM = (
    "Classify the student message into exactly one intent word. "
    "Reply with ONLY one word from: learn | practice | answer_question | general\n"
    "- learn: student wants to understand/study a topic\n"
    "- practice: student wants a quiz or exercise\n"
    "- answer_question: student has a specific factual question\n"
    "- general: anything else"
)


def classify_intent(message: str) -> str:
    try:
        raw = simple_prompt(
            system=_PLANNER_SYSTEM,
            user=message,
            fast=True,
            max_tokens=10,
            temperature=0.0,
        ).lower().strip()
        for intent in ("learn", "practice", "answer_question", "general"):
            if intent in raw:
                return intent
        return "general"
    except Exception:
        return "general"


# ---------------------------------------------------------------------------
# Teacher — structured lesson
# ---------------------------------------------------------------------------
_TEACHER_SYSTEM = """You are an enthusiastic expert tutor. When asked to teach a topic, structure your response with:

## Overview
Brief 2-3 sentence introduction.

## Core Concepts
Key ideas with bullet points and explanations.

## Example
A concrete code example or real-world application.

## Analogy
Relate the concept to something familiar.

## Key Takeaways
3 bullet points summarizing what was learned.

Be clear, engaging, and educational. Use markdown formatting."""


def generate_lesson(topic: str, context: str = "") -> str:
    system = _TEACHER_SYSTEM
    user = f"Teach me about: **{topic}**"
    if context:
        user += f"\n\nUse this context from my notes if relevant:\n{context}"
    return simple_prompt(system=system, user=user, max_tokens=2000)


# ---------------------------------------------------------------------------
# Answer questions
# ---------------------------------------------------------------------------
_ANSWER_SYSTEM = """You are a helpful, knowledgeable study assistant.
Answer the student's question clearly and concisely.
- For technical questions: include a brief code example when helpful.
- For conceptual questions: use simple language and analogies.
- Always be accurate and educational.
Use markdown formatting."""


def answer_question(
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
    context: str = "",
) -> str:
    if context:
        system = _ANSWER_SYSTEM + f"\n\nRelevant context from student's notes:\n{context}"
    else:
        system = _ANSWER_SYSTEM

    if history and len(history) > 0:
        # Include conversation history for context
        return multi_turn(history=history, system=system, max_tokens=1500)
    return simple_prompt(system=system, user=question, max_tokens=1500)


# ---------------------------------------------------------------------------
# Memory extraction
# ---------------------------------------------------------------------------
_MEMORY_SYSTEM = (
    "Extract 1-5 short, durable facts about the student from this conversation. "
    "Facts: topics they studied, skills they know, learning goals, difficulties, background. "
    "Return ONLY a JSON array of short strings (max 100 chars each). "
    "Return [] if nothing notable."
)


def extract_memory_facts(conversation_text: str) -> List[str]:
    try:
        result = simple_prompt_json(
            system=_MEMORY_SYSTEM,
            user=conversation_text[:2000],
            temperature=0.1,
            fast=True,
        )
        if isinstance(result, list):
            return [str(f) for f in result[:5]]
        return []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------
_REC_SYSTEM = (
    "You are a study advisor. Based on the student's topics studied, weak concepts, "
    "and target role, suggest 3-5 specific topics to study next. "
    "Return ONLY a JSON array of topic name strings. "
    "Be specific (e.g. 'Binary Search Trees' not just 'Data Structures')."
)


def suggest_next_topics(
    topics_studied: List[str],
    weak_concepts: List[str],
    target_role: str = "",
) -> List[str]:
    user = (
        f"Target role: {target_role or 'Software Engineer'}\n"
        f"Topics already studied: {', '.join(topics_studied[-8:]) if topics_studied else 'none yet'}\n"
        f"Weak concepts: {', '.join(weak_concepts[:5]) if weak_concepts else 'none identified'}\n"
        "What 3-5 topics should the student study next? Return JSON array."
    )
    try:
        result = simple_prompt_json(
            system=_REC_SYSTEM,
            user=user,
            temperature=0.5,
            fast=True,
        )
        if isinstance(result, list):
            return [str(t) for t in result[:5]]
        return []
    except Exception:
        return ["Data Structures & Algorithms", "System Design", "SQL & Databases"]


# ---------------------------------------------------------------------------
# Main chat pipeline
# ---------------------------------------------------------------------------
def process_chat(
    message: str,
    student_id: str,
    history: Optional[List[Dict[str, str]]] = None,
    use_rag: bool = True,
    student_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    intent = classify_intent(message)
    rag_context = ""
    rag_sources: List[str] = []

    # Only try RAG if the student has uploaded documents
    if use_rag:
        try:
            rag_result = rag_answer(student_id, message, top_k=3)
            sources = rag_result.get("sources", [])
            if sources:
                # Only use RAG context if we found real chunks
                rag_context = "\n\n".join(sources[:2])
                rag_sources = sources
        except Exception:
            pass

    if intent == "learn":
        topic = re.sub(
            r"^(teach me about|explain|tell me about|learn about|what is|how does|show me|study)\s*",
            "", message, flags=re.IGNORECASE,
        ).strip() or message
        reply = generate_lesson(topic, context=rag_context)
    elif intent == "answer_question":
        reply = answer_question(message, history=history, context=rag_context)
    else:
        # For general/practice, also give a good answer
        reply = answer_question(message, history=history, context=rag_context)

    # Extract memory facts
    turn_text = f"Student: {message}\nAssistant: {reply[:600]}"
    facts = extract_memory_facts(turn_text)

    sc = student_context or {}
    suggestions = suggest_next_topics(
        topics_studied=sc.get("topics_studied", []),
        weak_concepts=sc.get("weak_concepts", []),
        target_role=sc.get("target_role", ""),
    )

    return {
        "reply": reply,
        "intent": intent,
        "suggested_topics": suggestions,
        "memory_facts": facts,
        "rag_sources": rag_sources,
    }
