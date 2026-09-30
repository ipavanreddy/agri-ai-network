"""AI endpoints: advisory (FR-04), crop recommendation (FR-05), diagnosis (FR-06), ask (FR-08)."""

from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from app.advisory import service
from app.canonical.models import Language
from app.crops.recommend import recommend
from app.diagnosis import service as diagnosis
from app.intelligence.context import NotFound
from app.store import get_store

router = APIRouter(prefix="/api", tags=["ai"])


class AdvisoryIn(BaseModel):
    field_id: str
    language: Language = "en"
    use_sample: bool = False


class LocalizeIn(BaseModel):
    language: Language


class CropRecIn(BaseModel):
    field_id: str
    season: str | None = Field(None, pattern="^(kharif|rabi|zaid)$")
    use_sample: bool = False


class AskIn(BaseModel):
    field_id: str
    question: str = Field(min_length=1, max_length=1000)
    language: Language = "en"
    use_sample: bool = False


def _get(collection: str, doc_id: str) -> dict[str, Any]:
    doc = get_store().get(collection, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"{collection} {doc_id} not found")
    return doc


@router.post("/advisory/generate", status_code=201)
def generate_advisory(body: AdvisoryIn) -> dict[str, Any]:
    try:
        return service.generate_advisory(body.field_id, body.language, body.use_sample)
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/advisories")
def list_advisories(field_id: str | None = None) -> list[dict[str, Any]]:
    docs = get_store().list("advisories", **({"field_id": field_id} if field_id else {}))
    return sorted(docs, key=lambda d: d["generated_at"], reverse=True)


@router.get("/advisories/{advisory_id}")
def read_advisory(advisory_id: str, lang: Language = "en") -> dict[str, Any]:
    doc = _get("advisories", advisory_id)
    return {**doc, "presented": service.localize(doc, lang)}


@router.post("/advisories/{advisory_id}/localize")
def localize_advisory(advisory_id: str, body: LocalizeIn) -> dict[str, Any]:
    return service.localize(_get("advisories", advisory_id), body.language)


@router.post("/crop-recommendation", status_code=201)
def crop_recommendation(body: CropRecIn) -> dict[str, Any]:
    try:
        return recommend(body.field_id, body.season, body.use_sample)
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/diagnosis", status_code=201)
async def create_diagnosis(
    image: UploadFile = File(...),
    field_id: str | None = Form(None),
    crop: str | None = Form(None),
    growth_stage: str | None = Form(None),
) -> dict[str, Any]:
    data = await image.read(diagnosis.MAX_BYTES + 1)
    try:
        return diagnosis.diagnose(data, field_id=field_id or None, crop=crop or None, growth_stage=growth_stage or None)
    except diagnosis.InvalidImage as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/diagnoses")
def list_diagnoses(field_id: str | None = None) -> list[dict[str, Any]]:
    docs = get_store().list("diagnoses", **({"field_id": field_id} if field_id else {}))
    return sorted(docs, key=lambda d: d["created_at"], reverse=True)


@router.get("/diagnoses/{diagnosis_id}/image")
def diagnosis_image(diagnosis_id: str):
    doc = _get("diagnoses", diagnosis_id)
    if doc["image_url"].startswith("gs://"):
        # The bucket stays private: stream the object through the API (the service account can read it).
        try:
            data = diagnosis.read_gcs_image(doc["image_url"])
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"image unavailable: {type(exc).__name__}") from exc
        return Response(content=data, media_type=doc["image_mime"], headers={"Cache-Control": "private, max-age=3600"})
    path = diagnosis.local_image_path(diagnosis_id)
    if not path:
        raise HTTPException(status_code=404, detail="image not found")
    return FileResponse(path, media_type=doc["image_mime"])


@router.post("/ask")
def ask(body: AskIn) -> dict[str, Any]:
    try:
        return service.ask(body.field_id, body.question, body.language, body.use_sample)
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
