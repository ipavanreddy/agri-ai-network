"""Integration status (drives the UI "Demo mode" badges) and demo seeding through the state adapters."""

import logging
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from fastapi import APIRouter

from app.config import settings
from app.interop.adapters import load_state_dataset, state_configs
from app.store import get_store, store_status

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["system"])


# ---- live probes ------------------------------------------------------------------------------
# A configured variable is not proof that an integration works (e.g. a project with no Firestore database,
# or an Earth Engine project that is not registered yet). Each configured integration is probed with a cheap
# real call; the result is cached so the status endpoint stays fast. A failing probe is reported as demo
# (fallback in use) with the reason, so the UI badges never claim "live" for something that is not.
PROBE_TTL_S = 600
_probe_lock = threading.Lock()
_probe_cache: dict[str, Any] = {"at": 0.0, "results": {}}


def _probe_gemini() -> str:
    from app.ai.gemini import client

    client().models.get(model=settings.gemini_model)
    return f"model={settings.gemini_model}"


def _probe_earth_engine() -> str:
    import ee

    from app.intelligence.satellite import _init_earth_engine

    _init_earth_engine()
    ee.Number(1).getInfo()
    return f"Sentinel-2 via project {settings.earth_engine_project}"


def _probe_maps() -> str:
    from app.farms import maps

    maps.reverse_geocode(14.68, 77.6)
    return "Geocoding (village search, field address), Places + Routes (nearest KVK with drive time)"


def _probe_translation() -> str:
    from app.localization import service

    service.translate_texts(["water"], "hi")
    return "Live"


def _probe_speech() -> str:
    from app.localization import service

    service.text_to_speech("ok", "en")
    return "Live (Speech-to-Text + Text-to-Speech)"


def _probe_bigquery() -> str:
    from google.cloud import bigquery

    table = bigquery.Client(project=settings.google_cloud_project).get_table(
        f"{settings.google_cloud_project}.{settings.bigquery_dataset}.district_indicators")
    if not table.num_rows:
        raise RuntimeError("district_indicators is empty")
    return f"{settings.bigquery_dataset}.district_indicators ({table.num_rows} rows; labelled sample indicators)"


def _probe_storage() -> str:
    from google.cloud import storage

    bucket = storage.Client(project=settings.google_cloud_project or None).bucket(settings.gcs_bucket)
    list(bucket.list_blobs(prefix="diagnoses/", max_results=1))
    return f"gs://{settings.gcs_bucket}/diagnoses/"


PROBES: dict[str, tuple[Callable[[], bool], Callable[[], str]]] = {
    "gemini": (lambda: settings.gemini_enabled, _probe_gemini),
    "earth_engine": (lambda: settings.earth_engine_enabled, _probe_earth_engine),
    "maps_server": (lambda: bool(settings.maps_api_key), _probe_maps),
    "translation": (lambda: bool(settings.google_cloud_api_key), _probe_translation),
    "speech": (lambda: settings.cloud_speech_enabled, _probe_speech),
    "bigquery": (lambda: settings.bigquery_enabled, _probe_bigquery),
    "storage": (lambda: settings.gcs_enabled, _probe_storage),
}


def _run_probe(fn: Callable[[], str]) -> tuple[bool, str]:
    try:
        return True, fn()
    except Exception as exc:
        msg = str(exc).splitlines()[0][:160] if str(exc) else ""
        log.warning("integration probe failed: %s %s", type(exc).__name__, msg)
        return False, f"{type(exc).__name__}: {msg}" if msg else type(exc).__name__


def probe_integrations(force: bool = False) -> dict[str, tuple[bool, str]]:
    with _probe_lock:
        if not force and _probe_cache["results"] and time.monotonic() - _probe_cache["at"] < PROBE_TTL_S:
            return _probe_cache["results"]
        todo = {k: fn for k, (enabled, fn) in PROBES.items() if enabled()}
        with ThreadPoolExecutor(max_workers=max(1, len(todo))) as pool:
            futures = {k: pool.submit(_run_probe, fn) for k, fn in todo.items()}
            results = {k: f.result() for k, f in futures.items()}
        _probe_cache.update(at=time.monotonic(), results=results)
        return results


def integrations() -> list[dict[str, Any]]:
    store = store_status()
    probes = probe_integrations()

    def row(key: str, label: str, configured: bool, env: str, fallback: str, live_detail: str = "Live") -> dict[str, Any]:
        mode, detail = ("demo", fallback)
        if configured:
            ok, info = probes.get(key, (True, live_detail))
            mode, detail = ("live", info) if ok else ("demo", f"Configured but unavailable ({info}); using fallback: {fallback}")
        return {"key": key, "label": label, "mode": mode, "env": env, "detail": detail}

    return [
        row("gemini", "Gemini (advisory, crop doctor, Q&A)", settings.gemini_enabled,
            "GEMINI_API_KEY or GOOGLE_GENAI_USE_VERTEXAI+GOOGLE_CLOUD_PROJECT",
            "Rule-based demo outputs; Crop Doctor returns fixtures"),
        row("earth_engine", "Earth Engine (Sentinel-2 NDVI)", settings.earth_engine_enabled,
            "EARTH_ENGINE_PROJECT (+ ADC / GOOGLE_APPLICATION_CREDENTIALS)", "Sample NDVI series per state scenario"),
        row("weather", "Weather (Open-Meteo, keyless)", settings.use_public_apis, "USE_PUBLIC_APIS=true (default)",
            "Sample weather", live_detail="Live forecast + 14-day history; sample fallback if unreachable"),
        row("soilgrids", "Soil texture (ISRIC SoilGrids, keyless)", settings.use_public_apis,
            "USE_PUBLIC_APIS=true (default)", "Sample texture",
            live_detail="Live texture (sample fallback if ISRIC is slow); NPK/pH/OC from state Soil Health Card sample records"),
        row("maps_server", "Google Maps Geocoding / Places / Routes", bool(settings.maps_api_key), "MAPS_API_KEY",
            "Pick district from list; no nearest-KVK lookup"),
        row("translation", "Cloud Translation", bool(settings.google_cloud_api_key), "GOOGLE_CLOUD_API_KEY",
            "Gemini translation" if settings.gemini_enabled else "Built-in en/hi/te message catalogue"),
        row("speech", "Cloud Speech-to-Text / Text-to-Speech", settings.cloud_speech_enabled, "GOOGLE_CLOUD_API_KEY",
            "Browser Web Speech API fallback"),
        {"key": "store", "label": "Firestore", "mode": store["mode"], "env": "FIREBASE_PROJECT_ID (+ ADC)",
         "detail": store["note"] or ("Live" if store["mode"] == "live" else "Local SQLite (per instance, resets on restart)")},
        row("bigquery", "BigQuery regional analytics", settings.bigquery_enabled, "GOOGLE_CLOUD_PROJECT + BIGQUERY_DATASET",
            "Synthetic district sample (file)"),
        row("storage", "Cloud Storage (crop photos)", settings.gcs_enabled, "GCS_BUCKET",
            "Local disk (services/api/.data/uploads)"),
        {"key": "maps", "label": "Google Maps JavaScript (browser)", "mode": None,
         "env": "NEXT_PUBLIC_MAPS_API_KEY (apps/*/.env.local, baked at build time)",
         "detail": "Reported by each app; OpenStreetMap + Leaflet fallback"},
    ]


@router.get("/system/status")
def system_status(refresh: bool = False) -> dict[str, Any]:
    if refresh:
        probe_integrations(force=True)
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
