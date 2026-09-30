"""Regenerative crop recommendation (PRD §14-15).

Step 1 (always): transparent rule scoring of every catalogue crop that the state supports for the season.
Step 2 (Gemini, when configured): explain the top candidates in farmer language, citing supplied data.
Demo mode renders the explanation from the rule reasons.
"""

import uuid
from datetime import date
from typing import Any

from app.ai.runner import run_structured
from app.ai.schemas import CropOptionAI, CropRecommendationAI
from app.canonical.models import Review, utcnow
from app.crops.catalog import catalog, crop_label, season_for
from app.intelligence.context import FieldIntelligence, ai_context, build_intelligence
from app.intelligence.health import IRRIGATION_CREDIT
from app.interop.adapters import state_config
from app.store import get_store

WEIGHTS = {"ph": 25, "temperature": 20, "water": 25, "climate_risk": 10, "rotation": 20}


def band(score: float) -> str:
    return "High" if score >= 75 else "Moderate" if score >= 58 else "Low"


def score_crop(crop: dict[str, Any], *, ph: float | None, tmean: float | None, seasonal_rain: float | None,
               irrigation: str, current: dict[str, Any] | None, low_n: bool) -> dict[str, Any]:
    reasons, risks, parts = [], [], {}
    lo, hi = crop["ph"]
    if ph is None:
        parts["ph"] = 15
        risks.append("Soil pH unknown - get a soil test")
    elif lo <= ph <= hi:
        parts["ph"] = 25
        reasons.append(f"Soil pH {ph} is within {lo}-{hi}")
    elif lo - 0.5 <= ph <= hi + 0.5:
        parts["ph"] = 15
        risks.append(f"Soil pH {ph} is slightly outside {lo}-{hi}")
    else:
        parts["ph"] = 5
        risks.append(f"Soil pH {ph} is outside {lo}-{hi}")

    tlo, thi = crop["temp_c"]
    if tmean is None:
        parts["temperature"] = 12
    elif tlo <= tmean <= thi:
        parts["temperature"] = 20
        reasons.append(f"Season mean temperature ~{tmean} °C suits it ({tlo}-{thi} °C)")
    elif tlo - 3 <= tmean <= thi + 3:
        parts["temperature"] = 12
        risks.append(f"Season temperature ~{tmean} °C is at the edge of {tlo}-{thi} °C")
    else:
        parts["temperature"] = 4
        risks.append(f"Season temperature ~{tmean} °C is outside {tlo}-{thi} °C")

    credit = IRRIGATION_CREDIT.get(irrigation, 0.0)
    need = crop["water_mm"]
    if seasonal_rain is None:
        parts["water"] = 12
        risks.append("Seasonal rainfall normal unknown")
    else:
        available = seasonal_rain + credit * need
        ratio = available / need
        tol = crop["drought_tolerance"]
        if ratio >= 1:
            parts["water"] = 25
            reasons.append(f"Water need ~{need} mm is covered (~{seasonal_rain:.0f} mm season rain"
                           + (f" + {irrigation} irrigation)" if credit else ")"))
        elif ratio >= 0.75:
            parts["water"] = 20 if tol != "low" else 15
            reasons.append(f"Needs ~{need} mm; ~{available:.0f} mm available - mostly covered")
        else:
            parts["water"] = {"high": 17, "medium": 10, "low": 4}[tol]
            (reasons if tol == "high" else risks).append(
                f"Needs ~{need} mm but only ~{available:.0f} mm expected"
                + (" - drought tolerant, can cope" if tol == "high" else " - water shortfall risk"))

    rainfed_like = credit < 0.5
    parts["climate_risk"] = {"high": 10, "medium": 6, "low": 2}[crop["drought_tolerance"]] if rainfed_like else 8
    if rainfed_like and crop["drought_tolerance"] == "high":
        reasons.append("High drought tolerance for a rainfed field")

    if current and crop["crop_id"] == current["crop_id"]:
        parts["rotation"] = 6
        risks.append("Same crop as this season - repeating it builds up pests and disease")
    elif crop["n_fixing"] and (not current or not current.get("n_fixing")):
        parts["rotation"] = 20
        reasons.append("Legume: fixes nitrogen and breaks the pest cycle" + (" (soil N is low)" if low_n else ""))
    elif crop["family"] == "millet" and rainfed_like:
        parts["rotation"] = 16
        reasons.append("Millet: low water use and adds crop diversity")
    elif current and crop["family"] != current.get("family"):
        parts["rotation"] = 14
        reasons.append("Different crop family from the current crop (diversification)")
    else:
        parts["rotation"] = 10
    total = sum(parts.values())
    return {"crop_id": crop["crop_id"], "names": crop["names"], "family": crop["family"], "score": total,
            "suitability": band(total), "breakdown": parts, "reasons": reasons, "risks": risks,
            "n_fixing": crop["n_fixing"], "water_mm": need, "drought_tolerance": crop["drought_tolerance"]}


