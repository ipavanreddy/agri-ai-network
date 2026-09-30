"""Interoperability endpoints: state configurations, adapter demo, canonical schema (PRD §20-22, FR-10)."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.canonical.export import canonical_schemas
from app.crops.catalog import catalog, catalog_meta
from app.interop.adapters import AdapterError, adapter_demo, state_config, state_configs

router = APIRouter(prefix="/api", tags=["interoperability"])


def _summary(cfg: dict[str, Any]) -> dict[str, Any]:
    return {k: cfg.get(k) for k in ("state_id", "state_name", "adapter_version", "source_system", "primary_crop",
                                    "default_language", "language_note", "supported_crops")} | {
        "districts": [{k: d[k] for k in ("id", "name", "lat", "lon")} for d in cfg["districts"]]}


@router.get("/states")
def list_states() -> list[dict[str, Any]]:
    return [_summary(c) for c in state_configs().values()]


@router.get("/states/{state_id}")
def read_state(state_id: str) -> dict[str, Any]:
    try:
        return _summary(state_config(state_id))
    except AdapterError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/states/{state_id}/adapter-demo")
def state_adapter_demo(state_id: str) -> dict[str, Any]:
    try:
        return adapter_demo(state_id)
    except AdapterError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/crops")
def list_crops() -> dict[str, Any]:
    return {"_meta": catalog_meta(), "crops": list(catalog().values())}


@router.get("/schema/canonical")
def canonical_schema() -> dict[str, Any]:
    return canonical_schemas()
