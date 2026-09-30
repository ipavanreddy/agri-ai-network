"""Canonical agriculture data model (PRD §21, §22.2, §31).

State adapters map state-specific formats INTO these models; every shared service (intelligence,
Farm Health, advisory, crop recommendation, diagnosis, analytics) consumes ONLY these models.
"""

from datetime import UTC, date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Language = Literal["en", "hi", "te"]
DataMode = Literal["live", "demo"]


def utcnow() -> datetime:
    return datetime.now(UTC)


class Provenance(BaseModel):
    """Source + freshness metadata carried by every data block (PRD §36, §42)."""

    source: str
    source_url: str | None = None
    reference_timestamp: datetime | None = Field(None, description="When the data was observed/measured/forecast-issued")
    retrieved_at: datetime = Field(default_factory=utcnow)
    dataset_version: str | None = None
    geographic_scope: str | None = None
    is_sample: bool = False
    is_synthetic: bool = False
    mode: DataMode = "live"
    note: str | None = None


class GeoPoint(BaseModel):
    lat: float
    lon: float


class Farmer(BaseModel):
    farmer_id: str
    name: str
    preferred_language: Language = "en"
    state: str
    district: str
    block: str | None = None
    village: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    source_system: str = "platform"
    is_sample: bool = False


class Crop(BaseModel):
    crop_name: str = Field(description="Canonical crop id, e.g. groundnut, cotton, wheat")
    variety: str | None = None
    season: Literal["kharif", "rabi", "zaid"] | None = None
    sowing_date: date | None = None
    growth_stage: str | None = None


class Field_(BaseModel):
    """A farmer's field. (Named Field_ to avoid clashing with pydantic.Field.)"""

    field_id: str
    farmer_id: str
    name: str | None = None
    state: str
    district: str
    block: str | None = None
    village: str | None = None
    geometry: dict[str, Any] = Field(description="GeoJSON Polygon, [lon, lat] order")
    centroid: GeoPoint
    area_acres: float
    irrigation: str = "rainfed"
    farming_practice: str = "conventional"
    crop: Crop
    local_ref: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    source_system: str = "platform"
    is_sample: bool = False


class SoilObservation(BaseModel):
    sample_id: str | None = None
    ph: float | None = None
    organic_carbon_pct: float | None = None
    nitrogen_kg_ha: float | None = None
    phosphorus_kg_ha: float | None = None
    potassium_kg_ha: float | None = None
    electrical_conductivity_ds_m: float | None = None
    moisture_m3_m3: float | None = None
    clay_pct: float | None = None
    sand_pct: float | None = None
    silt_pct: float | None = None
    measurement_date: date | None = None
    provenance: Provenance
    texture_provenance: Provenance | None = None


class DailyWeather(BaseModel):
    date: date
    tmax_c: float | None = None
    tmin_c: float | None = None
    rain_mm: float | None = None
    rain_probability_pct: float | None = None
    wind_max_kmh: float | None = None
    is_forecast: bool


class WeatherAlert(BaseModel):
    code: str
    severity: Literal["low", "medium", "high"]
    message: str


class WeatherObservation(BaseModel):
    location: GeoPoint
    temperature_c: float | None = None
    humidity_pct: float | None = None
    wind_kmh: float | None = None
    precipitation_mm: float | None = None
    soil_moisture_m3_m3: float | None = None
    daily: list[DailyWeather] = []
    rain_past_14d_mm: float | None = None
    rain_next_3d_mm: float | None = None
    rain_next_7d_mm: float | None = None
    tmax_next_7d_c: float | None = None
    alerts: list[WeatherAlert] = []
    timestamp: datetime | None = None
    provenance: Provenance


class NdviPoint(BaseModel):
    date: date
    ndvi: float
    ndmi: float | None = None
    valid_fraction: float | None = None


class SatelliteObservation(BaseModel):
    series: list[NdviPoint] = []
    latest_ndvi: float | None = None
    latest_ndmi: float | None = None
    ndvi_change_30d: float | None = None
    vegetation_health: Literal["good", "moderate", "poor", "unknown"] = "unknown"
    observation_date: date | None = None
    thumbnail_url: str | None = None
    provenance: Provenance


class HealthFactor(BaseModel):
    key: Literal["vegetation", "soil", "weather", "water", "crop_condition"]
    label: str
    weight: float
    score: float | None = Field(None, description="0-100; None when inputs are missing")
    status: Literal["good", "moderate", "poor", "missing"]
    drivers: list[str] = []
    inputs: dict[str, Any] = {}


class FarmHealth(BaseModel):
    score: int
    band: Literal["Good", "Moderate", "Poor"]
    factors: list[HealthFactor]
    weights: dict[str, float]
    effective_weights: dict[str, float]
    missing_factors: list[str] = []
    method: str = "farm_health_rules_v1"
    computed_at: datetime = Field(default_factory=utcnow)


class AIRecordMeta(BaseModel):
    """Provenance stored on every AI-generated record (CLAUDE.md non-negotiable)."""

    model_name: str
    model_version: str
    prompt_version: str
    generated_at: datetime = Field(default_factory=utcnow)
    mode: DataMode
    fallback_reason: str | None = None


ReviewStatus = Literal["pending_officer_review", "approved", "rejected"]


class Review(BaseModel):
    status: ReviewStatus = "pending_officer_review"
    reviewer: str | None = None
    note: str | None = None
    reviewed_at: datetime | None = None
