"""End-to-end demo-mode journey through the API (PRD §44):
field -> intelligence + Farm Health -> advisory (+ Telugu) -> crop recommendation -> Crop Doctor ->
voice question -> officer review."""

from conftest import AP_FIELD


def test_demo_journey_end_to_end(client, leaf_png):
    # 1. Farmer + field (drawn polygon near the Anantapur scenario)
    farmer = client.post("/api/farmers", json={"name": "Lakshmi (journey)", "state": "AP", "district": "Anantapur",
                                              "block": "Rapthadu", "preferred_language": "te"}).json()
    polygon = {"type": "Polygon", "coordinates": [[[77.4410, 14.5595], [77.4424, 14.5595], [77.4424, 14.5610],
                                                   [77.4410, 14.5610], [77.4410, 14.5595]]]}
    field = client.post("/api/fields", json={"farmer_id": farmer["farmer_id"], "geometry": polygon, "crop_name": "groundnut",
                                            "sowing_date": "2026-07-12", "irrigation": "rainfed"}).json()
    fid = field["field_id"]

    # 2. Weather + soil + satellite -> Farm Health (sample data, labelled)
    intel = client.get(f"/api/fields/{fid}/intelligence").json()
    assert intel["demo_mode"] is True
    health = intel["health"]
    assert 0 <= health["score"] <= 100 and health["band"] in ("Good", "Moderate", "Poor")
    assert "crop_condition" in health["missing_factors"]
    assert intel["soil"]["ph"] == 6.4  # Soil Health Card record matched by block via the AP adapter
    before = health["score"]

    # 3. Advisory: observed -> interpretation -> recommendation, with provenance + review
    adv = client.post("/api/advisory/generate", json={"field_id": fid, "language": "te"}).json()
    content = adv["content"]
    assert content["observations"] and content["interpretations"] and content["recommendations"]
    assert content["regenerative_practice"]["action"]
    assert adv["model_name"] == "demo-rules" and adv["prompt_version"] == "advisory_v1" and adv["model_version"]
    assert adv["review"]["status"] == "pending_officer_review" and adv["demo_mode"] is True
    assert "delay irrigation" in content["recommendations"][0]["action"].lower()
    te = adv["localized"]["te"]
    assert te["method"] == "demo_catalog" and te["content"]["summary"] != content["summary"]
    assert te["content"]["risk_level"] == content["risk_level"]  # same analysis, different language
    hi = client.post(f"/api/advisories/{adv['advisory_id']}/localize", json={"language": "hi"}).json()
    assert hi["language"] == "hi" and "मूंगफली" in hi["content"]["summary"]

    # 4. Crop recommendation: >= 3 options with suitability
    rec = client.post("/api/crop-recommendation", json={"field_id": fid}).json()
    assert len(rec["options"]) >= 3
    assert all(o["suitability"] in ("High", "Moderate", "Low") and o["reasons"] for o in rec["options"])
    assert rec["prompt_version"] == "crop_recommendation_v1"

    # 5. Crop Doctor: image upload -> potential condition, confidence, next action
    dx = client.post("/api/diagnosis", files={"image": ("leaf.png", leaf_png, "image/png")}, data={"field_id": fid}).json()
    assert "potential" in dx["potential_condition"].lower()
    assert 0 <= dx["confidence"] <= 1 and dx["recommendation"]
    assert dx["result"]["requires_expert_review"] is True and "not a certified diagnosis" in dx["disclaimer"]
    assert client.get(f"/api/diagnoses/{dx['diagnosis_id']}/image").status_code == 200

    # Crop condition now contributes to Farm Health
    after = client.get(f"/api/fields/{fid}/health").json()["health"]
    assert "crop_condition" not in after["missing_factors"] and after["score"] != before

    # 6. Voice/text question in Telugu, answered from farm context
    ans = client.post("/api/ask", json={"field_id": fid, "question": "వర్షం ఎప్పుడు వస్తుంది? నీటి తడి ఇవ్వాలా?",
                                        "language": "te"}).json()
    assert ans["intent"] == "water" and "మి.మీ." in ans["answer"]

    # 7. Officer: review queue -> approve advisory; analytics show platform activity
    queue = client.get("/api/review-queue").json()
    assert {adv["advisory_id"], dx["diagnosis_id"], rec["recommendation_id"]} <= {i["id"] for i in queue}
    ok = client.post(f"/api/reviews/advisories/{adv['advisory_id']}", json={"decision": "approve", "note": "Agree"}).json()
    assert ok["review"]["status"] == "approved"
    assert client.get(f"/api/advisories/{adv['advisory_id']}").json()["review"]["status"] == "approved"
    activity = client.get("/api/states/AP/analytics").json()["platform_activity"]
    assert activity["diagnoses"] >= 1 and activity["advisories_generated"] >= 1


def test_same_services_work_for_every_state(client):
    for fid in (AP_FIELD, "FLD-PN-2026-0091", "FLD-PB-34--12"):
        adv = client.post("/api/advisory/generate", json={"field_id": fid}).json()
        rec = client.post("/api/crop-recommendation", json={"field_id": fid}).json()
        assert adv["content"]["summary"] and len(rec["options"]) >= 3
