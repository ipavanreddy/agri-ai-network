from datetime import date

import pytest

from app.ai import runner
from app.ai.schemas import AskAI
from app.config import settings
from app.farms import geo
from app.intelligence import satellite, soil, weather
from app.interop.adapters import (
    AdapterError,
    load_state_dataset,
    map_record,
    resolve_district,
    state_config,
)
from app.sample_data import load_sample


def test_three_state_configs_map_to_canonical():
    expected = {"AP": ("groundnut", 2.4, date(2026, 7, 12), "te"),
                "MH": ("cotton", 3.0, date(2026, 6, 25), "hi"),  # Marathi falls back to Hindi
                "PB": ("wheat", 4.0, date(2025, 11, 10), "hi")}  # Punjabi falls back to Hindi
    for state, (crop, acres, sowing, lang) in expected.items():
        ds = load_state_dataset(state)
        field, farmer = ds["fields"][0], ds["farmers"][0]
        assert field.crop.crop_name == crop
        assert field.area_acres == pytest.approx(acres, abs=0.01)
        assert field.crop.sowing_date == sowing
        assert farmer.preferred_language == lang
        assert field.state == state and field.is_sample
        assert geo.area_acres(field.geometry) == pytest.approx(acres, rel=0.02)


def test_unit_conversions_punjab_soil():
    rec = {"lab_ref": "X", "zila": "Ludhiana", "block": "B", "ph": 7.8, "oc_g_per_kg": 4.1, "n_kg_per_acre": 100,
           "p_kg_per_acre": 10, "k_kg_per_acre": 50, "tested_on": "05-Oct-2025"}
    out = map_record("PB", "soil", rec)
    assert out["organic_carbon_pct"] == pytest.approx(0.41)
    assert out["nitrogen_kg_ha"] == pytest.approx(247.1, abs=0.1)
    assert out["measurement_date"] == date(2025, 10, 5)


def test_unknown_codes_and_districts_are_rejected():
    with pytest.raises(AdapterError):
        map_record("AP", "fields", {"booking_id": "1", "crop_code": "ZZ", "extent_ac": 1, "sowing_dt": "01/07/2026"})
    with pytest.raises(AdapterError):
        resolve_district(state_config("MH"), "Atlantis")
    assert resolve_district(state_config("AP"), "Anantapuramu")["name"] == "Anantapur"
    with pytest.raises(AdapterError):
        state_config("XX")


def test_open_meteo_parser_on_sample_shape():
    obs = weather.sample_weather("AP")
    assert obs.provenance.is_sample and obs.provenance.mode == "demo"
    assert len([d for d in obs.daily if d.is_forecast]) == 7
    assert obs.rain_past_14d_mm == pytest.approx(3.6)
    assert {a.code for a in obs.alerts} >= {"dry_spell", "rain_expected"}


def test_weather_falls_back_when_live_fails(monkeypatch):
    monkeypatch.setattr(settings, "use_public_apis", True)
    monkeypatch.setattr(weather, "fetch_open_meteo", lambda lat, lon: (_ for _ in ()).throw(TimeoutError("offline")))
    obs = weather.get_weather(14.5, 77.4, "AP")
    assert obs.provenance.mode == "demo" and "TimeoutError" in obs.provenance.note


def test_weather_live_path_uses_parser(monkeypatch):
    payload = {k: v for k, v in load_sample("weather/MH.json").items() if k != "_meta"}
    monkeypatch.setattr(settings, "use_public_apis", True)
    monkeypatch.setattr(weather, "fetch_open_meteo", lambda lat, lon: payload)
    obs = weather.get_weather(20.3, 77.9, "MH")
    assert obs.provenance.mode == "live" and not obs.provenance.is_sample
    assert any(a.code == "high_humidity" for a in obs.alerts)


