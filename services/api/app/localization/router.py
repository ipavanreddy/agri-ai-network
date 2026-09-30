"""Language / voice endpoints (PRD §17-18, §37)."""

from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.canonical.models import Language
from app.localization import service

router = APIRouter(prefix="/api", tags=["localization"])


class TranslateIn(BaseModel):
    texts: list[str] = Field(max_length=100)
    target: Language
    source: Language = "en"


class TtsIn(BaseModel):
    text: str = Field(min_length=1, max_length=4500)
    language: Language = "en"


@router.post("/translate")
def translate(body: TranslateIn) -> dict[str, Any]:
    try:
        out = service.translate_texts(body.texts, body.target, body.source)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"translation failed: {type(exc).__name__}") from exc
    if out is None:
        return {"translations": body.texts, "method": "unavailable", "mode": "demo",
                "note": "No translator configured (set GOOGLE_CLOUD_API_KEY or GEMINI_API_KEY). Demo advisories are "
                        "localised from the built-in message catalogue instead."}
    translations, method = out
    return {"translations": translations, "method": method, "mode": "live"}


@router.post("/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...), language: Language = Form("en")) -> dict[str, Any]:
    data = await audio.read(10 * 1024 * 1024)
    try:
        return service.speech_to_text(data, language, audio.content_type or "audio/webm")
    except service.NotConfigured:
        return {"transcript": None, "mode": "demo", "use_browser_speech": True,
                "note": "Cloud Speech-to-Text not configured (GOOGLE_CLOUD_API_KEY). Use the browser's speech recognition."}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"speech-to-text failed: {type(exc).__name__}") from exc


@router.post("/text-to-speech")
def text_to_speech(body: TtsIn) -> dict[str, Any]:
    try:
        return service.text_to_speech(body.text, body.language)
    except service.NotConfigured:
        return {"audio_base64": None, "mode": "demo", "use_browser_tts": True,
                "note": "Cloud Text-to-Speech not configured (GOOGLE_CLOUD_API_KEY). Use the browser's speech synthesis."}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"text-to-speech failed: {type(exc).__name__}") from exc
