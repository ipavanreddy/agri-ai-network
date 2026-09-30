"""Farm Health score (PRD §11): transparent, weighted, rule-based.

    Farm Health = Vegetation x 30% + Soil x 25% + Weather x 20% + Water x 15% + Crop condition x 10%

Each factor scores 0-100 from observed inputs only. A factor whose inputs are missing is reported as
"missing" and its weight is redistributed over the remaining factors (never imputed).
Bands: >= 75 Good, 50-74 Moderate, < 50 Poor.
"""

from datetime import UTC, date, datetime
from typing import Any

from app.canonical.models import (
    FarmHealth,
    HealthFactor,
    SatelliteObservation,
    SoilObservation,
    WeatherObservation,
)

WEIGHTS: dict[str, float] = {"vegetation": 0.30, "soil": 0.25, "weather": 0.20, "water": 0.15, "crop_condition": 0.10}
LABELS = {"vegetation": "Vegetation", "soil": "Soil", "weather": "Weather", "water": "Water", "crop_condition": "Crop condition"}

# Soil Health Card rating thresholds (available nutrients, kg/ha) commonly used in India.
N_LOW, N_HIGH = 280, 560
P_LOW, P_HIGH = 10, 25
K_LOW, K_HIGH = 110, 280
IRRIGATION_CREDIT = {"rainfed": 0.0, "supplemental": 0.4, "tank": 0.5, "canal": 0.8, "borewell": 0.8, "drip": 0.9}


def clamp(v: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, v))


def status_of(score: float | None) -> str:
    if score is None:
        return "missing"
    return "good" if score >= 75 else "moderate" if score >= 50 else "poor"


def band_of(score: float) -> str:
    return "Good" if score >= 75 else "Moderate" if score >= 50 else "Poor"


def vegetation_factor(sat: SatelliteObservation | None, stage: dict[str, Any],
                      as_of: date | None = None) -> tuple[float | None, list[str], dict]:
    if not sat or sat.latest_ndvi is None:
        return None, ["No satellite observation available"], {}
    expected = stage.get("expected_ndvi")
    inputs = {"latest_ndvi": sat.latest_ndvi, "expected_ndvi": expected, "ndvi_change_30d": sat.ndvi_change_30d,
              "observation_date": str(sat.observation_date), "stage_at_observation": stage.get("stage")}
    drivers = []
    if expected:
        score = clamp(sat.latest_ndvi / expected * 100)
        drivers.append(f"NDVI {sat.latest_ndvi:.2f} vs ~{expected:.2f} expected at {stage['stage'].replace('_', ' ')}")
    else:
        score = clamp((sat.latest_ndvi - 0.1) / 0.6 * 100)
        drivers.append(f"NDVI {sat.latest_ndvi:.2f} (no stage-specific expectation available)")
    change = sat.ndvi_change_30d
    growing = stage.get("stage") not in (None, "maturity", "harvested_or_season_complete", "unknown")
    if change is not None and growing and change <= -0.05:
        penalty = 20 if change <= -0.1 else 10
        score = clamp(score - penalty)
        drivers.append(f"NDVI declined {abs(change):.2f} over ~30 days (possible stress)")
    elif change is not None and change >= 0.05:
        drivers.append(f"NDVI rising (+{change:.2f} over ~30 days)")
    if sat.observation_date and ((as_of or date.today()) - sat.observation_date).days > 20:
        drivers.append(f"Latest clear image is from {sat.observation_date} - treat as indicative")
    return round(score, 1), drivers, inputs


