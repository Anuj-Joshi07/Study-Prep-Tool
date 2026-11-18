"""
Groq LLM client — single entry point for all AI calls in Study Prep Tool.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List, Optional

from groq import Groq
from app.core.config import settings

_client: Optional[Groq] = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def chat_complete(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    retries: int = 3,
) -> str:
    model = model or settings.GROQ_MODEL_CHAT
    client = _get_client()
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            if attempt == retries - 1:
                raise RuntimeError(f"Groq call failed after {retries} attempts: {exc}") from exc
            time.sleep(1.5 ** attempt)
    return ""


def chat_complete_json(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> Any:
    raw = chat_complete(messages, model=model, temperature=temperature, max_tokens=max_tokens)
    # Strip ```json ... ``` fences
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"(\{[\s\S]+\}|\[[\s\S]+\])", cleaned)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        raise ValueError(f"Could not parse JSON from LLM response:\n{raw}")


def simple_prompt(system: str, user: str, fast: bool = False, **kwargs) -> str:
    model = settings.GROQ_MODEL_FAST if fast else settings.GROQ_MODEL_CHAT
    return chat_complete(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        model=model,
        **kwargs,
    )


def simple_prompt_json(system: str, user: str, fast: bool = False, **kwargs) -> Any:
    model = settings.GROQ_MODEL_FAST if fast else settings.GROQ_MODEL_CHAT
    return chat_complete_json(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        model=model,
        **kwargs,
    )


def multi_turn(history: List[Dict[str, str]], system: str, **kwargs) -> str:
    messages = [{"role": "system", "content": system}] + history
    return chat_complete(messages, **kwargs)
