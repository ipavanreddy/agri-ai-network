"""Deterministic generator for all committed demo/sample data under data/sample/.

Run from the repo root:  python3 data/scripts/generate_sample_data.py

Everything written here is SAMPLE / SYNTHETIC data for an offline hackathon demo. Each file carries a
`_meta` block (source, reference_timestamp, dataset_version, geographic_scope, is_sample, is_synthetic).
Values are shaped to be agronomically plausible for the three demo scenarios (PRD §43) but they are
NOT measurements. Live data replaces them when the corresponding integration is enabled.

No wall-clock time or unseeded randomness is used, so re-running produces byte-identical output.
"""

from __future__ import annotations

import json
import math
import random
import struct
import zlib
from datetime import date, timedelta
from pathlib import Path

SEED = 20260930
DATASET_VERSION = "sample-2026.09.30-v1"
GENERATOR = "data/scripts/generate_sample_data.py"
ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "sample"


def meta(source: str, reference_timestamp: str, scope: str, *, synthetic: bool = True, note: str = "") -> dict:
    return {
        "source": source,
        "reference_timestamp": reference_timestamp,
        "dataset_version": DATASET_VERSION,
        "geographic_scope": scope,
        "is_sample": True,
        "is_synthetic": synthetic,
        "generated_by": GENERATOR,
        "seed": SEED,
        "note": note,
    }


def write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def rect_polygon(lat: float, lon: float, acres: float, aspect: float = 1.2) -> dict:
    """Axis-aligned rectangle (GeoJSON, lon/lat) with approximately the given area."""
    area_m2 = acres * 4046.8564224
    h = math.sqrt(area_m2 / aspect)
    w = area_m2 / h
    dlat = h / 111_320
    dlon = w / (111_320 * math.cos(math.radians(lat)))
    lat0, lon0 = lat - dlat / 2, lon - dlon / 2
    ring = [
        [round(lon0, 6), round(lat0, 6)],
        [round(lon0 + dlon, 6), round(lat0, 6)],
        [round(lon0 + dlon, 6), round(lat0 + dlat, 6)],
        [round(lon0, 6), round(lat0 + dlat, 6)],
        [round(lon0, 6), round(lat0, 6)],
    ]
    return {"type": "Polygon", "coordinates": [ring]}


# --------------------------------------------------------------------------------------------
# Demo scenarios (PRD §43). Each state exports records in its OWN local format; the state
# adapters in data/adapters/*.json map them into the canonical schema.
# --------------------------------------------------------------------------------------------
SCENARIOS = {
    "AP": {"lat": 14.5602, "lon": 77.4417, "acres": 2.4, "scenario_date": date(2026, 9, 28)},
    "MH": {"lat": 20.3350, "lon": 77.9900, "acres": 3.0, "scenario_date": date(2026, 9, 28)},
    "PB": {"lat": 30.8420, "lon": 75.7610, "acres": 4.0, "scenario_date": date(2026, 2, 18)},
}


def ap_records() -> dict:
    s = SCENARIOS["AP"]
    return {
        "_meta": meta("AP e-Crop booking + Soil Health Card export (sample format)", "2026-09-28T06:00:00+05:30",
                      "Andhra Pradesh", note="Synthetic records in an AP-style local format (dd/mm/yyyy dates, crop codes, acres)."),
        "ryots": [
            {"ryot_id": "AP-ATP-000123", "ryot_name": "Lakshmi Devi", "lang": "te", "district_name": "Anantapuramu",
             "mandal": "Rapthadu", "village": "Gandlaparthi", "mobile_masked": "98xxxxxx21"},
            {"ryot_id": "AP-KNL-000877", "ryot_name": "Venkata Reddy", "lang": "te", "district_name": "Kurnool",
             "mandal": "Dhone", "village": "Kothakota", "mobile_masked": "94xxxxxx07"},
        ],
        "crop_bookings": [
            {"booking_id": "ECB-2026-K-55112", "ryot_id": "AP-ATP-000123", "survey_no": "112/2", "extent_ac": s["acres"],
             "crop_code": "GN", "variety": "Kadiri-6 (K-6)", "season": "Kharif-2026", "sowing_dt": "12/07/2026",
             "water_source": "RF", "practice": "CONV", "centroid": [s["lat"], s["lon"]],
             "boundary": rect_polygon(s["lat"], s["lon"], s["acres"])},
            {"booking_id": "ECB-2026-K-60301", "ryot_id": "AP-KNL-000877", "survey_no": "45/1A", "extent_ac": 3.1,
             "crop_code": "RG", "variety": "LRG-52", "season": "Kharif-2026", "sowing_dt": "02/07/2026",
             "water_source": "BW", "practice": "NF", "centroid": [15.4312, 77.8740],
             "boundary": rect_polygon(15.4312, 77.8740, 3.1)},
        ],
        "soil_health_cards": [
            {"shc_no": "AP/ATP/RPT/2025/00412", "district_name": "Anantapuramu", "mandal": "Rapthadu",
             "pH": 6.4, "EC": 0.21, "OC": 0.38, "N": 176, "P": 14.2, "K": 212, "sample_dt": "18/03/2025"},
            {"shc_no": "AP/KNL/DHN/2025/00128", "district_name": "Kurnool", "mandal": "Dhone",
             "pH": 7.6, "EC": 0.35, "OC": 0.47, "N": 205, "P": 18.6, "K": 298, "sample_dt": "02/02/2025"},
        ],
    }


