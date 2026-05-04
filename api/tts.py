"""
Vaani TTS API — Integrated with VaaniTTS_Standalone
Endpoints:
  GET /tts/speak       — generate speech audio (MP3/WAV)
  GET /tts/prosody     — get prosody hint for text/lang/tone
  GET /tts/languages   — list all supported languages and tones
"""
import sys
import os
import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response, JSONResponse
from dotenv import load_dotenv

load_dotenv()

# ── Robust VaaniTTS import ────────────────────────────────────────────────
# Works whether running from project root or app/ subdirectory
_vaani_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "VaaniTTS_Standalone")
)
if _vaani_path not in sys.path:
    sys.path.insert(0, _vaani_path)

try:
    from tts_service import text_to_speech_stream       # noqa: E402
    from prosody_mapper import (                         # noqa: E402
        generate_prosody_hint,
        get_available_tones,
        _load_prosody_mappings
    )
    _VAANI_AVAILABLE = True
except ImportError as e:
    logging.getLogger("tts_api").error(f"[TTS] VaaniTTS import failed: {e}")
    _VAANI_AVAILABLE = False

router = APIRouter(prefix="/tts", tags=["TTS"])
logger = logging.getLogger("tts_api")

_MAX_CHARS = 500  # gTTS limit per request


# ── /tts/speak ────────────────────────────────────────────────────────────

@router.get("/speak")
async def speak(
    text: str  = Query(..., min_length=1, max_length=_MAX_CHARS,
                       description="Text to convert to speech"),
    lang: str  = Query("en",      description="BCP-47 language code, e.g. en, hi, ar, fr"),
    tone: str  = Query("neutral", description="Vaani prosody tone: neutral, educational, formal, friendly, excited, calm"),
    translate: bool = Query(False, description="Translate text to target language before speaking"),
):
    """
    Convert text to speech using Vaani TTS (gTTS primary, pyttsx3 fallback).
    Prosody hint is generated from Vaani's prosody_mapper before synthesis.
    Returns audio/mpeg (MP3) or audio/wav depending on engine used.
    """
    if not _VAANI_AVAILABLE:
        raise HTTPException(status_code=503, detail="VaaniTTS service not available")

    try:
        # Step 1: Generate Vaani prosody hint (logged, used for routing)
        prosody = generate_prosody_hint(text, lang, tone)
        logger.info(
            f"[VAANI TTS] lang={lang} tone={prosody.get('tone')} "
            f"speed={prosody.get('speed')} pitch={prosody.get('pitch')} "
            f"chars={len(text)}"
        )

        # Step 2: Synthesise audio
        audio_data = text_to_speech_stream(
            text=text,
            language=lang,
            use_google_tts=True,
            translate=translate
        )

        if not audio_data:
            raise HTTPException(status_code=500, detail="TTS returned empty audio")

        # Step 3: Detect format and return
        media_type = "audio/wav" if audio_data[:4] == b"RIFF" else "audio/mpeg"
        return Response(
            content=audio_data,
            media_type=media_type,
            headers={
                "Cache-Control": "public, max-age=3600",
                "X-Vaani-Lang": lang,
                "X-Vaani-Tone": tone,
                "X-Vaani-Prosody-Hint": prosody.get("prosody_hint", "default"),
                "X-Vaani-Speed": str(prosody.get("speed", 1.0)),
                "X-Vaani-Pitch": str(prosody.get("pitch", 0.5)),
            }
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"[VAANI TTS] All engines failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="TTS service unavailable — check network access for gTTS"
        )
    except Exception as e:
        logger.error(f"[VAANI TTS] Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


# ── /tts/prosody ──────────────────────────────────────────────────────────

@router.get("/prosody")
async def get_prosody(
    text: str  = Query(..., min_length=1, description="Text to analyse"),
    lang: str  = Query("en",           description="Language code"),
    tone: str  = Query("neutral",      description="Tone name"),
):
    """
    Return Vaani prosody hint for given text, language, and tone.
    Useful for frontend to preview prosody before calling /speak.
    """
    if not _VAANI_AVAILABLE:
        raise HTTPException(status_code=503, detail="VaaniTTS service not available")
    try:
        hint = generate_prosody_hint(text, lang, tone)
        return hint
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── /tts/languages ────────────────────────────────────────────────────────

@router.get("/languages")
async def get_languages():
    """
    Return all languages and their available tones from Vaani prosody_mappings.
    Frontend uses this to populate language/tone selectors.
    """
    if not _VAANI_AVAILABLE:
        raise HTTPException(status_code=503, detail="VaaniTTS service not available")
    try:
        mappings = _load_prosody_mappings()
        languages = mappings.get("languages", {})

        result = {}
        for code, data in languages.items():
            result[code] = {
                "language_name":        data.get("language_name", code),
                "language_name_native": data.get("language_name_native", code),
                "rtl":                  data.get("rtl", False),
                "default_tone":         data.get("default_tone", "neutral"),
                "tones":                list(data.get("tones", {}).keys()),
                "tone_descriptions": {
                    tone_name: tone_data.get("description", "")
                    for tone_name, tone_data in data.get("tones", {}).items()
                }
            }

        return {
            "supported_languages": result,
            "total_languages": len(result),
            "version": mappings.get("version", "1.0.0")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
