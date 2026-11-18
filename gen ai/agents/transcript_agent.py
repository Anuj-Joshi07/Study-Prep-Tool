"""
TranscriptAgent — robust transcript pipeline with 4 strategies.

Strategy order (fastest → most expensive):
  1. YouTube captions — English (instant, free)
  2. YouTube captions — ANY language + Groq translation to English
  3. yt-dlp auto-subtitles (VTT) + Groq translation if non-English
  4. yt-dlp video description / metadata as context (last resort)

This means the agent works for:
  - English lecture videos           (strategy 1)
  - Hindi/regional language JEE vids (strategy 2 — very common)
  - Videos where transcript API fails (strategy 3)
  - Fully unlisted / caption-less vids (strategy 4 — basic context)
"""
import logging
import os
import re
import shutil
import tempfile

logger = logging.getLogger(__name__)

# Max chars to send to Groq for translation (keep cost low)
_TRANSLATE_CHUNK = 6000


# ── Helpers ───────────────────────────────────────────────────────────────────
def _video_id(url: str) -> str | None:
    m = re.search(r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None


def _snippets_to_text(snippets) -> str:
    return " ".join(
        (s.text if hasattr(s, "text") else str(s)).strip()
        for s in snippets
    ).strip()


def _is_mostly_latin(text: str) -> bool:
    """Return True if text is predominantly Latin-script (English/European)."""
    if not text:
        return True
    latin = sum(1 for c in text if ord(c) < 0x0600)
    return (latin / len(text)) > 0.75


def _translate_to_english(text: str, source_hint: str = "") -> str:
    """Translate non-English text to English using Groq."""
    from utils.llm_client import generate

    # Chunk the text so we don't exceed token limits
    chunks = [text[i:i + _TRANSLATE_CHUNK] for i in range(0, len(text), _TRANSLATE_CHUNK)]
    translated_parts = []

    for i, chunk in enumerate(chunks):
        lang_note = f" (original language: {source_hint})" if source_hint else ""
        prompt = (
            f"You are a professional translator specialising in physics, chemistry, and maths.\n"
            f"Translate the following lecture transcript{lang_note} to clear English.\n"
            f"Keep all formulas, variable names, numbers, and units exactly as they appear.\n"
            f"Output ONLY the translated text — no commentary, no notes.\n\n"
            f"TRANSCRIPT:\n{chunk}"
        )
        try:
            translated_parts.append(generate(prompt, timeout=60))
            logger.info("Translated chunk %d/%d", i + 1, len(chunks))
        except Exception as e:
            logger.warning("Translation chunk %d failed: %s — keeping original", i + 1, e)
            translated_parts.append(chunk)

    return " ".join(translated_parts)


def _clean_vtt(raw: str) -> str:
    """Strip VTT timing/markup and deduplicate repeated lines."""
    # Remove WEBVTT header block
    raw = re.sub(r"WEBVTT[^\n]*\n", "", raw)
    # Remove timestamp lines like 00:00:01.000 --> 00:00:03.000
    raw = re.sub(r"\d{2}:\d{2}:\d{2}[\.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[\.,]\d{3}[^\n]*\n?", "", raw)
    # Remove inline timing tags <00:00:01.000>
    raw = re.sub(r"<\d{2}:\d{2}:\d{2}[\.,]\d{3}>", "", raw)
    # Remove other HTML/VTT tags
    raw = re.sub(r"<[^>]+>", "", raw)
    # Remove cue identifiers (lines that are just numbers)
    raw = re.sub(r"^\d+\s*$", "", raw, flags=re.MULTILINE)
    # Collapse blank lines
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    # Deduplicate consecutive repeated lines (VTT rolls overlap)
    deduped: list[str] = []
    for line in lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)
    return " ".join(deduped)


