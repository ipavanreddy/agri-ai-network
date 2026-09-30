"""Deterministic rule-based advisory used in DEMO MODE (no Gemini key) - same schema as the Gemini output.

`plan_advisory` decides WHAT to say from the canonical context (language-neutral codes + params);
`render_advisory` turns a plan into text in en/hi/te. Localisation never recomputes the analysis.
"""

from typing import Any

from app.advisory.messages import stage_name, t
from app.ai.schemas import (
    AdvisoryAI,
    AdvisoryInterpretation,
    AdvisoryObservation,
    AdvisoryRecommendation,
    RegenerativePractice,
)
from app.crops.catalog import crop_label
from app.intelligence.context import FieldIntelligence

TF_TO_SENSITIVITY = {"tf.today": "today", "tf.48h": "next_48_hours", "tf.week": "this_week", "tf.season": "this_season"}
LOCALIZED_PARAMS = {"crop", "stage", "band", "category", "factor"}


def _item(code: str, **params: Any) -> dict[str, Any]:
    return {"code": code, "params": params}


def render_item(item: dict[str, Any], lang: str) -> str:
    params = dict(item["params"])
    if "crop" in params:
        params["crop"] = crop_label(params["crop"], lang)
    if "stage" in params:
        params["stage"] = stage_name(params["stage"], lang)
    if "band" in params:
        params["band"] = t(f"band.{params['band']}", lang)
    if "category" in params:
        params["category"] = t(f"cat.{params['category']}", lang)
    if "factor" in params:
        params["factor"] = t(f"factor.{params['factor']}", lang)
    if "advice" in params and isinstance(params["advice"], dict):
        params["advice"] = render_item(params["advice"], lang)
    if "interp" in params and isinstance(params["interp"], dict):
        params["interp"] = render_item(params["interp"], lang)
    return t(item["code"], lang, **params)


def signals(intel: FieldIntelligence) -> dict[str, Any]:
    w, soil, sat = intel.weather, intel.soil, intel.satellite
    factors = {f.key: f for f in intel.health.factors}
    water = factors["water"].score
    heat_c = intel.crop.get("heat_stress_c") or 38
    rain14 = w.rain_past_14d_mm or 0
    return {
        "rain14": rain14, "rain3": w.rain_next_3d_mm or 0, "rh": w.humidity_pct or 0, "tmax": w.tmax_next_7d_c,
        "dry": water is not None and water < 60 and rain14 < 30,
        "wet": rain14 >= 120 or (w.soil_moisture_m3_m3 or 0) > 0.40,
        "rain_coming": (w.rain_next_3d_mm or 0) >= 10,
        "humid": (w.humidity_pct or 0) >= 80,
        "heat": w.tmax_next_7d_c is not None and w.tmax_next_7d_c >= heat_c - 2,
        "irrigated": intel.field.irrigation not in ("rainfed",),
        "low_oc": bool(soil and soil.organic_carbon_pct is not None and soil.organic_carbon_pct < 0.5),
        "low_n": bool(soil and soil.nitrogen_kg_ha is not None and soil.nitrogen_kg_ha < 280),
        "ndvi_decline": sat.ndvi_change_30d is not None and sat.ndvi_change_30d <= -0.05,
        "legume": intel.crop.get("family") == "legume",
    }