def soil_factor(soil: SoilObservation | None, profile: dict[str, Any] | None) -> tuple[float | None, list[str], dict]:
    if not soil:
        return None, ["No soil record available"], {}
    parts: list[tuple[float, float]] = []  # (points, max)
    drivers: list[str] = []
    if soil.ph is not None:
        lo, hi = profile["ph"] if profile else (6.0, 7.8)
        if lo <= soil.ph <= hi:
            parts.append((40, 40))
        elif lo - 0.5 <= soil.ph <= hi + 0.5:
            parts.append((25, 40))
            drivers.append(f"pH {soil.ph} slightly outside {lo}-{hi} preferred range")
        else:
            parts.append((10, 40))
            drivers.append(f"pH {soil.ph} outside {lo}-{hi} preferred range")
    if soil.organic_carbon_pct is not None:
        oc = soil.organic_carbon_pct
        parts.append((30 if oc >= 0.75 else 20 if oc >= 0.5 else 10, 30))
        if oc < 0.5:
            drivers.append(f"Low organic carbon ({oc}%)")
        elif oc < 0.75:
            drivers.append(f"Medium organic carbon ({oc}%)")
    for label, val, low, high in (("nitrogen", soil.nitrogen_kg_ha, N_LOW, N_HIGH),
                                  ("phosphorus", soil.phosphorus_kg_ha, P_LOW, P_HIGH),
                                  ("potassium", soil.potassium_kg_ha, K_LOW, K_HIGH)):
        if val is None:
            continue
        parts.append((4 if val < low else 8 if val <= high else 10, 10))
        if val < low:
            drivers.append(f"Low available {label} ({val:.0f} kg/ha)")
    if not parts:
        return None, ["Soil record has no usable values"], {}
    score = sum(p for p, _ in parts) / sum(m for _, m in parts) * 100
    inputs = soil.model_dump(mode="json", include={"ph", "organic_carbon_pct", "nitrogen_kg_ha", "phosphorus_kg_ha",
                                                    "potassium_kg_ha", "measurement_date"})
    if not drivers:
        drivers.append("Soil parameters within preferred ranges")
    return round(score, 1), drivers, inputs


def weather_factor(w: WeatherObservation | None, profile: dict[str, Any] | None) -> tuple[float | None, list[str], dict]:
    if not w or not w.daily:
        return None, ["No weather data available"], {}
    score = 100.0
    drivers = []
    forecast = [d for d in w.daily if d.is_forecast]
    heat = profile["heat_stress_c"] if profile else 38
    tmax = w.tmax_next_7d_c
    if tmax is not None and tmax >= heat:
        score -= 25
        drivers.append(f"Forecast max {tmax:.0f} °C at/above crop heat-stress threshold ({heat} °C)")
    elif tmax is not None and tmax >= heat - 2:
        score -= 10
        drivers.append(f"Forecast max {tmax:.0f} °C close to heat-stress threshold ({heat} °C)")
    if any((d.rain_mm or 0) >= 64.5 for d in forecast[:3]):
        score -= 25
        drivers.append("Heavy rain (>= 64.5 mm/day) forecast in the next 3 days")
    elif (w.rain_next_3d_mm or 0) >= 64.5:
        score -= 15
        drivers.append(f"{w.rain_next_3d_mm:.0f} mm rain forecast over 3 days")
    if (w.humidity_pct or 0) >= 85:
        wet = (w.rain_past_14d_mm or 0) >= 60
        score -= 30 if wet else 15
        drivers.append(f"High humidity {w.humidity_pct:.0f}%" + (" after heavy rain" if wet else "") + " (disease-favourable)")
    if any((d.wind_max_kmh or 0) >= 40 for d in forecast[:3]):
        score -= 10
        drivers.append("Strong wind forecast")
    if any(d.tmin_c is not None and d.tmin_c <= 2 for d in forecast[:3]):
        score -= 20
        drivers.append("Frost risk (min <= 2 °C)")
    if not drivers:
        drivers.append("No significant weather risk in the 7-day forecast")
    inputs = {"tmax_next_7d_c": tmax, "rain_next_3d_mm": w.rain_next_3d_mm, "humidity_pct": w.humidity_pct}
    return round(clamp(score), 1), drivers, inputs