def mh_records() -> dict:
    s = SCENARIOS["MH"]
    return {
        "_meta": meta("Maharashtra MahaDBT farmer registry + Soil Health Card export (sample format)",
                      "2026-09-28T06:00:00+05:30", "Maharashtra",
                      note="Synthetic records in an MH-style local format (ISO dates, hectares, Marathi crop names)."),
        "shetkari": [
            {"shetkari_id": "MH-YTL-2231", "naav": "Suresh Patil", "bhasha": "mr", "jilha": "Yavatmal",
             "taluka": "Ner", "gaon": "Malkhed"},
            {"shetkari_id": "MH-AKL-0419", "naav": "Anita Wankhede", "bhasha": "hi", "jilha": "Akola",
             "taluka": "Barshitakli", "gaon": "Pinjar"},
        ],
        "pik_nondani": [
            {"nondani_id": "PN-2026-0091", "shetkari_id": "MH-YTL-2231", "gat_no": "217", "area_ha": 1.2141,
             "pik": "kapus", "vaan": "Bt hybrid (sample)", "hangam": "kharif", "perni_date": "2026-06-25",
             "sinchan": "rainfed", "paddhat": "conventional", "lat": s["lat"], "lon": s["lon"],
             "geometry": rect_polygon(s["lat"], s["lon"], s["acres"])},
            {"nondani_id": "PN-2026-0144", "shetkari_id": "MH-AKL-0419", "gat_no": "88", "area_ha": 2.0234,
             "pik": "soyabean", "vaan": "JS-335", "hangam": "kharif", "perni_date": "2026-06-30",
             "sinchan": "protective", "paddhat": "conventional", "lat": 20.6512, "lon": 77.0102,
             "geometry": rect_polygon(20.6512, 77.0102, 5.0)},
        ],
        "mati_arogya": [
            {"card_id": "MH-SHC-YTL-7781", "jilha": "Yavatmal", "taluka": "Ner", "ph_value": 7.9,
             "organic_carbon_pct": 0.52, "available_n_kg_ha": 214, "available_p_kg_ha": 11.8,
             "available_k_kg_ha": 356, "sampled_on": "2025-01-22"},
            {"card_id": "MH-SHC-AKL-1203", "jilha": "Akola", "taluka": "Barshitakli", "ph_value": 8.1,
             "organic_carbon_pct": 0.61, "available_n_kg_ha": 232, "available_p_kg_ha": 16.4,
             "available_k_kg_ha": 410, "sampled_on": "2024-12-11"},
        ],
    }


def pb_records() -> dict:
    s = SCENARIOS["PB"]
    return {
        "_meta": meta("Punjab Anaaj/land records + PAU soil test export (sample format)", "2026-02-18T06:00:00+05:30",
                      "Punjab", note="Synthetic records in a PB-style local format (dd-Mon-yyyy dates, kanal area, "
                                     "OC in g/kg, nutrients in kg/acre). Scenario date is last rabi season."),
        "kisan": [
            {"kisan_code": "PB-LDH-5510", "full_name": "Gurpreet Singh", "language_pref": "pa", "zila": "Ludhiana",
             "block": "Mullanpur Dakha", "pind": "Mullanpur"},
            {"kisan_code": "PB-SGR-2077", "full_name": "Harjit Kaur", "language_pref": "hi", "zila": "Sangrur",
             "block": "Dhuri", "pind": "Kanjhla"},
        ],
        "khet": [
            {"khasra": "34//12", "kisan_code": "PB-LDH-5510", "area_kanal": 32, "fasal": "kanak",
             "variety": "PBW 826", "season": "rabi 2025-26", "bijai": "10-Nov-2025", "irrigation": "tubewell",
             "practice": "happy_seeder_no_burn", "centroid": {"lat": s["lat"], "lng": s["lon"]},
             "polygon": rect_polygon(s["lat"], s["lon"], s["acres"])},
            {"khasra": "71//4", "kisan_code": "PB-SGR-2077", "area_kanal": 20, "fasal": "sarson",
             "variety": "PBR 357", "season": "rabi 2025-26", "bijai": "22-Oct-2025", "irrigation": "canal",
             "practice": "conventional", "centroid": {"lat": 30.3781, "lng": 75.8720},
             "polygon": rect_polygon(30.3781, 75.8720, 2.5)},
        ],
        "soil_tests": [
            {"lab_ref": "PAU-LDH-25-1180", "zila": "Ludhiana", "block": "Mullanpur Dakha", "ph": 7.8,
             "oc_g_per_kg": 4.1, "n_kg_per_acre": 101, "p_kg_per_acre": 9.2, "k_kg_per_acre": 58,
             "tested_on": "05-Oct-2025"},
            {"lab_ref": "PAU-SGR-25-0660", "zila": "Sangrur", "block": "Dhuri", "ph": 8.2,
             "oc_g_per_kg": 3.6, "n_kg_per_acre": 96, "p_kg_per_acre": 11.4, "k_kg_per_acre": 61,
             "tested_on": "28-Sep-2025"},
        ],
    }


