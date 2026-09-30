"""Localisation adapters: Cloud Translation, Speech-to-Text, Text-to-Speech (REST, GOOGLE_CLOUD_API_KEY),
with Gemini as a translation fallback. Without keys, callers fall back to the demo message catalogue
(server) and browser Web Speech APIs (client), clearly labelled as demo mode.
"""

import base64
import json
from typing import Any

import httpx

from app.ai import gemini
from app.ai.schemas import TranslationAI
from app.config import settings

SUPPORTED_LANGUAGES = {"en": "English", "hi": "Hindi", "te": "Telugu"}
LOCALE = {"en": "en-IN", "hi": "hi-IN", "te": "te-IN"}
TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"
STT_URL = "https://speech.googleapis.com/v1/speech:recognize"
TTS_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"
TIMEOUT = 20.0


class NotConfigured(RuntimeError):
    pass


def translation_mode() -> str:
    if settings.google_cloud_api_key:
        return "cloud_translation"
    if settings.gemini_enabled:
        return "gemini"
    return "demo_catalog"


def translate_texts(texts: list[str], target: str, source: str = "en") -> tuple[list[str], str] | None:
    """Translate a list of strings. Returns (translations, method) or None if no translator is configured."""
    if target == source or not texts:
        return list(texts), "noop"
    if settings.google_cloud_api_key:
        res = httpx.post(TRANSLATE_URL, params={"key": settings.google_cloud_api_key},
                         json={"q": texts, "target": target, "source": source, "format": "text"}, timeout=TIMEOUT)
        res.raise_for_status()
        return [t["translatedText"] for t in res.json()["data"]["translations"]], "cloud_translation"
    if settings.gemini_enabled:
        prompt = (gemini.load_prompt("translate", "v1")
                  + f"\n\nTARGET_LANGUAGE: {SUPPORTED_LANGUAGES.get(target, target)}\nSOURCE_TEXTS:\n"
                  + json.dumps(texts, ensure_ascii=False))
        result, _ = gemini.generate_structured(prompt, TranslationAI, "translate_v1")
        if len(result.translations) == len(texts):
            return result.translations, "gemini"
    return None


def speech_to_text(audio: bytes, language: str, mime_type: str) -> dict[str, Any]:
    if not settings.cloud_speech_enabled:
        raise NotConfigured("GOOGLE_CLOUD_API_KEY not set")
    encoding = "WEBM_OPUS" if "webm" in mime_type else "OGG_OPUS" if "ogg" in mime_type else "LINEAR16" if "wav" in mime_type else "MP3"
    config: dict[str, Any] = {"encoding": encoding, "languageCode": LOCALE.get(language, "en-IN"),
                              "enableAutomaticPunctuation": True,
                              "alternativeLanguageCodes": [v for k, v in LOCALE.items() if k != language]}
    if encoding in ("WEBM_OPUS", "OGG_OPUS"):
        config["sampleRateHertz"] = 48000
    res = httpx.post(STT_URL, params={"key": settings.google_cloud_api_key},
                     json={"config": config, "audio": {"content": base64.b64encode(audio).decode()}}, timeout=TIMEOUT)
    res.raise_for_status()
    results = res.json().get("results", [])
    alt = results[0]["alternatives"][0] if results else {"transcript": "", "confidence": 0}
    return {"transcript": alt.get("transcript", ""), "confidence": alt.get("confidence"), "mode": "live",
            "engine": "Google Cloud Speech-to-Text v1"}


def text_to_speech(text: str, language: str) -> dict[str, Any]:
    if not settings.cloud_speech_enabled:
        raise NotConfigured("GOOGLE_CLOUD_API_KEY not set")
    res = httpx.post(TTS_URL, params={"key": settings.google_cloud_api_key},
                     json={"input": {"text": text[:4500]}, "voice": {"languageCode": LOCALE.get(language, "en-IN")},
                           "audioConfig": {"audioEncoding": "MP3"}}, timeout=TIMEOUT)
    res.raise_for_status()
    return {"audio_base64": res.json()["audioContent"], "mime_type": "audio/mpeg", "mode": "live",
            "engine": "Google Cloud Text-to-Speech v1"}
