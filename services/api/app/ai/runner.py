"""Run a versioned prompt through Gemini with structured context, or fall back to labelled demo output.

Live:  GEMINI_API_KEY (or Vertex AI) set -> generate_structured() with the prompt from ai/prompts/.
Demo:  no key, or the call fails -> deterministic rule/fixture output with model_name="demo-rules".
Either way the caller gets (result, AIRecordMeta) so every stored record carries model/prompt provenance.
"""

import json
import logging
from collections.abc import Callable
from typing import Any

from google.genai import types
from pydantic import BaseModel

from app.ai import gemini
from app.canonical.models import AIRecordMeta
from app.config import settings

log = logging.getLogger(__name__)

DEMO_MODEL_NAME = "demo-rules"
DEMO_MODEL_VERSION = "demo-rules-v1 (no Gemini call)"


def build_prompt(name: str, version: str, context: dict[str, Any], extra: dict[str, Any] | None = None) -> str:
    template = gemini.load_prompt(name, version)
    payload = json.dumps(context, indent=1, default=str, ensure_ascii=False)
    sections = [template, "\n## STRUCTURED CONTEXT (the only farm data you may use)\n```json\n" + payload + "\n```"]
    for key, value in (extra or {}).items():
        sections.append(f"\n## {key}\n{value}")
    return "\n".join(sections)


def run_structured[T: BaseModel](
    name: str,
    version: str,
    schema: type[T],
    context: dict[str, Any],
    demo: Callable[[], T],
    *,
    extra: dict[str, Any] | None = None,
    parts: list[types.Part] | None = None,
) -> tuple[T, AIRecordMeta]:
    prompt_version = f"{name}_{version}"
    fallback_reason = None
    if settings.gemini_enabled:
        try:
            result, prov = gemini.generate_structured(build_prompt(name, version, context, extra), schema,
                                                      prompt_version, parts=parts)
            return result, AIRecordMeta(model_name=prov.model_name, model_version=prov.model_version,
                                        prompt_version=prov.prompt_version, generated_at=prov.generated_at, mode="live")
        except Exception as exc:
            log.exception("Gemini call failed for %s", prompt_version)
            fallback_reason = f"Gemini call failed ({type(exc).__name__}); demo output shown"
    else:
        fallback_reason = "GEMINI_API_KEY not set; demo output shown"
    return demo(), AIRecordMeta(model_name=DEMO_MODEL_NAME, model_version=DEMO_MODEL_VERSION,
                                prompt_version=prompt_version, mode="demo", fallback_reason=fallback_reason)
