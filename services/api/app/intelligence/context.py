"""Farm intelligence: assemble the canonical field context (weather + soil + satellite + farm) and Farm Health.

This structured context is the ONLY agricultural input the AI layer receives (PRD §32).
"""

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from typing import Any

from pydantic import BaseModel

from app.canonical.models import (
    Farmer,
    FarmHealth,
    Field_,
    Provenance,
    SatelliteObservation,
    SoilObservation,
    WeatherObservation,
)
from app.crops.catalog import crop_label, crop_profile, stage_at
from app.intelligence.health import compute_farm_health
from app.intelligence.satellite import get_satellite_raw, summarize
from app.intelligence.soil import get_soil
from app.intelligence.weather import get_weather, sample_weather
from app.interop.adapters import AdapterError, resolve_district, state_config
from app.store import get_store

CACHE_TTL_S = 900
_cache: dict[tuple[str, bool], tuple[float, Any]] = {}


class NotFound(LookupError):
    pass


class DataSourceInfo(BaseModel):
    category: str
    source: str
    mode: str
    is_sample: bool
    is_synthetic: bool
    reference_timestamp: datetime | None
    note: str | None = None


class FieldIntelligence(BaseModel):
    farmer: Farmer
    field: Field_
    crop: dict[str, Any]
    current_stage: dict[str, Any]
    as_of_date: date
    scenario_note: str | None
    stage_at_observation: dict[str, Any]
    weather: WeatherObservation
    soil: SoilObservation | None
    satellite: SatelliteObservation
    health: FarmHealth
    district_climate: dict[str, Any] | None
    data_sources: list[DataSourceInfo]
    demo_mode: bool
    as_of: datetime


def get_field(field_id: str) -> Field_:
    doc = get_store().get("fields", field_id)
    if not doc:
        raise NotFound(f"field {field_id} not found")
    return Field_.model_validate(doc)


def get_farmer(farmer_id: str) -> Farmer:
    doc = get_store().get("farmers", farmer_id)
    if not doc:
        raise NotFound(f"farmer {farmer_id} not found")
    return Farmer.model_validate(doc)


def latest_diagnosis(field_id: str) -> dict[str, Any] | None:
    docs = get_store().list("diagnoses", field_id=field_id)
    docs = [d for d in docs if d.get("review", {}).get("status") != "rejected"]
    return max(docs, key=lambda d: d["created_at"]) if docs else None


def invalidate(field_id: str) -> None:
    for key in [k for k in _cache if k[0] == field_id]:
        _cache.pop(key, None)


def _raw_signals(field: Field_, force_sample: bool) -> tuple[WeatherObservation, SoilObservation | None, tuple]:
    key = (field.field_id, force_sample)
    hit = _cache.get(key)
    if hit and time.monotonic() - hit[0] < CACHE_TTL_S:
        return hit[1]
    lat, lon = field.centroid.lat, field.centroid.lon
    with ThreadPoolExecutor(max_workers=3) as pool:
        fw = pool.submit(get_weather, lat, lon, field.state, force_sample)
        fs = pool.submit(get_soil, lat, lon, field.state, field.district, field.block, force_sample)
        fsat = pool.submit(get_satellite_raw, field.geometry, field.state, field.crop.sowing_date, force_sample)
        result = (fw.result(), fs.result(), fsat.result())
    _cache[key] = (time.monotonic(), result)
    return result


def _source(category: str, p: Provenance) -> DataSourceInfo:
    return DataSourceInfo(category=category, source=p.source, mode=p.mode, is_sample=p.is_sample,
                          is_synthetic=p.is_synthetic, reference_timestamp=p.reference_timestamp, note=p.note)


