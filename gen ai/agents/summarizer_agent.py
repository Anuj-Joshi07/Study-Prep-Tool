"""
SummarizerAgent — converts raw transcript into structured JEE study notes.
Uses unified LLM client (Gemini → Ollama fallback).
"""
import logging
from typing import Optional

from utils.llm_client import generate

logger = logging.getLogger(__name__)

NOTES_PROMPT = """You are an expert JEE/NEET teacher with 15 years of experience.

Convert the following lecture transcript into STRUCTURED TEXTBOOK-STYLE NOTES.

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

## 📚 Topic Overview
[2-3 sentence summary of what this lecture covers]

## 🔑 Key Concepts
[List each concept with a clear 1-2 line explanation]

## 📐 Important Formulas
[List every formula with:
- Formula name
- The formula itself
- What each symbol means]

## 📖 Theory Explanation
[Detailed explanation of the main concepts, written simply]

## ✏️ Worked Examples
[At least 2 solved examples with step-by-step working]

## ⚡ Exam Tips & Tricks
[5-7 bullet points of high-yield exam tips]

## 🎯 Key Takeaways
[3-5 most important points to remember]

---
TRANSCRIPT:
{transcript}
---

Write clear, structured notes. Use simple language. Be thorough but concise."""


class SummarizerAgent:

    def summarize(self, text: Optional[str]) -> str:
        if not text or not text.strip():
            logger.warning("Summarizer called with empty transcript")
            return "No transcript available to summarize."

        # Use first 4000 chars to stay within token limits
        clipped = text[:4000]
        logger.info("Summarizing transcript (chars=%d → clipped=%d)", len(text), len(clipped))

        prompt = NOTES_PROMPT.format(transcript=clipped)

        try:
            result = generate(prompt, timeout=120)
            logger.info("Summary generated (%d chars)", len(result))
            return result
        except RuntimeError as e:
            # LLM unavailable — return transcript formatted as basic notes
            logger.warning("LLM unavailable, returning raw transcript as notes: %s", e)
            return (
                "## 📚 Lecture Transcript\n\n"
                "> ⚠️ AI notes generation is currently unavailable (API quota exhausted or no LLM running).\n"
                "> The raw transcript is shown below. Notes will generate once the API resets.\n\n"
                + text[:5000]
            )
        except Exception as e:
            logger.exception("Summarizer failed: %s", e)
            return f"⚠️ Notes generation failed: {e}"