def water_factor(w: WeatherObservation | None, irrigation: str, profile: dict[str, Any] | None) -> tuple[float | None, list[str], dict]:
    if not w or w.rain_past_14d_mm is None:
        return None, ["No rainfall history available"], {}
    need_14d = (profile["water_mm"] / profile["duration_days"] * 14) if profile else 50.0
    credit = IRRIGATION_CREDIT.get(irrigation, 0.0)
    supply = w.rain_past_14d_mm + credit * need_14d
    ratio = supply / need_14d if need_14d else 1
    drivers = [f"{w.rain_past_14d_mm:.0f} mm rain in 14 days vs ~{need_14d:.0f} mm crop need"
               + (f"; {irrigation} irrigation credited" if credit else "; rainfed")]
    score = clamp(ratio * 100)
    if w.rain_past_14d_mm > 2 * need_14d and credit < 0.5:
        score = 65.0
        drivers.append("Excess rain - waterlogging risk")
    if w.soil_moisture_m3_m3 is not None:
        if w.soil_moisture_m3_m3 < 0.15:
            score = clamp(score - 10)
            drivers.append(f"Low topsoil moisture ({w.soil_moisture_m3_m3:.2f} m³/m³)")
        elif w.soil_moisture_m3_m3 > 0.40:
            score = clamp(score - 10)
            drivers.append(f"Saturated topsoil ({w.soil_moisture_m3_m3:.2f} m³/m³)")
    if score < 60 and (w.rain_next_3d_mm or 0) >= 10:
        score = clamp(score + 10)
        drivers.append(f"{w.rain_next_3d_mm:.0f} mm rain expected in 3 days should ease stress")
    inputs = {"rain_past_14d_mm": w.rain_past_14d_mm, "crop_need_14d_mm": round(need_14d, 1), "irrigation": irrigation,
              "soil_moisture_m3_m3": w.soil_moisture_m3_m3, "rain_next_3d_mm": w.rain_next_3d_mm}
    return round(score, 1), drivers, inputs


def crop_condition_factor(diagnosis: dict[str, Any] | None) -> tuple[float | None, list[str], dict]:
    """From the latest Crop Doctor result (within 30 days). Missing if no recent photo was checked."""
    if not diagnosis:
        return None, ["No recent Crop Doctor check - upload a leaf photo to include crop condition"], {}
    created = datetime.fromisoformat(str(diagnosis["created_at"]))
    if (datetime.now(UTC) - created).days > 30:
        return None, ["Latest Crop Doctor check is older than 30 days"], {}
    severity = diagnosis["result"]["severity"]
    score = {"none": 90, "low": 80, "moderate": 55, "high": 30}.get(severity)
    if score is None:
        return None, ["Crop Doctor result was inconclusive"], {"severity": severity}
    name = (diagnosis["result"].get("potential_conditions") or [{"name": "no condition"}])[0]["name"]
    return float(score), [f"Crop Doctor: {severity} severity ({name}; AI-assisted, unverified)"], {
        "severity": severity, "diagnosis_id": diagnosis["diagnosis_id"]}


def compute_farm_health(*, satellite: SatelliteObservation | None, soil: SoilObservation | None,
                        weather: WeatherObservation | None, irrigation: str, profile: dict[str, Any] | None,
                        stage_at_observation: dict[str, Any], latest_diagnosis: dict[str, Any] | None,
                        weights: dict[str, float] | None = None, as_of: date | None = None) -> FarmHealth:
    weights = weights or WEIGHTS
    results = {
        "vegetation": vegetation_factor(satellite, stage_at_observation, as_of),
        "soil": soil_factor(soil, profile),
        "weather": weather_factor(weather, profile),
        "water": water_factor(weather, irrigation, profile),
        "crop_condition": crop_condition_factor(latest_diagnosis),
    }
    available = {k: weights[k] for k, (s, _, _) in results.items() if s is not None}
    total_w = sum(available.values())
    effective = {k: round(w / total_w, 4) for k, w in available.items()} if total_w else {}
    score = sum(results[k][0] * w for k, w in effective.items()) if effective else 0.0
    factors = [
        HealthFactor(key=k, label=LABELS[k], weight=weights[k], score=s, status=status_of(s), drivers=d, inputs=i)
        for k, (s, d, i) in results.items()
    ]
    return FarmHealth(
        score=round(score), band=band_of(score), factors=factors, weights=weights, effective_weights=effective,
        missing_factors=[k for k, (s, _, _) in results.items() if s is None],
    )
