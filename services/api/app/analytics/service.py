"""Agriculture Officer analytics (PRD §19): India -> State -> District -> Block.

Regional indicators come from BigQuery (`{project}.{dataset}.district_indicators`) when GOOGLE_CLOUD_PROJECT
is set, otherwise from the labelled synthetic sample. Platform activity (registered fields, advisories,
diagnoses, pending reviews) is always live from the store.
"""

import json
import logging
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

from app.canonical.models import Provenance, utcnow
from app.config import settings
from app.interop.adapters import state_config, state_configs
from app.sample_data import load_sample, sample_provenance
from app.store import get_store

log = logging.getLogger(__name__)
REVIEWABLE = {"advisories": "advisory_id", "diagnoses": "diagnosis_id", "crop_recommendations": "recommendation_id"}


@lru_cache(maxsize=8)
def _bigquery_rows(state_id: str) -> list[dict[str, Any]]:
    from google.cloud import bigquery

    client = bigquery.Client(project=settings.google_cloud_project)
    table = f"`{settings.google_cloud_project}.{settings.bigquery_dataset}.district_indicators`"
    job = client.query(f"SELECT * FROM {table} WHERE state_id = @state",
                       job_config=bigquery.QueryJobConfig(query_parameters=[
                           bigquery.ScalarQueryParameter("state", "STRING", state_id)]))
    rows = []
    for r in job.result():
        row = dict(r)
        for key in ("crop_distribution_pct", "blocks", "top_issues"):
            if isinstance(row.get(key), str):
                row[key] = json.loads(row[key])
        rows.append(row)
    return rows


def district_rows(state_id: str) -> tuple[list[dict[str, Any]], Provenance]:
    state_id = state_id.upper()
    if settings.bigquery_enabled:
        try:
            rows = _bigquery_rows(state_id)
            if rows:
                sample = any(r.get("is_sample") for r in rows)
                return rows, Provenance(
                    source=f"BigQuery {settings.bigquery_dataset}.district_indicators"
                           + (f" ({rows[0].get('source')})" if rows[0].get("source") else ""),
                    reference_timestamp=datetime.now(UTC), mode="live", dataset_version=rows[0].get("dataset_version"),
                    is_sample=sample, is_synthetic=sample,
                    note="Served live from BigQuery; rows were loaded from the labelled synthetic sample by "
                         "data/transformations/load_bigquery.py" if sample else "Served live from BigQuery")
        except Exception as exc:
            log.warning("BigQuery unavailable: %s", exc)
    sample = load_sample("regional/district_indicators.json")
    return sample["states"].get(state_id, []), sample_provenance(sample["_meta"])


def _platform_activity(state_id: str | None = None, district: str | None = None) -> dict[str, Any]:
    store = get_store()
    where: dict[str, Any] = {}
    if state_id:
        where["state"] = state_id
    if district:
        where["district"] = district
    fields = store.list("fields", **where)
    advisories = store.list("advisories", **where)
    diagnoses = store.list("diagnoses", **where)
    recs = store.list("crop_recommendations", **where)
    pending = sum(1 for d in advisories + diagnoses + recs if d.get("review", {}).get("status") == "pending_officer_review")
    return {"registered_fields": len(fields), "registered_farmers": len({f["farmer_id"] for f in fields}),
            "advisories_generated": len(advisories), "diagnoses": len(diagnoses), "crop_recommendations": len(recs),
            "pending_reviews": pending,
            "recent_diagnoses": [{k: d.get(k) for k in ("diagnosis_id", "district", "crop", "potential_condition", "severity",
                                                        "confidence", "created_at")}
                                 for d in sorted(diagnoses, key=lambda d: d["created_at"], reverse=True)[:5]]}