# --------------------------------------------------------------------------------------------
# Weather fixtures in the Open-Meteo response shape so the SAME parser handles live + sample.
# --------------------------------------------------------------------------------------------
WEATHER_PLAN = {
    # past14 rain pattern, forecast7 rain pattern, tmax base, tmin base, humidity, wind
    "AP": {"past_rain": [0, 0, 0, 1.2, 0, 0, 0, 0, 2.4, 0, 0, 0, 0, 0],
           "fc_rain": [0.4, 14.8, 8.6, 1.2, 0, 0, 0], "fc_prob": [30, 80, 70, 35, 10, 10, 10],
           "tmax": 33.5, "tmin": 22.5, "rh": 72, "wind": 13.0, "soil_moisture": 0.14},
    "MH": {"past_rain": [12.0, 28.5, 4.2, 0, 18.4, 31.0, 9.6, 0, 2.2, 14.8, 22.1, 6.0, 0, 3.4],
           "fc_rain": [6.0, 11.5, 3.2, 0, 0, 2.0, 0], "fc_prob": [65, 75, 45, 20, 15, 25, 15],
           "tmax": 30.5, "tmin": 22.8, "rh": 89, "wind": 9.0, "soil_moisture": 0.41},
    "PB": {"past_rain": [0, 0, 0, 0, 3.1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
           "fc_rain": [0, 0, 0, 0, 0, 1.0, 0], "fc_prob": [5, 5, 5, 10, 10, 20, 10],
           "tmax": 23.0, "tmin": 8.5, "rh": 64, "wind": 11.0, "soil_moisture": 0.24},
}


def weather_fixture(state: str, rng: random.Random) -> dict:
    s = SCENARIOS[state]
    plan = WEATHER_PLAN[state]
    ref = s["scenario_date"]
    days = [ref - timedelta(days=14 - i) for i in range(14)] + [ref + timedelta(days=i) for i in range(7)]
    rain = plan["past_rain"] + plan["fc_rain"]
    probs = [100 if r > 0 else 0 for r in plan["past_rain"]] + plan["fc_prob"]
    warming = 3.0 if state == "PB" else 0.0  # PB: late-Feb warming trend in the forecast
    tmax = [round(plan["tmax"] + rng.uniform(-1.5, 1.5) - (1.5 if r > 5 else 0)
                  + (warming * max(0, i - 13) / 7), 1) for i, r in enumerate(rain)]
    tmin = [round(plan["tmin"] + rng.uniform(-1.0, 1.0), 1) for _ in rain]
    wind = [round(plan["wind"] + rng.uniform(0, 8), 1) for _ in rain]
    hourly_times = [f"{ref.isoformat()}T{h:02d}:00" for h in range(0, 24, 6)]
    return {
        "_meta": meta("Open-Meteo-shaped synthetic weather extract", f"{ref.isoformat()}T09:00:00+05:30",
                      f"{state} demo field point", note="Shape mirrors api.open-meteo.com/v1/forecast so the live parser is reused."),
        "latitude": s["lat"], "longitude": s["lon"], "timezone": "Asia/Kolkata",
        "current": {"time": f"{ref.isoformat()}T09:00", "temperature_2m": round(tmax[14] - 4.0, 1),
                    "relative_humidity_2m": plan["rh"], "wind_speed_10m": plan["wind"], "precipitation": 0.0},
        "daily": {
            "time": [d.isoformat() for d in days],
            "temperature_2m_max": tmax,
            "temperature_2m_min": tmin,
            "precipitation_sum": rain,
            "precipitation_probability_max": probs,
            "wind_speed_10m_max": wind,
        },
        "hourly": {"time": hourly_times, "soil_moisture_3_to_9cm": [plan["soil_moisture"]] * len(hourly_times)},
    }


# --------------------------------------------------------------------------------------------
# Satellite fixtures in the shape produced by app/intelligence/satellite.py (Earth Engine path).
# --------------------------------------------------------------------------------------------
NDVI_PLAN = {
    # (days after scenario start, ndvi, ndmi) - AP: dry-spell dip; MH: lush/wet; PB: healthy rising
    "AP": {"sowing": date(2026, 7, 12), "points": [(12, 0.21, -0.12), (22, 0.29, -0.06), (32, 0.38, 0.01),
                                                  (42, 0.49, 0.06), (52, 0.58, 0.10), (57, 0.62, 0.11),
                                                  (67, 0.61, 0.05), (72, 0.58, 0.01), (77, 0.56, -0.02)]},
    "MH": {"sowing": date(2026, 6, 25), "points": [(15, 0.22, -0.05), (30, 0.34, 0.06), (45, 0.47, 0.14),
                                                  (60, 0.58, 0.21), (70, 0.64, 0.25), (80, 0.68, 0.28),
                                                  (86, 0.69, 0.30), (91, 0.70, 0.31), (94, 0.70, 0.32)]},
    "PB": {"sowing": date(2025, 11, 10), "points": [(15, 0.24, -0.04), (30, 0.36, 0.05), (45, 0.49, 0.12),
                                                   (60, 0.58, 0.17), (72, 0.64, 0.21), (82, 0.68, 0.24),
                                                   (90, 0.71, 0.26), (95, 0.72, 0.26), (99, 0.73, 0.27)]},
}


def satellite_fixture(state: str, rng: random.Random) -> dict:
    plan = NDVI_PLAN[state]
    series = []
    for days, ndvi, ndmi in plan["points"]:
        d = plan["sowing"] + timedelta(days=days)
        series.append({"date": d.isoformat(), "ndvi": round(ndvi + rng.uniform(-0.005, 0.005), 3),
                       "ndmi": round(ndmi + rng.uniform(-0.005, 0.005), 3),
                       "valid_fraction": round(rng.uniform(0.82, 1.0), 2)})
    return {
        "_meta": meta("Sentinel-2 SR NDVI/NDMI field-mean series (synthetic, Earth Engine output shape)",
                      f"{series[-1]['date']}T05:30:00Z", f"{state} demo field polygon",
                      note="Shaped like app/intelligence/satellite.py output from COPERNICUS/S2_SR_HARMONIZED."),
        "collection": "COPERNICUS/S2_SR_HARMONIZED",
        "series": series,
    }


def soilgrids_fixture(state: str) -> dict:
    texture = {"AP": (18, 66, 16), "MH": (48, 22, 30), "PB": (16, 52, 32)}[state]  # clay, sand, silt %
    return {
        "_meta": meta("SoilGrids 2.0-shaped synthetic texture extract (0-15 cm)", "2020-01-01T00:00:00Z",
                      f"{state} demo field point", note="Modelled texture baseline; replaced by live SoilGrids when reachable."),
        "clay_pct": texture[0], "sand_pct": texture[1], "silt_pct": texture[2],
    }


# --------------------------------------------------------------------------------------------
# Regional (officer dashboard) aggregates.
# --------------------------------------------------------------------------------------------
DISTRICTS = {
    "AP": [("AP-ATP", "Anantapur", 14.68, 77.60, {"groundnut": 58, "red_gram": 14, "bajra": 9, "cotton": 8, "other": 11}, "high"),
           ("AP-KNL", "Kurnool", 15.83, 78.04, {"cotton": 31, "groundnut": 22, "red_gram": 18, "jowar": 12, "other": 17}, "medium"),
           ("AP-CTR", "Chittoor", 13.22, 79.10, {"groundnut": 34, "paddy": 28, "maize": 12, "other": 26}, "medium"),
           ("AP-GNT", "Guntur", 16.31, 80.44, {"cotton": 38, "paddy": 30, "maize": 10, "other": 22}, "low"),
           ("AP-PKM", "Prakasam", 15.35, 79.56, {"red_gram": 24, "cotton": 22, "bajra": 16, "other": 38}, "medium")],
    "MH": [("MH-YTL", "Yavatmal", 20.39, 78.12, {"cotton": 54, "soybean": 28, "red_gram": 10, "other": 8}, "high"),
           ("MH-AKL", "Akola", 20.70, 77.00, {"soybean": 42, "cotton": 36, "green_gram": 8, "other": 14}, "high"),
           ("MH-AMR", "Amravati", 20.93, 77.75, {"soybean": 38, "cotton": 34, "red_gram": 14, "other": 14}, "medium"),
           ("MH-JLN", "Jalna", 19.84, 75.88, {"cotton": 46, "soybean": 22, "bajra": 12, "other": 20}, "medium"),
           ("MH-NGP", "Nagpur", 21.15, 79.09, {"soybean": 30, "cotton": 26, "paddy": 22, "other": 22}, "low")],
    "PB": [("PB-LDH", "Ludhiana", 30.90, 75.85, {"wheat": 82, "mustard": 4, "other": 14}, "low"),
           ("PB-SGR", "Sangrur", 30.25, 75.84, {"wheat": 85, "mustard": 3, "other": 12}, "medium"),
           ("PB-BTH", "Bathinda", 30.21, 74.95, {"wheat": 70, "chickpea": 6, "mustard": 8, "other": 16}, "medium"),
           ("PB-PTL", "Patiala", 30.34, 76.39, {"wheat": 84, "other": 16}, "low"),
           ("PB-MGA", "Moga", 30.82, 75.17, {"wheat": 86, "other": 14}, "low")],
}
TOP_ISSUES = {
    "AP": ["Early/late leaf spot (tikka) - groundnut", "Dry spell moisture stress", "Red hairy caterpillar"],
    "MH": ["Pink bollworm - cotton", "Boll rot after heavy rain", "Yellow mosaic - soybean"],
    "PB": ["Yellow (stripe) rust - wheat", "Terminal heat risk", "Aphid build-up"],
}
WEATHER_REASON = {
    "high": {"AP": "Dry spell >14 days with rain only in forecast", "MH": "Heavy rain + humidity >85% (disease-favourable)",
             "PB": "Forecast warming during grain fill"},
    "medium": {"AP": "Patchy rainfall, high daytime temperature", "MH": "Intermittent heavy showers",
               "PB": "Cool humid nights favour rust"},
    "low": {"AP": "Near-normal conditions", "MH": "Near-normal conditions", "PB": "Near-normal conditions"},
}
BLOCKS = {
    "AP-ATP": ["Rapthadu", "Kalyandurg", "Dharmavaram"], "AP-KNL": ["Dhone", "Adoni", "Pattikonda"],
    "AP-CTR": ["Madanapalle", "Palamaner", "Punganur"], "AP-GNT": ["Tenali", "Narasaraopet", "Sattenapalle"],
    "AP-PKM": ["Kanigiri", "Markapur", "Darsi"], "MH-YTL": ["Ner", "Darwha", "Pusad"],
    "MH-AKL": ["Barshitakli", "Akot", "Telhara"], "MH-AMR": ["Achalpur", "Morshi", "Daryapur"],
    "MH-JLN": ["Ambad", "Bhokardan", "Partur"], "MH-NGP": ["Katol", "Umred", "Ramtek"],
    "PB-LDH": ["Mullanpur Dakha", "Jagraon", "Samrala"], "PB-SGR": ["Dhuri", "Sunam", "Malerkotla"],
    "PB-BTH": ["Rampura Phul", "Talwandi Sabo", "Maur"], "PB-PTL": ["Rajpura", "Nabha", "Samana"],
    "PB-MGA": ["Dharamkot", "Baghapurana", "Nihal Singh Wala"],
}
RISK_HEALTH = {"high": (52, 61), "medium": (60, 70), "low": (69, 79)}
RISK_WATER = {"high": (0.55, 0.75), "medium": (0.35, 0.55), "low": (0.15, 0.35)}


def regional(rng: random.Random) -> dict:
    states = {}
    for state, rows in DISTRICTS.items():
        ref = SCENARIOS[state]["scenario_date"].isoformat()
        districts = []
        for did, name, lat, lon, crops, risk in rows:
            lo, hi = RISK_HEALTH[risk]
            wlo, whi = RISK_WATER[risk]
            farmers = rng.randint(1800, 5200)
            blocks = []
            for b in BLOCKS[did]:
                blocks.append({"block": b, "avg_farm_health": rng.randint(lo - 3, hi + 3),
                               "water_stress_index": round(rng.uniform(wlo, whi), 2),
                               "disease_alerts": rng.randint(0, 9 if risk == "high" else 4)})
            districts.append({
                "district_id": did, "district": name, "lat": lat, "lon": lon,
                "farmers_represented": farmers, "fields_represented": int(farmers * rng.uniform(1.2, 1.6)),
                "crop_distribution_pct": crops,
                "avg_farm_health": rng.randint(lo, hi),
                "water_stress_index": round(rng.uniform(wlo, whi), 2),
                "weather_risk": risk, "weather_risk_reason": WEATHER_REASON[risk][state],
                "disease_alerts": sum(b["disease_alerts"] for b in blocks),
                "top_issues": TOP_ISSUES[state][: 3 if risk == "high" else 2],
                "advisories_issued_7d": rng.randint(120, 900),
                "reference_date": ref,
                "blocks": blocks,
            })
        states[state] = districts
    return {
        "_meta": meta("Synthetic district/block aggregates for the officer dashboard", "2026-09-28T00:00:00+05:30",
                      "AP, MH, PB (15 districts)", note="Realistic-looking but synthetic. PB reference date is rabi 2025-26."),
        "states": states,
    }


# --------------------------------------------------------------------------------------------
# Crop catalogue: indicative agronomic ranges (curated for the demo, not validated advice).
# --------------------------------------------------------------------------------------------
def stages(*rows):
    return [{"stage": s, "from_day": a, "to_day": b, "expected_ndvi": n} for s, a, b, n in rows]


CROPS = [
    {"crop_id": "groundnut", "names": {"en": "Groundnut", "hi": "मूंगफली", "te": "వేరుశనగ"}, "family": "legume",
     "seasons": ["kharif", "rabi"], "ph": [6.0, 7.5], "temp_c": [24, 33], "water_mm": 500, "duration_days": 115,
     "drought_tolerance": "medium", "n_fixing": True, "heat_stress_c": 38,
     "stages": stages(("emergence", 0, 20, 0.25), ("vegetative", 20, 45, 0.45), ("flowering_pegging", 45, 70, 0.62),
                      ("pod_development", 70, 95, 0.66), ("maturity", 95, 125, 0.5))},
    {"crop_id": "cotton", "names": {"en": "Cotton", "hi": "कपास", "te": "పత్తి"}, "family": "fibre",
     "seasons": ["kharif"], "ph": [6.0, 8.2], "temp_c": [21, 35], "water_mm": 800, "duration_days": 170,
     "drought_tolerance": "medium", "n_fixing": False, "heat_stress_c": 40,
     "stages": stages(("emergence", 0, 20, 0.25), ("vegetative", 20, 60, 0.5), ("squaring_flowering", 60, 100, 0.68),
                      ("boll_development", 100, 145, 0.72), ("maturity", 145, 185, 0.5))},
    {"crop_id": "wheat", "names": {"en": "Wheat", "hi": "गेहूं", "te": "గోధుమ"}, "family": "cereal",
     "seasons": ["rabi"], "ph": [6.0, 8.0], "temp_c": [12, 25], "water_mm": 450, "duration_days": 145,
     "drought_tolerance": "low", "n_fixing": False, "heat_stress_c": 32,
     "stages": stages(("emergence", 0, 20, 0.3), ("tillering", 20, 50, 0.55), ("jointing_booting", 50, 85, 0.72),
                      ("heading_grain_fill", 85, 120, 0.7), ("maturity", 120, 150, 0.4))},
    {"crop_id": "red_gram", "names": {"en": "Red gram (pigeon pea)", "hi": "अरहर", "te": "కంది"}, "family": "legume",
     "seasons": ["kharif"], "ph": [6.0, 8.0], "temp_c": [20, 35], "water_mm": 450, "duration_days": 160,
     "drought_tolerance": "high", "n_fixing": True, "heat_stress_c": 40,
     "stages": stages(("emergence", 0, 25, 0.22), ("vegetative", 25, 70, 0.45), ("flowering", 70, 110, 0.6),
                      ("pod_development", 110, 145, 0.58), ("maturity", 145, 175, 0.4))},
    {"crop_id": "bajra", "names": {"en": "Pearl millet (bajra)", "hi": "बाजरा", "te": "సజ్జ"}, "family": "millet",
     "seasons": ["kharif"], "ph": [6.0, 8.3], "temp_c": [25, 35], "water_mm": 320, "duration_days": 85,
     "drought_tolerance": "high", "n_fixing": False, "heat_stress_c": 42,
     "stages": stages(("emergence", 0, 15, 0.25), ("vegetative", 15, 40, 0.5), ("flowering", 40, 60, 0.62),
                      ("grain_fill", 60, 80, 0.55), ("maturity", 80, 95, 0.4))},
    {"crop_id": "jowar", "names": {"en": "Sorghum (jowar)", "hi": "ज्वार", "te": "జొన్న"}, "family": "millet",
     "seasons": ["kharif", "rabi"], "ph": [6.0, 8.3], "temp_c": [22, 34], "water_mm": 420, "duration_days": 110,
     "drought_tolerance": "high", "n_fixing": False, "heat_stress_c": 40,
     "stages": stages(("emergence", 0, 15, 0.25), ("vegetative", 15, 50, 0.52), ("flowering", 50, 75, 0.64),
                      ("grain_fill", 75, 100, 0.56), ("maturity", 100, 120, 0.4))},
    {"crop_id": "foxtail_millet", "names": {"en": "Foxtail millet", "hi": "कंगनी", "te": "కొర్ర"}, "family": "millet",
     "seasons": ["kharif"], "ph": [5.5, 8.0], "temp_c": [24, 34], "water_mm": 280, "duration_days": 80,
     "drought_tolerance": "high", "n_fixing": False, "heat_stress_c": 40,
     "stages": stages(("emergence", 0, 15, 0.22), ("vegetative", 15, 40, 0.45), ("flowering", 40, 60, 0.55),
                      ("maturity", 60, 90, 0.4))},
    {"crop_id": "chickpea", "names": {"en": "Chickpea (Bengal gram)", "hi": "चना", "te": "శనగ"}, "family": "legume",
     "seasons": ["rabi"], "ph": [6.0, 8.3], "temp_c": [14, 28], "water_mm": 300, "duration_days": 110,
     "drought_tolerance": "high", "n_fixing": True, "heat_stress_c": 33,
     "stages": stages(("emergence", 0, 20, 0.25), ("vegetative", 20, 50, 0.5), ("flowering_podding", 50, 90, 0.62),
                      ("maturity", 90, 120, 0.4))},
    {"crop_id": "mustard", "names": {"en": "Mustard", "hi": "सरसों", "te": "ఆవాలు"}, "family": "oilseed",
     "seasons": ["rabi"], "ph": [6.0, 8.3], "temp_c": [12, 25], "water_mm": 280, "duration_days": 125,
     "drought_tolerance": "medium", "n_fixing": False, "heat_stress_c": 30,
     "stages": stages(("emergence", 0, 20, 0.28), ("vegetative", 20, 50, 0.55), ("flowering", 50, 85, 0.68),
                      ("pod_fill", 85, 110, 0.55), ("maturity", 110, 130, 0.4))},
    {"crop_id": "maize", "names": {"en": "Maize", "hi": "मक्का", "te": "మొక్కజొన్న"}, "family": "cereal",
     "seasons": ["kharif", "rabi"], "ph": [5.5, 7.8], "temp_c": [21, 32], "water_mm": 550, "duration_days": 110,
     "drought_tolerance": "low", "n_fixing": False, "heat_stress_c": 38,
     "stages": stages(("emergence", 0, 15, 0.28), ("vegetative", 15, 50, 0.6), ("tasseling_silking", 50, 70, 0.78),
                      ("grain_fill", 70, 100, 0.7), ("maturity", 100, 120, 0.45))},
    {"crop_id": "paddy", "names": {"en": "Paddy (rice)", "hi": "धान", "te": "వరి"}, "family": "cereal",
     "seasons": ["kharif", "rabi"], "ph": [5.5, 7.5], "temp_c": [22, 34], "water_mm": 1200, "duration_days": 125,
     "drought_tolerance": "low", "n_fixing": False, "heat_stress_c": 38,
     "stages": stages(("establishment", 0, 25, 0.3), ("tillering", 25, 55, 0.6), ("panicle_initiation", 55, 85, 0.78),
                      ("grain_fill", 85, 110, 0.7), ("maturity", 110, 130, 0.45))},
    {"crop_id": "soybean", "names": {"en": "Soybean", "hi": "सोयाबीन", "te": "సోయాచిక్కుడు"}, "family": "legume",
     "seasons": ["kharif"], "ph": [6.0, 7.8], "temp_c": [20, 32], "water_mm": 500, "duration_days": 100,
     "drought_tolerance": "low", "n_fixing": True, "heat_stress_c": 36,
     "stages": stages(("emergence", 0, 15, 0.28), ("vegetative", 15, 40, 0.6), ("flowering", 40, 60, 0.76),
                      ("pod_fill", 60, 85, 0.72), ("maturity", 85, 105, 0.45))},
    {"crop_id": "green_gram", "names": {"en": "Green gram (moong)", "hi": "मूंग", "te": "పెసర"}, "family": "legume",
     "seasons": ["kharif", "zaid"], "ph": [6.2, 7.8], "temp_c": [25, 35], "water_mm": 280, "duration_days": 65,
     "drought_tolerance": "medium", "n_fixing": True, "heat_stress_c": 40,
     "stages": stages(("emergence", 0, 12, 0.25), ("vegetative", 12, 30, 0.5), ("flowering_podding", 30, 55, 0.6),
                      ("maturity", 55, 70, 0.4))},
]


def crop_catalog() -> dict:
    return {
        "_meta": meta("Curated indicative crop requirement ranges (demo knowledge base)", "2026-09-30T00:00:00+05:30",
                      "India (generic)", synthetic=False,
                      note="Indicative ranges compiled for the demo from general agronomy knowledge; not validated "
                           "extension advice. Expected NDVI by stage is a heuristic for the Farm Health score."),
        "crops": CROPS,
    }


# --------------------------------------------------------------------------------------------
# Demo-mode Crop Doctor fixtures (returned only when Gemini is not configured).
# --------------------------------------------------------------------------------------------
def diagnosis_fixtures() -> dict:
    return {
        "_meta": meta("Hand-written demo Crop Doctor outputs (NOT an analysis of the uploaded image)",
                      "2026-09-30T00:00:00+05:30", "demo", note="Used only when GEMINI_API_KEY is empty."),
        "by_crop": {
            "groundnut": {"plant_part": "leaf", "severity": "moderate", "confidence": 0.62,
                          "potential_conditions": [{"name": "Early leaf spot (Cercospora arachidicola) - potential", "likelihood": 0.62,
                                                    "visible_evidence": ["Circular brown lesions on upper leaf surface", "Yellow halo around some lesions"]},
                                                   {"name": "Late leaf spot (Nothopassalora personata) - possible", "likelihood": 0.24,
                                                    "visible_evidence": ["Dark lesions without clear halo"]}],
                          "visible_symptoms": ["Brown circular lesions", "Yellowing around lesions", "Localized leaf damage"],
                          "recommended_next_actions": ["Inspect 10-15 plants across the field to see how widespread the spots are",
                                                       "Remove heavily spotted lower leaves where practical",
                                                       "Confirm with the local agriculture officer / KVK before any spray decision"]},
            "cotton": {"plant_part": "leaf", "severity": "low", "confidence": 0.55,
                       "potential_conditions": [{"name": "Alternaria leaf spot - potential", "likelihood": 0.55,
                                                 "visible_evidence": ["Small brown concentric spots on older leaves"]},
                                                {"name": "Bacterial blight - possible", "likelihood": 0.2,
                                                 "visible_evidence": ["Angular water-soaked patches"]}],
                       "visible_symptoms": ["Brown spots on older leaves", "Some yellowing"],
                       "recommended_next_actions": ["Check lower canopy and bolls for spread after the recent heavy rain",
                                                    "Improve drainage where water is standing",
                                                    "Ask the agriculture officer to verify before treatment"]},
            "wheat": {"plant_part": "leaf", "severity": "moderate", "confidence": 0.6,
                      "potential_conditions": [{"name": "Yellow (stripe) rust - potential", "likelihood": 0.6,
                                                "visible_evidence": ["Yellow pustules arranged in stripes along veins"]},
                                               {"name": "Nutrient deficiency (N) - possible", "likelihood": 0.18,
                                                "visible_evidence": ["General pale yellowing"]}],
                      "visible_symptoms": ["Yellow striped pustules", "Leaf yellowing"],
                      "recommended_next_actions": ["Walk the field in a W pattern and check for rust patches",
                                                   "Report patches to the agriculture officer quickly - rust spreads fast in cool humid weather",
                                                   "Follow PAU-recommended management only after confirmation"]},
            "_default": {"plant_part": "leaf", "severity": "unknown", "confidence": 0.4,
                         "potential_conditions": [{"name": "Leaf spot / stress - uncertain", "likelihood": 0.4,
                                                   "visible_evidence": ["Discoloured patches on leaf"]}],
                         "visible_symptoms": ["Discoloured patches"],
                         "recommended_next_actions": ["Take a clearer close-up photo in daylight",
                                                      "Consult the local agriculture officer"]},
        },
    }


# --------------------------------------------------------------------------------------------
# Synthetic leaf image (pure-stdlib PNG) for the Crop Doctor demo.
# --------------------------------------------------------------------------------------------
def png_bytes(width: int, height: int, pixel) -> bytes:
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            raw.extend(pixel(x, y))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")


def leaf_image(rng: random.Random) -> bytes:
    w = h = 256
    spots = [(rng.randint(80, 176), rng.randint(70, 186), rng.randint(6, 12)) for _ in range(9)]

    def pixel(x, y):
        cx, cy = 128, 128
        dx, dy = (x - cx) / 70, (y - cy) / 112
        inside = dx * dx + dy * dy <= 1.0
        if not inside:
            return (226, 214, 190)  # soil-coloured background
        if abs(x - cx) <= 1:
            return (160, 190, 90)  # midrib
        for sx, sy, r in spots:
            d = math.hypot(x - sx, y - sy)
            if d <= r:
                return (110, 70, 35)  # brown lesion
            if d <= r + 4:
                return (205, 190, 60)  # yellow halo
        shade = int(20 * (1 - dy * dy))
        return (60, 120 + shade, 45)

    return png_bytes(w, h, pixel)


def main() -> None:
    rng = random.Random(SEED)
    write(SAMPLE / "states" / "AP" / "source_records.json", ap_records())
    write(SAMPLE / "states" / "MH" / "source_records.json", mh_records())
    write(SAMPLE / "states" / "PB" / "source_records.json", pb_records())
    for state in ("AP", "MH", "PB"):
        write(SAMPLE / "weather" / f"{state}.json", weather_fixture(state, rng))
        write(SAMPLE / "satellite" / f"{state}.json", satellite_fixture(state, rng))
        write(SAMPLE / "soilgrids" / f"{state}.json", soilgrids_fixture(state))
    write(SAMPLE / "regional" / "district_indicators.json", regional(rng))
    write(SAMPLE / "crops" / "crop_catalog.json", crop_catalog())
    write(SAMPLE / "diagnosis" / "fixtures.json", diagnosis_fixtures())
    img = SAMPLE / "images" / "leaf_spot_synthetic.png"
    img.parent.mkdir(parents=True, exist_ok=True)
    img.write_bytes(leaf_image(rng))
    write(SAMPLE / "images" / "leaf_spot_synthetic.meta.json",
          {"_meta": meta("Procedurally drawn synthetic leaf with brown spots (no real photo)", "2026-09-30T00:00:00+05:30",
                         "n/a", note="For exercising the upload flow; not a real crop photograph.")})
    manifest = []
    for p in sorted(SAMPLE.rglob("*.json")):
        m = json.loads(p.read_text()).get("_meta")
        if m:
            manifest.append({"path": str(p.relative_to(ROOT)), **{k: m[k] for k in ("source", "reference_timestamp",
                             "dataset_version", "geographic_scope", "is_sample", "is_synthetic")}})
    write(SAMPLE / "manifest.json", {"dataset_version": DATASET_VERSION, "generated_by": GENERATOR, "datasets": manifest})
    print(f"wrote {len(manifest)} datasets to {SAMPLE}")


if __name__ == "__main__":
    main()
