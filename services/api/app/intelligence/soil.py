"""Soil adapter.

Primary: state Soil Health Card style records (NPK, pH, OC), mapped to canonical form by the state adapter.
Secondary: ISRIC SoilGrids 2.0 (keyless REST, modelled 250 m) for texture, and for pH/OC only when no
state record exists. Sample texture fixtures are used when SoilGrids is unreachable or disabled.
"""

import logging
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

import httpx

from app.canonical.models import Provenance, SoilObservation
from app.config import settings
from app.interop.adapters import soil_for
from app.sample_data import load_sample, sample_provenance

log = logging.getLogger(__name__)

SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
# SoilGrids mapped units -> conventional units (https://www.isric.org/explore/soilgrids/faq-soilgrids)
CONVERSIONS = {"phh2o": 0.1, "soc": 0.01, "clay": 0.1, "sand": 0.1, "silt": 0.1}  # pH, %, %, %, %


@lru_cache(maxsize=256)
def fetch_soilgrids(lat: float, lon: float) -> dict[str, float]:
    """Modelled soil properties are static, so successful lookups are cached per point."""
    params: list[tuple[str, Any]] = [("lat", lat), ("lon", lon), ("value", "mean")]
    params += [("property", p) for p in CONVERSIONS] + [("depth", "0-5cm"), ("depth", "5-15cm")]
    res = httpx.get(SOILGRIDS_URL, params=params, timeout=min(settings.public_api_timeout_s, 5.0))
    res.raise_for_status()
    return parse_soilgrids(res.json())


def parse_soilgrids(payload: dict[str, Any]) -> dict[str, float]:
    """Mean of the 0-5 and 5-15 cm layers, converted to conventional units."""
    out: dict[str, float] = {}
    for layer in payload.get("properties", {}).get("layers", []):
        name = layer["name"]
        vals = [d["values"].get("mean") for d in layer.get("depths", []) if d["values"].get("mean") is not None]
        if name in CONVERSIONS and vals:
            out[name] = round(sum(vals) / len(vals) * CONVERSIONS[name], 2)
    return out


def get_soil(lat: float, lon: float, state: str, district: str, block: str | None,
             force_sample: bool = False) -> SoilObservation | None:
    obs = soil_for(state, district, block)
    grids: dict[str, float] = {}
    grids_prov: Provenance | None = None
    if settings.use_public_apis and not force_sample:
        try:
            grids = fetch_soilgrids(lat, lon)
            grids_prov = Provenance(source="ISRIC SoilGrids 2.0 (modelled, 250 m, 0-15 cm)",
                                    source_url="https://soilgrids.org", reference_timestamp=datetime(2020, 1, 1, tzinfo=UTC),
                                    retrieved_at=datetime.now(UTC), dataset_version="2.0",
                                    geographic_scope=f"{lat:.4f},{lon:.4f}", mode="live")
        except Exception as exc:
            log.warning("SoilGrids unavailable: %s", exc)
    if not grids:
        fixture = load_sample(f"soilgrids/{state}.json")
        grids = {"clay": fixture["clay_pct"], "sand": fixture["sand_pct"], "silt": fixture["silt_pct"]}
        grids_prov = sample_provenance(fixture["_meta"])

    texture = {"clay_pct": grids.get("clay"), "sand_pct": grids.get("sand"), "silt_pct": grids.get("silt")}
    if obs is not None:
        return obs.model_copy(update={**texture, "texture_provenance": grids_prov})
    if "phh2o" in grids:  # no state record: fall back to modelled SoilGrids pH / organic carbon
        return SoilObservation(ph=grids["phh2o"], organic_carbon_pct=grids.get("soc"), **texture,
                               provenance=grids_prov, texture_provenance=grids_prov)
    return None
