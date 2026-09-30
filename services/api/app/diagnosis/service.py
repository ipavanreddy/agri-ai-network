"""AI Crop Doctor (PRD §16, §34.2): image validation -> Gemini multimodal -> potential condition.

Always an AI-assisted PRELIMINARY assessment. Images go to Cloud Storage when GCS_BUCKET is set,
otherwise to services/api/.data/uploads/.
"""

import hashlib
import logging
import uuid
from datetime import date
from pathlib import Path
from typing import Any

from google.genai import types

from app.ai.runner import run_structured
from app.ai.schemas import DiagnosisAI, PotentialCondition
from app.canonical.models import Review, utcnow
from app.config import settings
from app.crops.catalog import crop_label, stage_at
from app.intelligence.context import get_field
from app.sample_data import load_sample
from app.store import get_store

log = logging.getLogger(__name__)

MAX_BYTES = 8 * 1024 * 1024
MIN_BYTES = 256
DISCLAIMER = ("AI-assisted preliminary assessment, not a certified diagnosis. Confirm with your local agriculture "
              "officer or KVK before acting, especially before any chemical treatment.")
EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


class InvalidImage(ValueError):
    pass


def sniff_mime(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_image(data: bytes) -> str:
    if len(data) < MIN_BYTES:
        raise InvalidImage("image is empty or too small")
    if len(data) > MAX_BYTES:
        raise InvalidImage("image is larger than 8 MB")
    mime = sniff_mime(data)
    if not mime:
        raise InvalidImage("unsupported image type (use JPEG, PNG or WebP)")
    return mime


def store_image(diagnosis_id: str, data: bytes, mime: str) -> str:
    name = f"diagnoses/{diagnosis_id}.{EXT[mime]}"
    if settings.gcs_enabled:
        try:
            from google.cloud import storage

            blob = storage.Client(project=settings.google_cloud_project or None).bucket(settings.gcs_bucket).blob(name)
            blob.upload_from_string(data, content_type=mime)
            return f"gs://{settings.gcs_bucket}/{name}"
        except Exception as exc:
            log.warning("GCS upload failed, storing locally: %s", exc)
    path = Path(settings.upload_dir) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return f"/api/diagnoses/{diagnosis_id}/image"


def read_gcs_image(gs_url: str) -> bytes:
    from google.cloud import storage

    bucket, _, name = gs_url.removeprefix("gs://").partition("/")
    return storage.Client(project=settings.google_cloud_project or None).bucket(bucket).blob(name).download_as_bytes()


def local_image_path(diagnosis_id: str) -> Path | None:
    for ext in EXT.values():
        p = Path(settings.upload_dir) / "diagnoses" / f"{diagnosis_id}.{ext}"
        if p.exists():
            return p
    return None


def demo_diagnosis(crop: str) -> DiagnosisAI:
    fixtures = load_sample("diagnosis/fixtures.json")["by_crop"]
    fx = fixtures.get(crop, fixtures["_default"])
    return DiagnosisAI(
        image_usable=True, image_issue="", plant_part=fx["plant_part"],
        potential_conditions=[PotentialCondition(**c) for c in fx["potential_conditions"]],
        visible_symptoms=fx["visible_symptoms"], severity=fx["severity"], confidence=fx["confidence"],
        recommended_next_actions=fx["recommended_next_actions"], requires_expert_review=True,
        explanation=f"DEMO MODE: fixed example output for {crop_label(crop)}. The uploaded image was NOT analysed "
                    "(set GEMINI_API_KEY for real multimodal analysis).",
    )


def diagnose(image: bytes, *, field_id: str | None, crop: str | None, growth_stage: str | None) -> dict[str, Any]:
    mime = validate_image(image)
    field = get_field(field_id) if field_id else None  # raises NotFound for unknown ids
    crop = crop or (field.crop.crop_name if field else "unknown")
    if field and not growth_stage:
        growth_stage = stage_at(crop, field.crop.sowing_date, date.today())["stage"]
    context = {"crop": crop, "crop_name": crop_label(crop), "growth_stage": growth_stage,
               "location": {"state": field.state, "district": field.district} if field else None}
    result, meta = run_structured("diagnosis", "v1", DiagnosisAI, context, lambda: demo_diagnosis(crop),
                                  parts=[types.Part.from_bytes(data=image, mime_type=mime)])
    result.confidence = max(0.0, min(1.0, result.confidence))
    for c in result.potential_conditions:
        c.likelihood = max(0.0, min(1.0, c.likelihood))
    if result.confidence < 0.6 or result.severity in ("high", "unknown") or not result.image_usable:
        result.requires_expert_review = True
    diagnosis_id = f"DX-{uuid.uuid4().hex[:10]}"
    top = result.potential_conditions[0] if result.potential_conditions else None
    record = {
        "diagnosis_id": diagnosis_id, "field_id": field_id, "farmer_id": field.farmer_id if field else None,
        "state": field.state if field else None, "district": field.district if field else None,
        "crop": crop, "growth_stage": growth_stage,
        "image_url": store_image(diagnosis_id, image, mime), "image_sha256": hashlib.sha256(image).hexdigest(),
        "image_mime": mime, "result": result.model_dump(mode="json"),
        "potential_condition": top.name if top else "No clear condition identified",
        "confidence": result.confidence, "severity": result.severity,
        "recommendation": result.recommended_next_actions[0] if result.recommended_next_actions else "",
        "disclaimer": DISCLAIMER, "ai": meta.model_dump(mode="json"), "model_name": meta.model_name,
        "model_version": meta.model_version, "prompt_version": meta.prompt_version,
        "review": Review().model_dump(mode="json"), "created_at": utcnow().isoformat(), "demo_mode": meta.mode == "demo",
    }
    get_store().put("diagnoses", diagnosis_id, record)
    return record