def build_intelligence(field_id: str, force_sample: bool = False) -> FieldIntelligence:
    field = get_field(field_id)
    farmer = get_farmer(field.farmer_id)
    weather, soil, (series, sat_prov, thumb) = _raw_signals(field, force_sample)
    crop_id = field.crop.crop_name
    profile = crop_profile(crop_id)
    today = date.today()
    obs_date = date.fromisoformat(series[-1]["date"]) if series else today
    # Sample scenarios are time-shifted: evaluate the crop at the scenario's own reference date.
    as_of = obs_date if sat_prov.is_sample and series and (today - obs_date).days > 7 else today
    scenario_note = (f"Sample scenario evaluated as of {as_of} (latest sample observation), not today"
                     if as_of != today else None)
    if (today - as_of).days > 30 and weather.provenance.mode == "live":
        # Keep a time-shifted scenario internally consistent: today's live weather would not match it.
        weather = sample_weather(field.state, f"Scenario dated {as_of}: sample weather used so signals are consistent")
    current = stage_at(crop_id, field.crop.sowing_date, as_of)
    at_obs = stage_at(crop_id, field.crop.sowing_date, obs_date)
    satellite = summarize(series, sat_prov, thumb, expected_ndvi=at_obs.get("expected_ndvi"))
    health = compute_farm_health(satellite=satellite, soil=soil, weather=weather, irrigation=field.irrigation,
                                 profile=profile, stage_at_observation=at_obs, latest_diagnosis=latest_diagnosis(field_id),
                                 as_of=as_of)
    try:
        climate = resolve_district(state_config(field.state), field.district).get("climate")
    except AdapterError:
        climate = None
    sources = [_source("weather", weather.provenance), _source("satellite", satellite.provenance)]
    if soil:
        sources.append(_source("soil", soil.provenance))
        if soil.texture_provenance:
            sources.append(_source("soil_texture", soil.texture_provenance))
    return FieldIntelligence(
        farmer=farmer, field=field,
        crop={"crop_id": crop_id, "name": crop_label(crop_id), "names": (profile or {}).get("names", {}),
              "family": (profile or {}).get("family"), "preferred_ph": (profile or {}).get("ph"),
              "season_water_need_mm": (profile or {}).get("water_mm"), "heat_stress_c": (profile or {}).get("heat_stress_c"),
              "variety": field.crop.variety, "season": field.crop.season, "sowing_date": field.crop.sowing_date},
        current_stage=current, as_of_date=as_of, scenario_note=scenario_note, stage_at_observation={**at_obs, "date": obs_date.isoformat()},
        weather=weather, soil=soil, satellite=satellite, health=health, district_climate=climate,
        data_sources=sources, demo_mode=any(s.mode == "demo" or s.is_sample for s in sources),
        as_of=datetime.now(UTC),
    )


def ai_context(intel: FieldIntelligence) -> dict[str, Any]:
    """Compact, canonical JSON context for Gemini (PRD §12 input context shape)."""
    w, s, sat, f = intel.weather, intel.soil, intel.satellite, intel.field
    return {
        "location": {"state": f.state, "district": f.district, "block": f.block, "village": f.village,
                     "lat": f.centroid.lat, "lon": f.centroid.lon},
        "crop": {**intel.crop, "current_stage": intel.current_stage, "stage_at_satellite_observation": intel.stage_at_observation},
        "farm": {"area_acres": f.area_acres, "irrigation": f.irrigation, "farming_practice": f.farming_practice},
        "soil": None if s is None else {
            **s.model_dump(mode="json", exclude={"provenance", "texture_provenance"}, exclude_none=True),
            "source": s.provenance.source, "is_sample": s.provenance.is_sample},
        "weather": {
            "current": {"temperature_c": w.temperature_c, "humidity_pct": w.humidity_pct, "wind_kmh": w.wind_kmh},
            "rain_past_14d_mm": w.rain_past_14d_mm, "rain_next_3d_mm": w.rain_next_3d_mm, "rain_next_7d_mm": w.rain_next_7d_mm,
            "tmax_next_7d_c": w.tmax_next_7d_c, "topsoil_moisture_m3_m3": w.soil_moisture_m3_m3,
            "forecast": [d.model_dump(mode="json") for d in w.daily if d.is_forecast],
            "alerts": [a.model_dump() for a in w.alerts],
            "source": w.provenance.source, "is_sample": w.provenance.is_sample,
            "reference_timestamp": w.provenance.reference_timestamp.isoformat() if w.provenance.reference_timestamp else None},
        "satellite": {"latest_ndvi": sat.latest_ndvi, "latest_ndmi": sat.latest_ndmi, "ndvi_change_30d": sat.ndvi_change_30d,
                      "vegetation_health": sat.vegetation_health, "observation_date": str(sat.observation_date),
                      "ndvi_series": [{"date": str(p.date), "ndvi": p.ndvi} for p in sat.series[-6:]],
                      "source": sat.provenance.source, "is_sample": sat.provenance.is_sample},
        "farm_health": {"score": intel.health.score, "band": intel.health.band,
                        "factors": [{"factor": x.key, "score": x.score, "drivers": x.drivers} for x in intel.health.factors],
                        "missing_factors": intel.health.missing_factors},
        "district_climate_normals": intel.district_climate,
        "today": date.today().isoformat(),
        "evaluation_date": intel.as_of_date.isoformat(),
        "scenario_note": intel.scenario_note,
    }
