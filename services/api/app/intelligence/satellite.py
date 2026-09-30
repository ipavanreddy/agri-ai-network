"""Satellite adapter: Google Earth Engine Sentinel-2 NDVI/NDMI time series for a field polygon.

Live when EARTH_ENGINE_PROJECT is set (credentials via ADC or GOOGLE_APPLICATION_CREDENTIALS service
account). Otherwise a labelled sample series in the same output shape is returned.
"""

import json
import logging
import os
from datetime import UTC, date, datetime, timedelta
from functools import lru_cache
from typing import Any

from app.canonical.models import NdviPoint, Provenance, SatelliteObservation
from app.config import settings
from app.sample_data import load_sample, sample_provenance

log = logging.getLogger(__name__)

S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
# Sentinel-2 Scene Classification: 4 vegetation, 5 bare soil, 6 water, 7 unclassified (cloud/shadow/snow excluded)
CLEAR_SCL_CLASSES = (4, 5, 6, 7)
NDVI_PALETTE = ["#a50026", "#f46d43", "#fee08b", "#d9ef8b", "#66bd63", "#006837"]


@lru_cache
def _init_earth_engine() -> None:
    import ee

    key_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if key_file and os.path.exists(key_file):
        with open(key_file) as fh:
            email = json.load(fh).get("client_email")
        credentials = ee.ServiceAccountCredentials(email, key_file)
        ee.Initialize(credentials, project=settings.earth_engine_project)
    else:
        ee.Initialize(project=settings.earth_engine_project)


def fetch_ndvi_series_ee(geometry: dict[str, Any], start: date, end: date) -> dict[str, Any]:
    """Per-scene field-mean NDVI/NDMI over clear pixels + an NDVI thumbnail of the latest 20 days."""
    import ee

    _init_earth_engine()
    geom = ee.Geometry(geometry)
    scl_clear = lambda img: img.select("SCL").remap(list(CLEAR_SCL_CLASSES), [1] * len(CLEAR_SCL_CLASSES), 0)

    collection = (
        ee.ImageCollection(S2_COLLECTION)
        .filterBounds(geom)
        .filterDate(start.isoformat(), (end + timedelta(days=1)).isoformat())
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 70))
    )

    def with_indices(img):
        clear = scl_clear(img)
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("ndvi")
        ndmi = img.normalizedDifference(["B8", "B11"]).rename("ndmi")
        return ndvi.addBands(ndmi).updateMask(clear).set("system:time_start", img.get("system:time_start")) \
            .set("clear_fraction", clear.reduceRegion(ee.Reducer.mean(), geom, 20, maxPixels=1e8).get("remapped"))

    def to_feature(img):
        stats = img.reduceRegion(ee.Reducer.mean(), geom, 10, maxPixels=1e8)
        return ee.Feature(None, {
            "date": ee.Date(img.get("system:time_start")).format("YYYY-MM-dd"),
            "ndvi": stats.get("ndvi"),
            "ndmi": stats.get("ndmi"),
            "valid_fraction": img.get("clear_fraction"),
        })

    indexed = collection.map(with_indices)
    features = ee.FeatureCollection(indexed.map(to_feature)).filter(ee.Filter.notNull(["ndvi"])).getInfo()

    thumbnail_url = None
    try:
        recent = indexed.filterDate((end - timedelta(days=20)).isoformat(), (end + timedelta(days=1)).isoformat())
        thumbnail_url = recent.select("ndvi").median().clip(geom).getThumbURL({
            "min": 0.0, "max": 0.9, "palette": NDVI_PALETTE, "region": geom.buffer(40).bounds(), "dimensions": 256,
        })
    except Exception as exc:  # thumbnail is optional
        log.info("NDVI thumbnail unavailable: %s", exc)
    return {"collection": S2_COLLECTION, "series": parse_ee_features(features), "thumbnail_url": thumbnail_url}


def parse_ee_features(fc_info: dict[str, Any]) -> list[dict[str, Any]]:
    """Collapse overlapping tiles to one value per date (mean), sorted by date; drop low-coverage scenes."""
    by_date: dict[str, list[dict[str, Any]]] = {}
    for f in fc_info.get("features", []):
        p = f.get("properties", {})
        if p.get("ndvi") is None or (p.get("valid_fraction") is not None and p["valid_fraction"] < 0.3):
            continue
        by_date.setdefault(p["date"], []).append(p)

    def mean(rows: list[dict[str, Any]], key: str) -> float | None:
        vals = [r[key] for r in rows if r.get(key) is not None]
        return round(sum(vals) / len(vals), 3) if vals else None

    return [{"date": d, **{k: mean(by_date[d], k) for k in ("ndvi", "ndmi", "valid_fraction")}} for d in sorted(by_date)]


def summarize(series: list[dict[str, Any]], provenance: Provenance, thumbnail_url: str | None = None,
              expected_ndvi: float | None = None) -> SatelliteObservation:
    points = [NdviPoint(**p) for p in series]
    if not points:
        return SatelliteObservation(provenance=provenance, thumbnail_url=thumbnail_url)
    latest = points[-1]
    earlier = [p for p in points if (latest.date - p.date).days >= 25]
    change = round(latest.ndvi - earlier[-1].ndvi, 3) if earlier else None
    if expected_ndvi:
        ratio = latest.ndvi / expected_ndvi
        health = "good" if ratio >= 0.9 else "moderate" if ratio >= 0.7 else "poor"
    else:
        health = "good" if latest.ndvi >= 0.6 else "moderate" if latest.ndvi >= 0.4 else "poor"
    return SatelliteObservation(
        series=points, latest_ndvi=latest.ndvi, latest_ndmi=latest.ndmi, ndvi_change_30d=change,
        vegetation_health=health, observation_date=latest.date, thumbnail_url=thumbnail_url, provenance=provenance,
    )


def sample_series(state: str) -> tuple[list[dict[str, Any]], Provenance]:
    payload = load_sample(f"satellite/{state}.json")
    return payload["series"], sample_provenance(payload["_meta"])


def get_satellite_raw(geometry: dict[str, Any], state: str, sowing: date | None,
                      force_sample: bool = False) -> tuple[list[dict[str, Any]], Provenance, str | None]:
    if settings.earth_engine_enabled and not force_sample:
        end = date.today()
        start = max(sowing - timedelta(days=15), end - timedelta(days=180)) if sowing and sowing < end else end - timedelta(days=90)
        try:
            out = fetch_ndvi_series_ee(geometry, start, end)
            ref = out["series"][-1]["date"] if out["series"] else None
            return out["series"], Provenance(
                source="Google Earth Engine - Sentinel-2 SR Harmonized (Copernicus), field-mean NDVI/NDMI",
                source_url="https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED",
                reference_timestamp=datetime.fromisoformat(ref).replace(tzinfo=UTC) if ref else None,
                geographic_scope="field polygon", mode="live",
            ), out["thumbnail_url"]
        except Exception as exc:
            log.warning("Earth Engine unavailable: %s", exc)
            series, prov = sample_series(state)
            return series, prov.model_copy(update={"note": f"Earth Engine call failed ({type(exc).__name__}); sample series shown"}), None
    series, prov = sample_series(state)
    note = "Sample NDVI series for the demo scenario (EARTH_ENGINE_PROJECT not set)"
    return series, prov.model_copy(update={"note": note}), None
