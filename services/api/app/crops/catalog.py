"""Crop knowledge base (data/sample/crops/crop_catalog.json) + growth-stage helpers."""

from datetime import date
from typing import Any

from app.sample_data import load_sample


def catalog() -> dict[str, dict[str, Any]]:
    return {c["crop_id"]: c for c in load_sample("crops/crop_catalog.json")["crops"]}


def catalog_meta() -> dict[str, Any]:
    return load_sample("crops/crop_catalog.json")["_meta"]


def crop_profile(crop_id: str) -> dict[str, Any] | None:
    return catalog().get(crop_id)


def crop_label(crop_id: str, lang: str = "en") -> str:
    p = crop_profile(crop_id)
    return p["names"].get(lang, p["names"]["en"]) if p else crop_id.replace("_", " ").title()


def stage_at(crop_id: str, sowing: date | None, on: date) -> dict[str, Any]:
    """Growth stage (and expected NDVI) at a given date, from days after sowing."""
    p = crop_profile(crop_id)
    if not p or not sowing:
        return {"stage": "unknown", "days_after_sowing": None, "expected_ndvi": None}
    das = (on - sowing).days
    if das < 0:
        return {"stage": "not_sown", "days_after_sowing": das, "expected_ndvi": None}
    for s in p["stages"]:
        if s["from_day"] <= das < s["to_day"]:
            return {"stage": s["stage"], "days_after_sowing": das, "expected_ndvi": s["expected_ndvi"]}
    return {"stage": "harvested_or_season_complete", "days_after_sowing": das, "expected_ndvi": None}


def season_for(d: date) -> str:
    return "kharif" if 6 <= d.month <= 9 else "rabi" if d.month >= 10 or d.month <= 2 else "zaid"