def plan_advisory(intel: FieldIntelligence) -> dict[str, Any]:
    s = signals(intel)
    w, soil, sat, field = intel.weather, intel.soil, intel.satellite, intel.field
    crop = field.crop.crop_name
    wsrc, ssrc, satsrc = w.provenance.source, soil.provenance.source if soil else "", sat.provenance.source

    obs = [
        {"category": "weather", "item": _item("obs.rain_past", rain14=round(s["rain14"])), "source": wsrc},
        {"category": "weather", "item": _item("obs.rain_forecast", rain3=round(s["rain3"])), "source": wsrc},
    ]
    if s["humid"]:
        obs.append({"category": "weather", "item": _item("obs.humidity", rh=round(s["rh"])), "source": wsrc})
    if s["heat"]:
        obs.append({"category": "weather", "item": _item("obs.tmax", tmax=round(s["tmax"])), "source": wsrc})
    if sat.latest_ndvi is not None:
        exp = intel.stage_at_observation.get("expected_ndvi")
        obs.append({"category": "satellite", "item": _item("obs.ndvi", ndvi=f"{sat.latest_ndvi:.2f}", date=str(sat.observation_date),
                                                          expected=f"{exp:.2f}" if exp else "n/a"), "source": satsrc})
        if s["ndvi_decline"]:
            obs.append({"category": "satellite", "item": _item("obs.ndvi_change", change=f"{sat.ndvi_change_30d:+.2f}"), "source": satsrc})
    if soil:
        if soil.organic_carbon_pct is not None:
            obs.append({"category": "soil", "item": _item("obs.soil_oc", oc=soil.organic_carbon_pct, date=str(soil.measurement_date)), "source": ssrc})
        if soil.ph is not None:
            obs.append({"category": "soil", "item": _item("obs.soil_ph", ph=soil.ph), "source": ssrc})
        if s["low_n"]:
            obs.append({"category": "soil", "item": _item("obs.soil_n", n=round(soil.nitrogen_kg_ha)), "source": ssrc})
    if w.soil_moisture_m3_m3 is not None:
        obs.append({"category": "weather", "item": _item("obs.soil_moisture", sm=f"{w.soil_moisture_m3_m3:.2f}"), "source": wsrc})
    if intel.current_stage.get("days_after_sowing") is not None:
        obs.append({"category": "farm", "item": _item("obs.stage", das=intel.current_stage["days_after_sowing"],
                                                     stage=intel.current_stage["stage"]), "source": "Field record"})
    obs.append({"category": "farm", "item": _item("obs.health", score=intel.health.score, band=intel.health.band),
                "source": "Farm Health rules v1"})

    interps, recs = [], []
    disease = s["humid"] and (s["wet"] or s["rain_coming"] or s["rain14"] >= 30)
    if s["dry"]:
        interps.append({"item": _item("int.moisture_stress"), "based_on": ["weather.rain_past_14d_mm", "satellite.ndvi_change_30d"], "uncertainty": "medium"})
        if s["rain_coming"]:
            interps.append({"item": _item("int.rain_relief"), "based_on": ["weather.rain_next_3d_mm"], "uncertainty": "medium"})
            recs.append({"item": _item("rec.delay_irrigation"), "priority": "high", "tf": "tf.48h", "reason": interps[-1]["item"]})
            if not s["irrigated"]:
                recs.append({"item": _item("rec.conserve_moisture"), "priority": "medium", "tf": "tf.week", "reason": interps[0]["item"]})
        elif s["irrigated"]:
            recs.append({"item": _item("rec.protective_irrigation"), "priority": "high", "tf": "tf.48h", "reason": interps[0]["item"]})
        else:
            recs.append({"item": _item("rec.conserve_moisture"), "priority": "high", "tf": "tf.week", "reason": interps[0]["item"]})
    if s["wet"]:
        interps.append({"item": _item("int.waterlogging"), "based_on": ["weather.rain_past_14d_mm", "weather.topsoil_moisture_m3_m3"], "uncertainty": "medium"})
        recs.append({"item": _item("rec.drain"), "priority": "high", "tf": "tf.48h", "reason": interps[-1]["item"]})
    if disease:
        interps.append({"item": _item("int.disease_risk"), "based_on": ["weather.humidity_pct", "weather.rain_past_14d_mm"], "uncertainty": "medium"})
        recs.append({"item": _item("rec.scout_disease"), "priority": "high" if s["wet"] else "medium", "tf": "tf.week", "reason": interps[-1]["item"]})
    if s["heat"]:
        interps.append({"item": _item("int.heat_risk"), "based_on": ["weather.tmax_next_7d_c"], "uncertainty": "medium"})
        if s["irrigated"]:
            recs.append({"item": _item("rec.heat_irrigation"), "priority": "medium", "tf": "tf.week", "reason": interps[-1]["item"]})
    if s["low_oc"]:
        interps.append({"item": _item("int.low_fertility"), "based_on": ["soil.organic_carbon_pct"], "uncertainty": "low"})
    if s["low_n"] or s["low_oc"]:
        recs.append({"item": _item("rec.follow_shc"), "priority": "low", "tf": "tf.season",
                     "reason": _item("int.low_fertility") if s["low_oc"] else _item("obs.soil_n", n=round(soil.nitrogen_kg_ha))})
    if not interps:
        interps.append({"item": _item("int.on_track"), "based_on": ["satellite.latest_ndvi"], "uncertainty": "low"})
    if not recs:
        recs.append({"item": _item("rec.monitor"), "priority": "low", "tf": "tf.week", "reason": interps[0]["item"]})

    # One field-specific regenerative practice.
    oc = soil.organic_carbon_pct if soil and soil.organic_carbon_pct is not None else "n/a"
    if s["wet"]:
        regen = {"action": _item("regen.ridge_furrow"), "reason": _item("regen.ridge_furrow.why", rain14=round(s["rain14"])),
                 "evidence": ["weather.rain_past_14d_mm"]}
    elif field.farming_practice == "residue_retention" or crop in ("wheat", "paddy"):
        regen = {"action": _item("regen.residue_no_burn"), "reason": _item("regen.residue_no_burn.why", oc=oc),
                 "evidence": ["soil.organic_carbon_pct", "farm.farming_practice"]}
    elif s["dry"]:
        regen = {"action": _item("regen.mulch"), "reason": _item("regen.mulch.why"),
                 "evidence": ["weather.rain_past_14d_mm", "soil.organic_carbon_pct"]}
    elif s["low_oc"]:
        regen = {"action": _item("regen.fym"), "reason": _item("regen.fym.why", oc=oc), "evidence": ["soil.organic_carbon_pct"]}
    elif not s["legume"]:
        regen = {"action": _item("regen.legume_rotation"), "reason": _item("regen.legume_rotation.why", crop=crop),
                 "evidence": ["crop.family", "soil.nitrogen_kg_ha"]}
    else:
        regen = {"action": _item("regen.intercrop"), "reason": _item("regen.intercrop.why"), "evidence": ["farm.irrigation"]}

    if s["dry"] and s["rain_coming"]:
        summary = _item("sum.dry_rain_coming", crop=crop)
    elif s["dry"]:
        summary = _item("sum.dry", crop=crop)
    elif disease or s["wet"]:
        summary = _item("sum.wet_disease", crop=crop)
    elif s["heat"]:
        summary = _item("sum.heat", crop=crop)
    else:
        summary = _item("sum.ok", crop=crop)

    if (s["dry"] and not s["rain_coming"]) or (s["wet"] and s["humid"]) or intel.health.score < 50:
        risk = "high"
    elif s["dry"] or disease or s["heat"] or s["wet"]:
        risk = "medium"
    else:
        risk = "low"

    missing = []
    if "crop_condition" in intel.health.missing_factors:
        missing.append(_item("miss.no_diagnosis"))
    if w.soil_moisture_m3_m3 is None:
        missing.append(_item("miss.no_soil_moisture"))
    soil_old = bool(soil and soil.measurement_date and (intel.as_of_date - soil.measurement_date).days > 365)
    if soil_old:
        missing.append(_item("miss.soil_old"))
    fresh = [_item("fresh.sample", category=src.category) for src in intel.data_sources if src.is_sample]
    if sat.observation_date and (age := (intel.as_of_date - sat.observation_date).days) > 10:
        fresh.append(_item("fresh.sat_age", days=age))
    if soil and soil.measurement_date:
        fresh.append(_item("fresh.soil_date", date=str(soil.measurement_date)))

    any_sample = any(src.is_sample for src in intel.data_sources)
    confidence = round(max(0.4, min(0.85, 0.8 - (0.12 if any_sample else 0) - (0.05 if soil_old else 0))), 2)
    return {
        "summary": summary, "risk_level": risk, "time_sensitivity": TF_TO_SENSITIVITY[recs[0]["tf"]],
        "observations": obs, "interpretations": interps, "recommendations": recs, "regenerative": regen,
        "missing": missing, "freshness": fresh, "confidence": confidence,
        "requires_human_review": risk == "high" or confidence < 0.6 or any_sample,
    }


def render_advisory(plan: dict[str, Any], lang: str = "en") -> AdvisoryAI:
    r = lambda item: render_item(item, lang)
    return AdvisoryAI(
        summary=r(plan["summary"]),
        risk_level=plan["risk_level"],
        time_sensitivity=plan["time_sensitivity"],
        observations=[AdvisoryObservation(category=o["category"], fact=r(o["item"]), source=o["source"]) for o in plan["observations"]],
        interpretations=[AdvisoryInterpretation(statement=r(i["item"]), based_on=i["based_on"], uncertainty=i["uncertainty"])
                         for i in plan["interpretations"]],
        recommendations=[AdvisoryRecommendation(action=r(x["item"]), priority=x["priority"], reason=r(x["reason"]),
                                                timeframe=t(x["tf"], lang)) for x in plan["recommendations"]],
        regenerative_practice=RegenerativePractice(action=r(plan["regenerative"]["action"]), reason=r(plan["regenerative"]["reason"]),
                                                   evidence=plan["regenerative"]["evidence"]),
        missing_information=[r(m) for m in plan["missing"]],
        data_freshness_notes=[r(f) for f in plan["freshness"]],
        confidence=plan["confidence"],
        requires_human_review=plan["requires_human_review"],
    )
