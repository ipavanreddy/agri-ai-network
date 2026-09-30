"""AI agro-advisory (PRD §12-13, §34.1) and farm-context question answering (voice, PRD §18)."""

import logging
import uuid
from typing import Any

from app.advisory.demo import plan_advisory, render_advisory, render_item, signals
from app.advisory.messages import t
from app.ai.runner import run_structured
from app.ai.schemas import AdvisoryAI, AskAI
from app.canonical.models import Review, utcnow
from app.crops.catalog import crop_label
from app.intelligence.context import FieldIntelligence, ai_context, build_intelligence
from app.localization.service import translate_texts
from app.store import get_store

log = logging.getLogger(__name__)

TRANSLATABLE_KEYS = {"summary", "fact", "statement", "action", "reason", "timeframe", "missing_information",
                     "data_freshness_notes", "answer", "follow_up_suggestion"}


def _collect(node: Any, out: list[str], key: str | None = None) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            _collect(v, out, k)
    elif isinstance(node, list):
        for v in node:
            _collect(v, out, key)
    elif isinstance(node, str) and key in TRANSLATABLE_KEYS:
        out.append(node)


def _replace(node: Any, it, key: str | None = None) -> Any:
    if isinstance(node, dict):
        return {k: _replace(v, it, k) for k, v in node.items()}
    if isinstance(node, list):
        return [_replace(v, it, key) for v in node]
    if isinstance(node, str) and key in TRANSLATABLE_KEYS:
        return next(it)
    return node


def translate_content(content: dict[str, Any], lang: str) -> tuple[dict[str, Any], str]:
    texts: list[str] = []
    _collect(content, texts)
    try:
        out = translate_texts(texts, lang)
    except Exception as exc:
        log.warning("translation failed: %s", exc)
        out = None
    if out is None:
        return content, "unavailable"
    translated, method = out
    return _replace(content, iter(translated)), method


def generate_advisory(field_id: str, language: str = "en", force_sample: bool = False) -> dict[str, Any]:
    intel = build_intelligence(field_id, force_sample)
    plan = plan_advisory(intel)
    result, meta = run_structured("advisory", "v1", AdvisoryAI, ai_context(intel), lambda: render_advisory(plan, "en"))
    result.confidence = max(0.0, min(1.0, result.confidence))
    if result.risk_level == "high" or result.confidence < 0.6 or intel.demo_mode:
        result.requires_human_review = True
    record = {
        "advisory_id": f"ADV-{uuid.uuid4().hex[:10]}",
        "field_id": field_id,
        "farmer_id": intel.field.farmer_id,
        "state": intel.field.state,
        "district": intel.field.district,
        "category": "agro_advisory",
        "severity": result.risk_level,
        "recommendation": result.recommendations[0].action if result.recommendations else "",
        "generated_at": utcnow().isoformat(),
        "language": "en",
        "content": result.model_dump(mode="json"),
        "demo_plan": plan if meta.mode == "demo" else None,
        "localized": {},
        "ai": meta.model_dump(mode="json"),
        "model_name": meta.model_name,
        "model_version": meta.model_version,
        "prompt_version": meta.prompt_version,
        "review": Review().model_dump(mode="json"),
        "context_snapshot": {"farm_health": intel.health.score, "band": intel.health.band,
                             "data_sources": [s.model_dump(mode="json") for s in intel.data_sources]},
        "demo_mode": intel.demo_mode or meta.mode == "demo",
    }
    get_store().put("advisories", record["advisory_id"], record)
    if language != "en":
        localize(record, language)
    return record


def localize(record: dict[str, Any], lang: str) -> dict[str, Any]:
    """Present an existing advisory in another language without recomputing the analysis (FR-07)."""
    if lang == "en":
        return {"language": "en", "content": record["content"], "method": "original"}
    if lang in record.get("localized", {}):
        return record["localized"][lang]
    if record.get("demo_plan"):
        content, method = render_advisory(record["demo_plan"], lang).model_dump(mode="json"), "demo_catalog"
    else:
        content, method = translate_content(record["content"], lang)
    entry = {"language": lang, "content": content, "method": method}
    record.setdefault("localized", {})[lang] = entry
    get_store().put("advisories", record["advisory_id"], record)
    return entry


