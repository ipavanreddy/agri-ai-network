"""Farmer & field management (PRD §9.1, FR-01/02) and field intelligence endpoints (FR-03, §37)."""

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.canonical.models import Crop, Farmer, Field_, GeoPoint, Language
from app.crops.catalog import crop_profile, season_for, stage_at
from app.farms import geo
from app.intelligence import context
from app.interop.adapters import AdapterError, resolve_district, state_config
from app.store import get_store

router = APIRouter(prefix="/api", tags=["farms"])


class FarmerIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    preferred_language: Language = "en"
    state: str
    district: str
    block: str | None = None
    village: str | None = None


class FieldIn(BaseModel):
    farmer_id: str
    name: str | None = None
    geometry: dict[str, Any]
    crop_name: str
    variety: str | None = None
    sowing_date: date | None = None
    irrigation: str = "rainfed"
    farming_practice: str = "conventional"
    area_acres: float | None = Field(None, gt=0, le=1000)


class LanguageIn(BaseModel):
    preferred_language: Language


def _404(exc: Exception) -> HTTPException:
    return HTTPException(status_code=404, detail=str(exc))


@router.post("/farmers", response_model=Farmer, status_code=201)
def create_farmer(body: FarmerIn) -> Farmer:
    try:
        cfg = state_config(body.state)
        district = resolve_district(cfg, body.district)["name"]
    except AdapterError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    farmer = Farmer(farmer_id=f"F-{uuid.uuid4().hex[:8]}", name=body.name, preferred_language=body.preferred_language,
                    state=cfg["state_id"], district=district, block=body.block, village=body.village)
    get_store().put("farmers", farmer.farmer_id, farmer.model_dump(mode="json"))
    return farmer


@router.get("/farmers", response_model=list[Farmer])
def list_farmers(state: str | None = None) -> list[Farmer]:
    docs = get_store().list("farmers", **({"state": state.upper()} if state else {}))
    return [Farmer.model_validate(d) for d in docs]


@router.get("/farmers/{farmer_id}", response_model=Farmer)
def read_farmer(farmer_id: str) -> Farmer:
    try:
        return context.get_farmer(farmer_id)
    except context.NotFound as exc:
        raise _404(exc) from exc


@router.patch("/farmers/{farmer_id}", response_model=Farmer)
def update_farmer_language(farmer_id: str, body: LanguageIn) -> Farmer:
    try:
        farmer = context.get_farmer(farmer_id)
    except context.NotFound as exc:
        raise _404(exc) from exc
    farmer.preferred_language = body.preferred_language
    get_store().put("farmers", farmer_id, farmer.model_dump(mode="json"))
    return farmer


@router.post("/fields", response_model=Field_, status_code=201)
def create_field(body: FieldIn) -> Field_:
    try:
        farmer = context.get_farmer(body.farmer_id)
    except context.NotFound as exc:
        raise _404(exc) from exc
    profile = crop_profile(body.crop_name)
    if not profile:
        raise HTTPException(status_code=422, detail=f"unknown crop '{body.crop_name}'")
    if body.crop_name not in state_config(farmer.state)["supported_crops"]:
        raise HTTPException(status_code=422, detail=f"'{body.crop_name}' is not configured for {farmer.state}")
    try:
        geometry = geo.normalize(body.geometry)
        area = body.area_acres or geo.area_acres(geometry)
        lat, lon = geo.centroid(geometry)
    except geo.GeometryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    season = season_for(body.sowing_date) if body.sowing_date else profile["seasons"][0]
    if season not in profile["seasons"]:
        season = profile["seasons"][0]
    field = Field_(
        field_id=f"FLD-{uuid.uuid4().hex[:8]}", farmer_id=farmer.farmer_id,
        name=body.name or f"{farmer.village or farmer.district} field", state=farmer.state, district=farmer.district,
        block=farmer.block, village=farmer.village, geometry=geometry, centroid=GeoPoint(lat=lat, lon=lon), area_acres=area,
        irrigation=body.irrigation, farming_practice=body.farming_practice,
        crop=Crop(crop_name=body.crop_name, variety=body.variety, season=season, sowing_date=body.sowing_date,
                  growth_stage=stage_at(body.crop_name, body.sowing_date, date.today())["stage"]),
    )
    get_store().put("fields", field.field_id, field.model_dump(mode="json"))
    return field


@router.get("/fields", response_model=list[Field_])
def list_fields(farmer_id: str | None = None, state: str | None = None) -> list[Field_]:
    where: dict[str, Any] = {}
    if farmer_id:
        where["farmer_id"] = farmer_id
    if state:
        where["state"] = state.upper()
    return [Field_.model_validate(d) for d in get_store().list("fields", **where)]


@router.get("/fields/{field_id}", response_model=Field_)
def read_field(field_id: str) -> Field_:
    try:
        return context.get_field(field_id)
    except context.NotFound as exc:
        raise _404(exc) from exc


def _intel(field_id: str, sample: bool) -> context.FieldIntelligence:
    try:
        return context.build_intelligence(field_id, force_sample=sample)
    except context.NotFound as exc:
        raise _404(exc) from exc


SampleQ = Query(False, description="true = force labelled sample data (offline demo)")


@router.get("/fields/{field_id}/intelligence", response_model=context.FieldIntelligence)
def field_intelligence(field_id: str, sample: bool = SampleQ) -> context.FieldIntelligence:
    return _intel(field_id, sample)


@router.get("/fields/{field_id}/weather")
def field_weather(field_id: str, sample: bool = SampleQ):
    return _intel(field_id, sample).weather


@router.get("/fields/{field_id}/soil")
def field_soil(field_id: str, sample: bool = SampleQ):
    return _intel(field_id, sample).soil


@router.get("/fields/{field_id}/satellite")
def field_satellite(field_id: str, sample: bool = SampleQ):
    return _intel(field_id, sample).satellite


@router.get("/fields/{field_id}/health")
def field_health(field_id: str, sample: bool = SampleQ):
    intel = _intel(field_id, sample)
    return {"field_id": field_id, "health": intel.health, "data_sources": intel.data_sources, "demo_mode": intel.demo_mode}
