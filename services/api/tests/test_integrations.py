"""Integration status must never claim "live" for something that is not working, and Maps features degrade cleanly."""

from app import system
from app.config import settings
from tests.conftest import AP_FIELD


def test_status_all_demo_without_keys(client):
    items = {i["key"]: i for i in client.get("/api/system/status").json()["integrations"]}
    for key in ("gemini", "earth_engine", "maps_server", "translation", "speech", "store", "bigquery", "storage"):
        assert items[key]["mode"] == "demo", key


def test_failing_probe_is_reported_as_demo(monkeypatch):
    monkeypatch.setattr(settings, "maps_api_key", "configured-but-broken")

    def boom() -> str:
        raise RuntimeError("REQUEST_DENIED")

    monkeypatch.setitem(system.PROBES, "maps_server", (lambda: True, boom))
    system.probe_integrations(force=True)
    row = next(i for i in system.integrations() if i["key"] == "maps_server")
    assert row["mode"] == "demo" and "REQUEST_DENIED" in row["detail"]
    monkeypatch.setattr(settings, "maps_api_key", "")
    system.probe_integrations(force=True)


def test_maps_endpoints_demo_mode(client):
    geo = client.get("/api/geocode", params={"q": "Kalyandurg"}).json()
    assert geo["mode"] == "demo" and geo["results"] == []
    near = client.get(f"/api/fields/{AP_FIELD}/nearby-support").json()
    assert near["mode"] == "demo" and near["places"] == []
    assert client.get("/api/fields/NOPE/nearby-support").status_code == 404


def test_cors_allows_cloud_run_frontends(client):
    ok = "https://agri-ai-network-farmer-web-847963771142.asia-south1.run.app"
    res = client.get("/health", headers={"Origin": ok})
    assert res.headers.get("access-control-allow-origin") == ok
    res = client.get("/health", headers={"Origin": "https://evil.example.com"})
    assert "access-control-allow-origin" not in res.headers