# ---- voice / text Q&A -------------------------------------------------------------------------
INTENTS = {
    "water": ["rain", "water", "irrigat", "बारिश", "पानी", "सिंचाई", "వర్ష", "నీరు", "నీటి", "తడి"],
    "disease": ["disease", "pest", "spot", "insect", "yellow", "रोग", "कीट", "बीमारी", "धब्बे", "తెగులు", "పురుగు", "మచ్చ", "రోగం"],
    "fertilizer": ["fertil", "nutrient", "urea", "manure", "nitrogen", "खाद", "उर्वरक", "यूरिया", "ఎరువు", "యూరియా"],
    "sow": ["sow", "next crop", "which crop", "what crop", "बुवाई", "कौन सी फसल", "अगली फसल", "విత్త", "ఏ పంట", "తదుపరి పంట"],
    "health": ["health", "score", "how is", "स्वास्थ्य", "हालत", "कैसी", "ఆరోగ్య", "ఎలా ఉంది"],
}


def detect_intent(question: str) -> str:
    q = question.lower()
    for intent, words in INTENTS.items():
        if any(w in q for w in words):
            return intent
    return "unknown"


def demo_answer(intel: FieldIntelligence, question: str, lang: str) -> AskAI:
    s = signals(intel)
    intent = detect_intent(question)
    soil = intel.soil
    if intent == "water":
        advice = ("rec.delay_irrigation" if s["dry"] and s["rain_coming"] else "rec.protective_irrigation" if s["dry"] and s["irrigated"]
                  else "rec.conserve_moisture" if s["dry"] else "rec.drain" if s["wet"] else "rec.monitor")
        answer = t("ask.water", lang, rain14=round(s["rain14"]), rain3=round(s["rain3"]), advice=t(advice, lang))
        grounded = ["weather.rain_past_14d_mm", "weather.rain_next_3d_mm"]
    elif intent == "disease":
        interp = "int.disease_risk" if s["humid"] else "int.on_track"
        answer = t("ask.disease", lang, rh=round(s["rh"]), interp=t(interp, lang))
        grounded = ["weather.humidity_pct"]
    elif intent == "fertilizer" and soil:
        answer = t("ask.fertilizer", lang, oc=soil.organic_carbon_pct, ph=soil.ph)
        grounded = ["soil.organic_carbon_pct", "soil.ph"]
    elif intent == "sow":
        from app.crops.recommend import score_crops

        top = [crop_label(c["crop_id"], lang) for c in score_crops(intel)[:3]]
        answer = t("ask.sow", lang, crops=", ".join(top))
        grounded = ["soil.ph", "district_climate_normals", "farm.irrigation"]
    else:
        present = [f for f in intel.health.factors if f.score is not None]
        weakest = min(present, key=lambda f: f.score).key if present else "soil"
        code = "ask.health" if intent == "health" else "ask.unknown"
        answer = render_item({"code": code, "params": {"score": intel.health.score, "band": intel.health.band,
                                                       "factor": weakest}}, lang)
        grounded = ["farm_health.score"]
    return AskAI(answer=answer, grounded_on=grounded, follow_up_suggestion=t("ask.follow_up", lang),
                 requires_expert_review=intent == "disease")


def ask(field_id: str, question: str, language: str, force_sample: bool = False) -> dict[str, Any]:
    intel = build_intelligence(field_id, force_sample)
    result, meta = run_structured("ask", "v1", AskAI, ai_context(intel), lambda: demo_answer(intel, question, language),
                                  extra={"QUESTION": question, "ANSWER_LANGUAGE": language})
    return {"field_id": field_id, "question": question, "language": language, "intent": detect_intent(question),
            **result.model_dump(), "ai": meta.model_dump(mode="json"), "demo_mode": intel.demo_mode or meta.mode == "demo"}
