from datetime import UTC, date, datetime

import pytest

from app.canonical.models import (
    DailyWeather,
    GeoPoint,
    NdviPoint,
    Provenance,
    SatelliteObservation,
    SoilObservation,
    WeatherObservation,
)
from app.crops.catalog import crop_profile
from app.intelligence import health

PROV = Provenance(source="test", mode="demo", is_sample=True)
GROUNDNUT = crop_profile("groundnut")
STAGE = {"stage": "pod_development", "expected_ndvi": 0.66}


def sat(latest: float, change: float | None = None) -> SatelliteObservation:
    return SatelliteObservation(series=[NdviPoint(date=date.today(), ndvi=latest)], latest_ndvi=latest, ndvi_change_30d=change,
                                observation_date=date.today(), provenance=PROV)


def weather(rain14: float = 40, rain3: float = 0, rh: float = 60, tmax: float = 32, daily_rain: float = 0,
            sm: float | None = None) -> WeatherObservation:
    fc = [DailyWeather(date=date.today(), tmax_c=tmax, tmin_c=20, rain_mm=daily_rain, wind_max_kmh=10, is_forecast=True)]
    return WeatherObservation(location=GeoPoint(lat=0, lon=0), humidity_pct=rh, daily=fc, rain_past_14d_mm=rain14,
                              rain_next_3d_mm=rain3, tmax_next_7d_c=tmax, soil_moisture_m3_m3=sm, provenance=PROV)


def soil(**kw) -> SoilObservation:
    base = dict(ph=6.8, organic_carbon_pct=0.8, nitrogen_kg_ha=600, phosphorus_kg_ha=30, potassium_kg_ha=300)
    return SoilObservation(**{**base, **kw}, provenance=PROV)


def test_weights_match_prd():
    assert health.WEIGHTS == {"vegetation": 0.30, "soil": 0.25, "weather": 0.20, "water": 0.15, "crop_condition": 0.10}
    assert sum(health.WEIGHTS.values()) == pytest.approx(1.0)


@pytest.mark.parametrize("score,band", [(90, "Good"), (75, "Good"), (74.9, "Moderate"), (50, "Moderate"), (49, "Poor")])
def test_bands(score, band):
    assert health.band_of(score) == band


def test_vegetation_relative_to_stage_and_trend():
    assert health.vegetation_factor(sat(0.70), STAGE)[0] == 100
    healthy = health.vegetation_factor(sat(0.56), STAGE)[0]
    declining = health.vegetation_factor(sat(0.56, change=-0.06), STAGE)[0]
    assert healthy == pytest.approx(0.56 / 0.66 * 100, abs=0.1)
    assert declining == pytest.approx(healthy - 10, abs=0.1)
    assert health.vegetation_factor(None, STAGE)[0] is None


def test_soil_scoring():
    assert health.soil_factor(soil(), GROUNDNUT)[0] == 100
    poor, drivers, _ = health.soil_factor(soil(organic_carbon_pct=0.38, nitrogen_kg_ha=176, ph=8.9), GROUNDNUT)
    assert poor < 60
    assert any("organic carbon" in d for d in drivers) and any("nitrogen" in d for d in drivers)
    partial = health.soil_factor(SoilObservation(ph=6.5, provenance=PROV), GROUNDNUT)[0]
    assert partial == 100  # only pH known, and it is in range -> rescaled, not imputed


def test_weather_penalties():
    assert health.weather_factor(weather(), GROUNDNUT)[0] == 100
    assert health.weather_factor(weather(daily_rain=80, rain3=80), GROUNDNUT)[0] == 75
    assert health.weather_factor(weather(rh=90, rain14=100), GROUNDNUT)[0] == 70
    assert health.weather_factor(weather(tmax=39), GROUNDNUT)[0] == 75


def test_water_rainfed_vs_irrigated_and_relief():
    dry_rainfed = health.water_factor(weather(rain14=4), "rainfed", GROUNDNUT)[0]
    dry_irrigated = health.water_factor(weather(rain14=4), "borewell", GROUNDNUT)[0]
    dry_relief = health.water_factor(weather(rain14=4, rain3=20), "rainfed", GROUNDNUT)[0]
    assert dry_rainfed < 20 < dry_irrigated
    assert dry_relief == pytest.approx(dry_rainfed + 10)
    assert health.water_factor(weather(rain14=200), "rainfed", GROUNDNUT)[0] == 65  # waterlogging


def test_missing_factor_is_reweighted_not_imputed():
    fh = health.compute_farm_health(satellite=sat(0.66), soil=soil(), weather=weather(), irrigation="borewell",
                                    profile=GROUNDNUT, stage_at_observation=STAGE, latest_diagnosis=None)
    assert fh.missing_factors == ["crop_condition"]
    assert sum(fh.effective_weights.values()) == pytest.approx(1.0, abs=1e-3)
    assert "crop_condition" not in fh.effective_weights
    factor = {f.key: f for f in fh.factors}
    assert factor["crop_condition"].status == "missing"
    expected = sum(factor[k].score * w for k, w in fh.effective_weights.items())
    assert fh.score == round(expected)


def test_crop_condition_from_recent_diagnosis():
    dx = {"diagnosis_id": "DX-1", "created_at": datetime.now(UTC).isoformat(),
          "result": {"severity": "moderate", "potential_conditions": [{"name": "Leaf spot"}]}}
    score, drivers, _ = health.crop_condition_factor(dx)
    assert score == 55 and "unverified" in drivers[0]
    old = {**dx, "created_at": "2020-01-01T00:00:00+00:00"}
    assert health.crop_condition_factor(old)[0] is None
