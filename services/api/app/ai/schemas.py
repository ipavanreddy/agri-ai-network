"""Structured Gemini output schemas (PRD §33). Exported as JSON Schema to ai/schemas/ by app.canonical.export.

Kept free of defaults/numeric constraints so they translate cleanly into Gemini response schemas;
range checks happen in post-validation (see app/ai/runner.py and the service modules).
"""

from typing import Literal

from pydantic import BaseModel

Risk = Literal["low", "medium", "high"]


# ---- Agro-advisory (prompt: ai/prompts/advisory_v1.md) ---------------------------------------
class AdvisoryObservation(BaseModel):
    category: Literal["weather", "soil", "satellite", "farm", "crop_health"]
    fact: str  # restates a SUPPLIED value, never a new measurement
    source: str


class AdvisoryInterpretation(BaseModel):
    statement: str
    based_on: list[str]
    uncertainty: Risk


class AdvisoryRecommendation(BaseModel):
    action: str
    priority: Risk
    reason: str
    timeframe: str


class RegenerativePractice(BaseModel):
    action: str
    reason: str
    evidence: list[str]


class AdvisoryAI(BaseModel):
    summary: str
    risk_level: Risk
    time_sensitivity: Literal["today", "next_48_hours", "this_week", "this_season"]
    observations: list[AdvisoryObservation]
    interpretations: list[AdvisoryInterpretation]
    recommendations: list[AdvisoryRecommendation]
    regenerative_practice: RegenerativePractice
    missing_information: list[str]
    data_freshness_notes: list[str]
    confidence: float
    requires_human_review: bool


# ---- Crop recommendation (prompt: ai/prompts/crop_recommendation_v1.md) -------------------------
class CropOptionAI(BaseModel):
    crop_id: str
    suitability: Literal["High", "Moderate", "Low"]
    reasons: list[str]
    risks: list[str]
    regenerative_role: str


class CropRecommendationAI(BaseModel):
    summary: str
    options: list[CropOptionAI]
    rotation_plan: str
    missing_information: list[str]
    confidence: float


# ---- Crop Doctor (prompt: ai/prompts/diagnosis_v1.md) --------------------------------------------
class PotentialCondition(BaseModel):
    name: str
    likelihood: float
    visible_evidence: list[str]


class DiagnosisAI(BaseModel):
    image_usable: bool
    image_issue: str
    plant_part: Literal["leaf", "stem", "fruit", "whole_plant", "canopy", "unknown"]
    potential_conditions: list[PotentialCondition]
    visible_symptoms: list[str]
    severity: Literal["none", "low", "moderate", "high", "unknown"]
    confidence: float
    recommended_next_actions: list[str]
    requires_expert_review: bool
    explanation: str


# ---- Voice / text question answering (prompt: ai/prompts/ask_v1.md) -------------------------------
class AskAI(BaseModel):
    answer: str
    grounded_on: list[str]
    follow_up_suggestion: str
    requires_expert_review: bool


# ---- Translation of an existing advisory (prompt: ai/prompts/translate_v1.md) -------------------
class TranslationAI(BaseModel):
    translations: list[str]


AI_SCHEMAS: dict[str, type[BaseModel]] = {
    "advisory_v1": AdvisoryAI,
    "crop_recommendation_v1": CropRecommendationAI,
    "diagnosis_v1": DiagnosisAI,
    "ask_v1": AskAI,
    "translate_v1": TranslationAI,
}
