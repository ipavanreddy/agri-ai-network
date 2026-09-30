"""Agriculture Officer endpoints: analytics (FR-09) and human review of AI outputs."""

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.analytics import service
from app.interop.adapters import AdapterError

router = APIRouter(prefix="/api", tags=["officer"])


class ReviewIn(BaseModel):
    decision: Literal["approve", "reject"]
    reviewer: str = Field("Agriculture Officer (demo)", max_length=120)
    note: str | None = Field(None, max_length=1000)


@router.get("/overview")
def india_overview() -> dict[str, Any]:
    return service.overview()


@router.get("/states/{state_id}/analytics")
def state_analytics(state_id: str) -> dict[str, Any]:
    try:
        return service.state_analytics(state_id)
    except AdapterError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/districts/{district_id}/risks")
def district_risks(district_id: str) -> dict[str, Any]:
    out = service.district_risks(district_id)
    if not out:
        raise HTTPException(status_code=404, detail=f"district {district_id} not found")
    return out


@router.get("/review-queue")
def review_queue(status: str | None = "pending_officer_review") -> list[dict[str, Any]]:
    items = service.review_queue()
    return [i for i in items if not status or i["review"]["status"] == status]


@router.post("/reviews/{kind}/{doc_id}")
def review(kind: Literal["advisories", "diagnoses", "crop_recommendations"], doc_id: str, body: ReviewIn) -> dict[str, Any]:
    doc = service.review(kind, doc_id, body.decision, body.reviewer, body.note)
    if not doc:
        raise HTTPException(status_code=404, detail=f"{kind} {doc_id} not found")
    return {"id": doc_id, "kind": kind, "review": doc["review"]}