def state_analytics(state_id: str) -> dict[str, Any]:
    cfg = state_config(state_id)
    rows, prov = district_rows(cfg["state_id"])
    farmers = sum(r["farmers_represented"] for r in rows) or 1
    crop_area: dict[str, float] = {}
    for r in rows:
        for crop, pct in r["crop_distribution_pct"].items():
            crop_area[crop] = crop_area.get(crop, 0) + pct * r["fields_represented"] / 100
    total_area = sum(crop_area.values()) or 1
    return {
        "state_id": cfg["state_id"], "state_name": cfg["state_name"], "primary_crop": cfg["primary_crop"],
        "provenance": prov.model_dump(mode="json"),
        "totals": {
            "farmers_represented": sum(r["farmers_represented"] for r in rows),
            "fields_represented": sum(r["fields_represented"] for r in rows),
            "avg_farm_health": round(sum(r["avg_farm_health"] * r["farmers_represented"] for r in rows) / farmers),
            "avg_water_stress_index": round(sum(r["water_stress_index"] * r["farmers_represented"] for r in rows) / farmers, 2),
            "disease_alerts": sum(r["disease_alerts"] for r in rows),
            "advisories_issued_7d": sum(r["advisories_issued_7d"] for r in rows),
            "high_weather_risk_districts": sum(1 for r in rows if r["weather_risk"] == "high"),
            "active_crops": len([c for c in crop_area if c != "other"]),
        },
        "crop_distribution_pct": {c: round(v / total_area * 100, 1) for c, v in sorted(crop_area.items(), key=lambda x: (x[0] == "other", -x[1]))},
        "districts": [{k: v for k, v in r.items() if k != "blocks"} for r in rows],
        "hotspots": sorted(({"district_id": r["district_id"], "district": r["district"], "disease_alerts": r["disease_alerts"],
                             "top_issues": r["top_issues"], "weather_risk": r["weather_risk"]} for r in rows),
                           key=lambda x: -x["disease_alerts"])[:3],
        "platform_activity": _platform_activity(cfg["state_id"]),
        "generated_at": utcnow().isoformat(),
    }


def overview() -> dict[str, Any]:
    states = []
    demo = False
    for sid, cfg in state_configs().items():
        a = state_analytics(sid)
        demo = demo or a["provenance"]["is_sample"]
        states.append({"state_id": sid, "state_name": cfg["state_name"], "primary_crop": cfg["primary_crop"], **a["totals"],
                       "lat": sum(d["lat"] for d in a["districts"]) / max(1, len(a["districts"])),
                       "lon": sum(d["lon"] for d in a["districts"]) / max(1, len(a["districts"]))})
    return {"level": "India", "states": states, "demo_mode": demo, "platform_activity": _platform_activity()}


def district_risks(district_id: str) -> dict[str, Any] | None:
    state_id = district_id.split("-")[0].upper()
    if state_id not in state_configs():
        return None
    rows, prov = district_rows(state_id)
    row = next((r for r in rows if r["district_id"].upper() == district_id.upper()), None)
    if not row:
        return None
    risks = []
    if row["weather_risk"] in ("high", "medium"):
        risks.append({"type": "weather", "level": row["weather_risk"], "detail": row["weather_risk_reason"]})
    if row["water_stress_index"] >= 0.5:
        risks.append({"type": "water_stress", "level": "high" if row["water_stress_index"] >= 0.65 else "medium",
                      "detail": f"Water stress index {row['water_stress_index']}"})
    for issue in row["top_issues"]:
        risks.append({"type": "disease_or_pest", "level": "medium", "detail": issue})
    return {**row, "state_id": state_id, "risks": risks, "provenance": prov.model_dump(mode="json"),
            "platform_activity": _platform_activity(state_id, row["district"])}


def review_queue() -> list[dict[str, Any]]:
    store = get_store()
    items = []
    for collection, key in REVIEWABLE.items():
        for d in store.list(collection):
            items.append({
                "kind": collection, "id": d[key], "field_id": d.get("field_id"), "state": d.get("state"),
                "district": d.get("district"),
                "title": d.get("content", {}).get("summary") or d.get("potential_condition") or d.get("summary"),
                "severity": d.get("severity") or d.get("content", {}).get("risk_level"),
                "requires_review_reason": _review_reason(collection, d),
                "model_name": d.get("model_name"), "prompt_version": d.get("prompt_version"),
                "demo_mode": d.get("demo_mode"), "created_at": d.get("generated_at") or d.get("created_at"),
                "review": d.get("review"), "detail": d,
            })
    return sorted(items, key=lambda x: x["created_at"] or "", reverse=True)


def _review_reason(collection: str, d: dict[str, Any]) -> str:
    if collection == "diagnoses":
        return "AI-assisted diagnosis" + (" - expert review flagged" if d["result"].get("requires_expert_review") else "")
    if collection == "advisories" and d.get("content", {}).get("requires_human_review"):
        return "AI advisory flagged for human review (risk/confidence/sample data)"
    return "All AI recommendations need officer approval"


def review(collection: str, doc_id: str, decision: str, reviewer: str, note: str | None) -> dict[str, Any] | None:
    store = get_store()
    doc = store.get(collection, doc_id)
    if not doc:
        return None
    doc["review"] = {"status": "approved" if decision == "approve" else "rejected", "reviewer": reviewer, "note": note,
                     "reviewed_at": utcnow().isoformat()}
    store.put(collection, doc_id, doc)
    return doc