def test_soilgrids_parser_units():
    payload = {"properties": {"layers": [
        {"name": "phh2o", "depths": [{"values": {"mean": 64}}, {"values": {"mean": 66}}]},
        {"name": "soc", "depths": [{"values": {"mean": 40}}, {"values": {"mean": 30}}]},
        {"name": "clay", "depths": [{"values": {"mean": 180}}, {"values": {"mean": 200}}]},
    ]}}
    assert soil.parse_soilgrids(payload) == {"phh2o": 6.5, "soc": 0.35, "clay": 19.0}


def test_soil_prefers_state_record_and_adds_texture():
    obs = soil.get_soil(14.56, 77.44, "AP", "Anantapur", "Rapthadu")
    assert obs.ph == 6.4 and obs.nitrogen_kg_ha == 176
    assert obs.clay_pct is not None and obs.texture_provenance.is_sample


def test_earth_engine_feature_parser():
    fc = {"features": [
        {"properties": {"date": "2026-09-01", "ndvi": 0.5, "ndmi": 0.1, "valid_fraction": 0.9}},
        {"properties": {"date": "2026-09-01", "ndvi": 0.6, "ndmi": 0.2, "valid_fraction": 1.0}},
        {"properties": {"date": "2026-08-20", "ndvi": 0.4, "ndmi": 0.0, "valid_fraction": 0.1}},  # too cloudy
        {"properties": {"date": "2026-08-10", "ndvi": None}},
    ]}
    assert satellite.parse_ee_features(fc) == [{"date": "2026-09-01", "ndvi": 0.55, "ndmi": 0.15, "valid_fraction": 0.95}]


def test_satellite_sample_when_ee_disabled_and_on_failure(monkeypatch):
    series, prov, _ = satellite.get_satellite_raw({}, "AP", date(2026, 7, 12))
    assert series and prov.is_sample and "EARTH_ENGINE_PROJECT" in prov.note
    monkeypatch.setattr(settings, "earth_engine_project", "demo-project")
    monkeypatch.setattr(satellite, "fetch_ndvi_series_ee", lambda *a: (_ for _ in ()).throw(RuntimeError("no creds")))
    series, prov, _ = satellite.get_satellite_raw({}, "AP", date(2026, 7, 12))
    assert prov.is_sample and "RuntimeError" in prov.note


def test_gemini_runner_live_demo_and_failure(monkeypatch):
    demo = lambda: AskAI(answer="demo", grounded_on=[], follow_up_suggestion="", requires_expert_review=False)
    result, meta = runner.run_structured("ask", "v1", AskAI, {"x": 1}, demo)
    assert result.answer == "demo" and meta.mode == "demo" and meta.prompt_version == "ask_v1"

    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    from app.ai import gemini

    def fake(prompt, schema, prompt_version, parts=None):
        assert "STRUCTURED CONTEXT" in prompt and "ask_v1" in prompt
        return schema(answer="live", grounded_on=["x"], follow_up_suggestion="", requires_expert_review=False), \
            gemini.AIProvenance(model_name=settings.gemini_model, model_version="v-test", prompt_version=prompt_version,
                                generated_at="2026-09-30T00:00:00Z")

    monkeypatch.setattr(gemini, "generate_structured", fake)
    result, meta = runner.run_structured("ask", "v1", AskAI, {"x": 1}, demo)
    assert result.answer == "live" and meta.mode == "live" and meta.model_name == settings.gemini_model

    monkeypatch.setattr(gemini, "generate_structured", lambda *a, **k: (_ for _ in ()).throw(ValueError("bad json")))
    result, meta = runner.run_structured("ask", "v1", AskAI, {"x": 1}, demo)
    assert result.answer == "demo" and "ValueError" in meta.fallback_reason


def test_geometry_validation():
    with pytest.raises(geo.GeometryError):
        geo.normalize({"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]})  # outside India
    with pytest.raises(geo.GeometryError):
        geo.normalize({"type": "Point", "coordinates": [77, 14]})
