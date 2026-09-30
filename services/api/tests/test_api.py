from pathlib import Path

from conftest import AP_FIELD, MH_FIELD, PB_FIELD

from app.canonical import export

POLYGON = {"type": "Polygon", "coordinates": [[[77.44, 14.56], [77.441, 14.56], [77.441, 14.561], [77.44, 14.561], [77.44, 14.56]]]}


def test_system_status_reports_demo_mode(client):
    res = client.get("/api/system/status").json()
    modes = {i["key"]: i["mode"] for i in res["integrations"]}
    assert res["demo_mode"] is True
    assert modes["gemini"] == "demo" and modes["earth_engine"] == "demo" and modes["store"] == "demo"


def test_states_and_adapter_demo(client):
    states = client.get("/api/states").json()
    assert {s["state_id"] for s in states} == {"AP", "MH", "PB"}
    demo = client.get("/api/states/PB/adapter-demo").json()
    field_example = next(e for e in demo["examples"] if e["entity"] == "field")
    assert field_example["raw"]["fasal"] == "kanak" and field_example["canonical"]["crop"]["crop_name"] == "wheat"
    assert client.get("/api/states/XX").status_code == 404


def test_seeded_fields_come_through_adapters(client):
    ids = {f["field_id"] for f in client.get("/api/fields").json()}
    assert {AP_FIELD, MH_FIELD, PB_FIELD} <= ids


def test_farmer_and_field_validation(client):
    assert client.post("/api/farmers", json={"name": "X", "state": "AP", "district": "Nowhere"}).status_code == 422
    farmer = client.post("/api/farmers", json={"name": "Ravi", "state": "ap", "district": "Anantapuramu", "preferred_language": "te"})
    assert farmer.status_code == 201 and farmer.json()["district"] == "Anantapur"
    fid = farmer.json()["farmer_id"]
    bad_crop = client.post("/api/fields", json={"farmer_id": fid, "geometry": POLYGON, "crop_name": "wheat"})
    assert bad_crop.status_code == 422  # wheat is not configured for AP
    bad_geom = client.post("/api/fields", json={"farmer_id": fid, "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 1], [0, 1]]]},
                                               "crop_name": "groundnut"})
    assert bad_geom.status_code == 422
    field = client.post("/api/fields", json={"farmer_id": fid, "geometry": POLYGON, "crop_name": "groundnut",
                                             "sowing_date": "2026-07-10"}).json()
    assert 2.5 < field["area_acres"] < 3.2 and field["crop"]["season"] == "kharif"
    assert client.patch(f"/api/farmers/{fid}", json={"preferred_language": "hi"}).json()["preferred_language"] == "hi"


def test_intelligence_endpoints(client):
    intel = client.get(f"/api/fields/{AP_FIELD}/intelligence").json()
    assert {s["category"] for s in intel["data_sources"]} >= {"weather", "soil", "satellite"}
    assert intel["demo_mode"] is True
    assert all(s["is_sample"] for s in intel["data_sources"])
    for part in ("weather", "soil", "satellite", "health"):
        assert client.get(f"/api/fields/{AP_FIELD}/{part}").status_code == 200
    assert client.get("/api/fields/NOPE/intelligence").status_code == 404


def test_diagnosis_rejects_non_images(client):
    res = client.post("/api/diagnosis", files={"image": ("x.txt", b"hello" * 100, "text/plain")}, data={"crop": "cotton"})
    assert res.status_code == 422


def test_localization_demo_fallbacks(client):
    tr = client.post("/api/translate", json={"texts": ["hello"], "target": "te"}).json()
    assert tr["method"] == "unavailable" and tr["mode"] == "demo"
    tts = client.post("/api/text-to-speech", json={"text": "hello", "language": "hi"}).json()
    assert tts["use_browser_tts"] is True
    stt = client.post("/api/speech-to-text", files={"audio": ("a.webm", b"\x1a\x45\xdf\xa3" * 10, "audio/webm")},
                      data={"language": "te"}).json()
    assert stt["use_browser_speech"] is True


def test_officer_analytics(client):
    overview = client.get("/api/overview").json()
    assert len(overview["states"]) == 3 and overview["demo_mode"] is True
    ap = client.get("/api/states/AP/analytics").json()
    assert ap["provenance"]["is_sample"] and ap["totals"]["farmers_represented"] > 0
    assert "groundnut" in list(ap["crop_distribution_pct"])[:2]
    risks = client.get("/api/districts/MH-YTL/risks").json()
    assert risks["district"] == "Yavatmal" and any(r["type"] == "weather" for r in risks["risks"])
    assert client.get("/api/districts/MH-NOPE/risks").status_code == 404
    assert client.post("/api/reviews/advisories/NOPE", json={"decision": "approve"}).status_code == 404


def test_committed_schemas_match_models():
    for path, content in export.rendered().items():
        assert Path(path).read_text() == content, f"{path} is stale: run `uv run python -m app.canonical.export`"