# ── TranscriptAgent ───────────────────────────────────────────────────────────
class TranscriptAgent:

    def __init__(self, whisper_model_size: str = "tiny"):
        self.whisper_model_size = whisper_model_size  # kept for API compat

    # ── Strategy 1 & 2: YouTube Transcript API ────────────────────────────────
    def _try_captions(self, url: str) -> str | None:
        """
        Fetch YouTube captions.
        - Prefers English.
        - Falls back to ANY available language and translates via Groq.
        """
        try:
            from youtube_transcript_api import YouTubeTranscriptApi

            vid = _video_id(url)
            if not vid:
                return None

            logger.info("YouTube transcript API: video_id=%s", vid)
            api = YouTubeTranscriptApi()

            # ── Strategy 1: Try English directly ─────────────────────────────
            for lang_codes in (["en", "en-IN", "en-US", "en-GB"], None):
                try:
                    if lang_codes:
                        fetched = api.fetch(vid, languages=lang_codes)
                    else:
                        fetched = api.fetch(vid)
                    snippets = list(fetched)
                    text = _snippets_to_text(snippets)
                    if text:
                        logger.info("English captions OK (%d chars)", len(text))
                        return text
                except Exception:
                    continue

            # ── Strategy 2: Fetch any language, translate ─────────────────────
            try:
                transcript_list = api.list(vid)
                transcripts = list(transcript_list)
                logger.info("No English captions — found %d transcript(s); will translate", len(transcripts))

                for t in transcripts:
                    try:
                        snippets = list(t.fetch())
                        raw_text = _snippets_to_text(snippets)
                        if not raw_text:
                            continue

                        lang = getattr(t, "language_code", "unknown")
                        logger.info("Fetched %s transcript (%d chars) — translating to English", lang, len(raw_text))

                        if _is_mostly_latin(raw_text):
                            return raw_text  # already English enough
                        return _translate_to_english(raw_text, source_hint=lang)

                    except Exception as te:
                        logger.info("Transcript fetch for %s failed: %s", getattr(t, 'language_code', '?'), te)
                        continue

            except Exception as e:
                logger.info("Transcript list failed: %s", e)

        except Exception as e:
            logger.info("Caption fetch failed: %s", e)

        return None

    # ── Strategy 3: yt-dlp subtitle extraction ────────────────────────────────
    def _try_yt_dlp_subs(self, url: str) -> str | None:
        """
        Download auto-generated subtitles via yt-dlp (no video download).
        Translates non-English subs via Groq.
        """
        try:
            import yt_dlp

            logger.info("yt-dlp subtitle extraction: %s", url)
            tmp_dir = tempfile.mkdtemp(prefix="jee_subs_")

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "skip_download": True,
                "writeautomaticsub": True,
                "writesubtitles": True,
                # Try all languages — we'll translate if needed
                "subtitleslangs": ["en", "en-IN", "hi", "all"],
                "subtitlesformat": "vtt",
                "outtmpl": os.path.join(tmp_dir, "sub"),
                "socket_timeout": 30,
                # suppress JS runtime warnings
                "extractor_args": {"youtube": {"skip": ["dash", "hls"]}},
            }

            info = None
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
            except Exception as e:
                logger.info("yt-dlp download error: %s", e)

            # Find subtitle files
            text = ""
            lang_found = "unknown"
            for fname in sorted(os.listdir(tmp_dir)):
                if not fname.endswith(".vtt"):
                    continue
                vtt_path = os.path.join(tmp_dir, fname)
                raw = open(vtt_path, encoding="utf-8", errors="ignore").read()
                cleaned = _clean_vtt(raw)
                if cleaned and len(cleaned) > 100:
                    # Detect language from filename e.g. sub.en.vtt or sub.hi.vtt
                    m = re.search(r"\.([a-z]{2,5})\.vtt$", fname)
                    lang_found = m.group(1) if m else "unknown"
                    text = cleaned
                    logger.info("yt-dlp sub file: %s (%d chars)", fname, len(text))
                    break

            shutil.rmtree(tmp_dir, ignore_errors=True)

            if text:
                if not _is_mostly_latin(text):
                    logger.info("Non-Latin subtitle (%s) — translating to English", lang_found)
                    text = _translate_to_english(text, source_hint=lang_found)
                return text

        except ImportError:
            logger.info("yt-dlp not available")
        except Exception as e:
            logger.info("yt-dlp subtitle attempt failed: %s", e)

        return None

    # ── Strategy 4: Video metadata / description ──────────────────────────────
    def _try_video_metadata(self, url: str) -> str | None:
        """
        Last resort: extract title + description from video metadata.
        Enough context for Groq to generate relevant notes/PYQs.
        """
        try:
            import yt_dlp

            logger.info("yt-dlp metadata extraction: %s", url)
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "skip_download": True,
                "socket_timeout": 20,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if not info:
                return None

            title = info.get("title", "")
            desc = info.get("description", "")
            channel = info.get("channel", "")
            tags = ", ".join(info.get("tags", [])[:20])

            if not title and not desc:
                return None

            metadata_text = (
                f"[Video Context — captions unavailable, using metadata]\n\n"
                f"Title: {title}\n"
                f"Channel: {channel}\n"
                f"Tags: {tags}\n\n"
                f"Description:\n{desc[:4000]}"
            )
            logger.info("Metadata extracted (%d chars)", len(metadata_text))
            return metadata_text

        except Exception as e:
            logger.info("Metadata extraction failed: %s", e)
        return None

    # ── Public API ────────────────────────────────────────────────────────────
    def get_transcript(self, url: str) -> str:
        if not url or not url.strip():
            raise ValueError("URL cannot be empty.")
        if "youtube.com" not in url and "youtu.be" not in url:
            raise ValueError(f"Not a valid YouTube URL: {url!r}")

        url = url.strip()
        logger.info("get_transcript: %s", url)

        # Strategy 1 & 2 — YouTube captions (English direct, or any language + translate)
        text = self._try_captions(url)
        if text:
            return text

        # Strategy 3 — yt-dlp subtitles + translate
        logger.info("Captions failed — trying yt-dlp subtitle extraction")
        text = self._try_yt_dlp_subs(url)
        if text:
            return text

        # Strategy 4 — video metadata as context
        logger.info("Subtitles failed — falling back to video metadata")
        text = self._try_video_metadata(url)
        if text:
            return text

        raise RuntimeError(
            "Could not extract any content from this video.\n\n"
            "Possible reasons:\n"
            "  • The video is private, deleted, or age-restricted\n"
            "  • YouTube is rate-limiting requests (try again in a few minutes)\n\n"
            "Tips:\n"
            "  • Try a different video from a popular JEE/NEET channel\n"
            "  • Most Physics Wallah, Vedantu, Unacademy videos work fine"
        )