def score_crops(intel: FieldIntelligence, season: str | None = None) -> list[dict[str, Any]]:
    field = intel.field
    season = season or field.crop.season or season_for(date.today())
    climate = intel.district_climate or {}
    cat = catalog()
    try:
        supported = set(state_config(field.state)["supported_crops"])
    except Exception:
        supported = set(cat)
    current = cat.get(field.crop.crop_name)
    soil = intel.soil
    low_n = bool(soil and soil.nitrogen_kg_ha is not None and soil.nitrogen_kg_ha < 280)
    scored = [
        score_crop(c, ph=soil.ph if soil else None, tmean=climate.get(f"{season}_tmean_c"),
                   seasonal_rain=climate.get(f"{season}_rain_mm"), irrigation=field.irrigation, current=current, low_n=low_n)
        for cid, c in cat.items() if season in c["seasons"] and cid in supported
    ]
    return sorted(scored, key=lambda x: (-x["score"], x["crop_id"]))


def demo_explanation(intel: FieldIntelligence, candidates: list[dict[str, Any]]) -> CropRecommendationAI:
    current = intel.field.crop.crop_name
    options = []
    for c in candidates[:5]:
        role = ("Adds nitrogen for the following crop" if c["n_fixing"]
                else "Low water demand; spreads drought risk" if c["family"] == "millet"
                else "Diversifies the rotation" if c["crop_id"] != current else "Current crop - rotate before repeating")
        options.append(CropOptionAI(crop_id=c["crop_id"], suitability=c["suitability"], reasons=c["reasons"] or ["Meets basic requirements"],
                                    risks=c["risks"], regenerative_role=role))
    legume = next((c for c in candidates if c["n_fixing"] and c["crop_id"] != current), None)
    plan = (f"After {crop_label(current)}, consider {crop_label(legume['crop_id'])} (legume) to rebuild soil nitrogen, "
            "and keep crop residue on the field." if legume else
            f"Rotate {crop_label(current)} with a different crop family and retain crop residue.")
    top = ", ".join(crop_label(c["crop_id"]) for c in candidates[:3])
    missing = ["Market prices and seed availability are not considered"]
    if not intel.soil:
        missing.append("No soil test available")
    return CropRecommendationAI(summary=f"Best-fit options for this field: {top}.", options=options, rotation_plan=plan,
                                missing_information=missing, confidence=0.7 if not intel.demo_mode else 0.6)


def recommend(field_id: str, season: str | None = None, force_sample: bool = False) -> dict[str, Any]:
    intel = build_intelligence(field_id, force_sample)
    candidates = score_crops(intel, season)
    top = candidates[:6]
    rules_view = [{k: c[k] for k in ("crop_id", "score", "suitability", "reasons", "risks", "family")} for c in top]
    result, meta = run_structured("crop_recommendation", "v1", CropRecommendationAI, ai_context(intel),
                                  lambda: demo_explanation(intel, top), extra={"CANDIDATES": rules_view})
    by_id = {c["crop_id"]: c for c in candidates}
    options, seen = [], set()
    for o in result.options:
        if o.crop_id in by_id and o.crop_id not in seen:
            seen.add(o.crop_id)
            options.append({**by_id[o.crop_id], "suitability": o.suitability, "reasons": o.reasons, "risks": o.risks,
                            "regenerative_role": o.regenerative_role, "rule_suitability": by_id[o.crop_id]["suitability"]})
    for c in top:  # guarantee >= 3 options (FR-05) even if the model returned fewer valid ones
        if len(options) >= 3:
            break
        if c["crop_id"] not in seen:
            seen.add(c["crop_id"])
            options.append({**c, "regenerative_role": "", "rule_suitability": c["suitability"]})
    record = {
        "recommendation_id": f"REC-{uuid.uuid4().hex[:10]}",
        "field_id": field_id, "farmer_id": intel.field.farmer_id, "state": intel.field.state, "district": intel.field.district,
        "season": season or intel.field.crop.season, "current_crop": intel.field.crop.crop_name,
        "summary": result.summary, "options": options, "rotation_plan": result.rotation_plan,
        "missing_information": result.missing_information, "confidence": max(0.0, min(1.0, result.confidence)),
        "scoring_weights": WEIGHTS, "method": "crop_rules_v1 + " + meta.prompt_version,
        "ai": meta.model_dump(mode="json"), "model_name": meta.model_name, "model_version": meta.model_version,
        "prompt_version": meta.prompt_version, "review": Review().model_dump(mode="json"),
        "generated_at": utcnow().isoformat(), "demo_mode": intel.demo_mode or meta.mode == "demo",
    }
    get_store().put("crop_recommendations", record["recommendation_id"], record)
    return record
