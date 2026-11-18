"""
Unified LLM client — Groq (primary) → Ollama (fallback).

Key design decisions:
- API key is read fresh on EVERY call (so .env changes take effect without restart)
- Models ordered by speed/availability — fast models first
- Rate-limit errors trigger rotation to next model
- All errors are caught and converted to clean RuntimeError messages
"""
import logging
import os
import time

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Groq models ordered: best quality first, fallbacks after
GROQ_MODELS = [
    "openai/gpt-oss-120b",   # ✅ largest, best quality
    "qwen/qwen3.8-27b",      # ✅ good reasoning, fast
    "openai/gpt-oss-20b",    # fallback
    "allam-2-7b",            # lightest fallback
]

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def _get_key() -> str:
    """Read API key fresh from env every call — picks up .env changes instantly."""
    load_dotenv(override=True)
    return os.getenv("GROQ_API_KEY", "").strip()


def _get_ollama_cfg() -> tuple:
    load_dotenv(override=True)
    return (
        os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate"),
        os.getenv("OLLAMA_MODEL", "llama3"),
    )


def _validate_key(key: str) -> None:
    """Raise clear error if key looks wrong."""
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is not set.\n"
            "  1. Go to https://console.groq.com/keys\n"
            "  2. Create a new key\n"
            "  3. Add it to your .env file:\n"
            "     GROQ_API_KEY=gsk_..."
        )
    if not key.startswith("gsk_"):
        raise RuntimeError(
            f"GROQ_API_KEY looks invalid (got: {key[:8]}...).\n"
            "A valid Groq key starts with 'gsk_'. Get one at https://console.groq.com/keys"
        )


def _call_groq(prompt: str, timeout: int = 120) -> str:
    """
    Try each Groq model in order until one succeeds.
    Rotates on rate-limit (429) errors, raises immediately on auth errors.
    """
    key = _get_key()
    _validate_key(key)

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    last_err = None

    for model in GROQ_MODELS:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 8192,
        }
        try:
            t0 = time.perf_counter()
            resp = requests.post(
                GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=timeout,
            )

            # Auth error — no point trying other models
            if resp.status_code in (401, 403):
                raise RuntimeError(
                    "Groq API key is invalid or expired.\n"
                    "Get a new key at https://console.groq.com/keys\n"
                    "Then update GROQ_API_KEY in your .env file."
                )

            # Rate limit — try next model
            if resp.status_code == 429:
                logger.warning("Groq [%s] rate limited — trying next model", model)
                last_err = RuntimeError(f"Rate limited on {model}")
                time.sleep(1)
                continue

            # Model not found — try next
            if resp.status_code == 404:
                logger.warning("Groq [%s] not found — trying next model", model)
                last_err = RuntimeError(f"Model {model} not found")
                continue
            # Server error — try next
            if resp.status_code >= 500:
                logger.warning("Groq [%s] server error %d — trying next model", model, resp.status_code)
                last_err = RuntimeError(f"Server error {resp.status_code} on {model}")
                time.sleep(2)
                continue

            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"].strip()
            logger.info("✓ Groq [%s]: %d chars in %.1fs", model, len(text), time.perf_counter() - t0)
            return text

        except RuntimeError:
            raise  # re-raise auth errors immediately
        except requests.exceptions.Timeout:
            logger.warning("Groq [%s] timed out — trying next model", model)
            last_err = RuntimeError(f"Timeout on {model}")
            continue
        except requests.exceptions.ConnectionError as e:
            logger.warning("Groq [%s] connection error: %s", model, e)
            last_err = RuntimeError(f"Connection error: {e}")
            continue
        except Exception as e:
            logger.warning("Groq [%s] unexpected error: %s", model, str(e)[:80])
            last_err = e
            continue

    raise RuntimeError(
        f"All Groq models failed. Last error: {last_err}\n"
        "Your free tier quota may be exhausted — check https://console.groq.com\n"
        "Or run Ollama locally: ollama serve && ollama pull llama3"
    )


def _call_ollama(prompt: str, timeout: int = 300) -> str:
    """Call local Ollama API."""
    url, model = _get_ollama_cfg()
    t0 = time.perf_counter()
    try:
        resp = requests.post(
            url,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        resp.raise_for_status()
        text = resp.json().get("response", "").strip()
        logger.info("✓ Ollama [%s]: %d chars in %.1fs", model, len(text), time.perf_counter() - t0)
        return text
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Ollama not running. Start it with: ollama serve")
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Ollama timed out after {timeout}s.")
    except Exception as e:
        raise RuntimeError(f"Ollama error: {e}")


def generate(prompt: str, timeout: int = 120) -> str:
    """
    Main entry point — Groq first, Ollama fallback.
    Always returns a string or raises RuntimeError with a user-friendly message.
    """
    key = _get_key()

    # Try Groq if key is present
    if key:
        try:
            return _call_groq(prompt, timeout)
        except RuntimeError as e:
            err_str = str(e)
            # Auth errors should not fall through to Ollama
            if "invalid or expired" in err_str or "not set" in err_str:
                raise
            logger.warning("Groq unavailable: %s — trying Ollama", err_str[:100])

    # Ollama fallback
    try:
        return _call_ollama(prompt, timeout)
    except RuntimeError:
        raise RuntimeError(
            "AI service unavailable. To fix:\n\n"
            "Option A — Groq (cloud, free):\n"
            "  1. Get a key: https://console.groq.com/keys\n"
            "  2. Set in .env: GROQ_API_KEY=gsk_...\n\n"
            "Option B — Ollama (local, unlimited):\n"
            "  1. ollama serve\n"
            "  2. ollama pull llama3"
        )


def check_availability() -> dict:
    """
    Returns status dict — used by /health endpoint.
    Does a lightweight probe without running a full prompt.
    """
    key = _get_key()
    result = {
        "groq_key_present": bool(key),
        "groq_key_valid_format": key.startswith("gsk_") if key else False,
        "groq_working": False,
        "groq_model": None,
        "ollama_running": False,
        "ollama_model": None,
        "active_backend": None,
    }

    # Probe Groq with a tiny request
    if key and key.startswith("gsk_"):
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        for model in GROQ_MODELS:
            try:
                resp = requests.post(
                    GROQ_API_URL,
                    headers=headers,
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "Hi"}],
                        "max_tokens": 5,
                    },
                    timeout=10,
                )
                if resp.status_code == 200:
                    result["groq_working"] = True
                    result["groq_model"] = model
                    result["active_backend"] = f"groq/{model}"
                    break
                elif resp.status_code == 429:
                    # Rate limited but key is valid — try next
                    continue
                elif resp.status_code in (401, 403):
                    break  # invalid key, stop probing
                # 404 = model not available on this account, try next
            except Exception:
                break

    # Probe Ollama
    url, model = _get_ollama_cfg()
    try:
        r = requests.get(url.replace("/api/generate", "/api/tags"), timeout=2)
        if r.status_code == 200:
            result["ollama_running"] = True
            result["ollama_model"] = model
            if not result["active_backend"]:
                result["active_backend"] = f"ollama/{model}"
    except Exception:
        pass

    return result
