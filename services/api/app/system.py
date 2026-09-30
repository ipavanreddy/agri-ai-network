"""Integration status (drives the UI "Demo mode" badges) and demo seeding through the state adapters."""

import logging
from typing import Any

from fastapi import APIRouter

from app.config import settings
from app.interop.adapters import load_state_dataset, state_configs
from app.store import get_store, store_status

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["system"])


def integrations() -> list[dict[str, Any]]:
    store = store_status()
    rows = [
        ("gemini", "Gemini (advisory, crop doctor, Q&A)", settings.gemini_enabled, "GEMINI_API_KEY or GOOGLE_GENAI_USE_VERTEXAI+GOOGLE_CLOUD_PROJECT",
         f"model={settings.gemini_model}" if settings.gemini_enabled else "Rule-based demo outputs; Crop Doctor returns fixtures"),
        ("earth_engine", "Earth Engine (Sentinel-2 NDVI)", settings.earth_engine_enabled, "EARTH_ENGINE_PROJECT (+ ADC / GOOGLE_APPLICATION_CREDENTIALS)",
         "Live field polygon time series" if settings.earth_engine_enabled else "Sample NDVI series per state scenario"),
        ("weather", "Weather (Open-Meteo, keyless)", settings.use_public_apis, "USE_PUBLIC_APIS=true (default)",
         "Live forecast + 14-day history; sample fallback if unreachable" if settings.use_public_apis else "Sample weather"),
        ("soilgrids", "Soil texture (ISRIC SoilGrids, keyless)", settings.use_public_apis, "USE_PUBLIC_APIS=true (default)",
         "Soil NPK/pH/OC always from state Soil Health Card sample records (via adapters)"),
        ("translation", "Cloud Translation", bool(settings.google_cloud_api_key), "GOOGLE_CLOUD_API_KEY",
         "Gemini translation" if settings.gemini_enabled and not settings.google_cloud_api_key else
         "Live" if settings.google_cloud_api_key else "Built-in en/hi/te message catalogue"),
        ("speech", "Cloud Speech-to-Text / Text-to-Speech", settings.cloud_speech_enabled, "GOOGLE_CLOUD_API_KEY",
         "Live" if settings.cloud_speech_enabled else "Browser Web Speech API fallback"),
        ("store", "Firestore", store["mode"] == "live", "FIREBASE_PROJECT_ID (+ ADC)", store["note"] or
         ("Live" if store["mode"] == "live" else "Local SQLite (services/api/.data/)")),
        ("bigquery", "BigQuery regional analytics", settings.bigquery_enabled, "GOOGLE_CLOUD_PROJECT + BIGQUERY_DATASET",
         "Queries district_indicators (falls back to sample if table missing)" if settings.bigquery_enabled else "Synthetic district sample"),
        ("storage", "Cloud Storage (images)", settings.gcs_enabled, "GCS_BUCKET",
         "Live" if settings.gcs_enabled else "Local disk (services/api/.data/uploads)"),
        ("maps", "Google Maps (browser)", None, "NEXT_PUBLIC_MAPS_API_KEY (apps/*/.env.local)",
         "Configured per app; OpenStreetMap + Leaflet fallback"),
    ]
    return [{"key": k, "label": label, "mode": None if live is None else ("live" if live else "demo"), "env": env, "detail": detail}
            for k, label, live, env, detail in rows]


@router.get("/system/status")
def system_status() -> dict[str, Any]:
    items = integrations()
    return {"integrations": items, "demo_mode": any(i["mode"] == "demo" for i in items if i["key"] in ("gemini", "earth_engine")),
            "gemini_model": settings.gemini_model, "states": list(state_configs())}


def seed_demo_data() -> int:
    """Load every state's sample export through its adapter into the store (idempotent)."""
    store = get_store()
    n = 0
    for state_id in state_configs():
        ds = load_state_dataset(state_id)
        for farmer in ds["farmers"]:
            if not store.get("farmers", farmer.farmer_id):
                store.put("farmers", farmer.farmer_id, farmer.model_dump(mode="json"))
                n += 1
        for field in ds["fields"]:
            if not store.get("fields", field.field_id):
                store.put("fields", field.field_id, field.model_dump(mode="json"))
                n += 1
    return n
