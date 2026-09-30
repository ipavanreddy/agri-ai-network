"""Google Maps Platform (server side, MAPS_API_KEY): Geocoding, Places and Routes.

- `geocode(query)`: village / town search so a farmer can jump the map to their location (FR-02).
- `reverse_geocode(lat, lon)`: fills village / sub-district for a newly drawn field when the farmer left it empty.
- `nearest_support(lat, lon)`: nearest Krishi Vigyan Kendras / agriculture offices (Places) with real driving
  distance and time (Routes), so the Crop Doctor's "confirm with your local officer or KVK" step is actionable.

Without MAPS_API_KEY every function raises NotConfigured and callers degrade to a labelled demo response.
"""

import logging
import math
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

import httpx

from app.config import settings

log = logging.getLogger(__name__)

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
PLACES_TEXT_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
TIMEOUT = 8.0
SUPPORT_QUERIES = ("Krishi Vigyan Kendra", "agriculture office")


class NotConfigured(RuntimeError):
    pass


def _key() -> str:
    if not settings.maps_api_key:
        raise NotConfigured("MAPS_API_KEY not set")
    return settings.maps_api_key


def _component(result: dict[str, Any], *types: str) -> str | None:
    for t in types:
        for c in result.get("address_components", []):
            if t in c.get("types", []):
                return c.get("long_name")
    return None


def _place(result: dict[str, Any]) -> dict[str, Any]:
    loc = result["geometry"]["location"]
    return {
        "label": result.get("formatted_address"),
        "lat": round(loc["lat"], 6),
        "lon": round(loc["lng"], 6),
        "village": _component(result, "locality", "sublocality_level_1", "sublocality", "neighborhood"),
        "sub_district": _component(result, "administrative_area_level_3"),
        "district": _component(result, "administrative_area_level_2", "administrative_area_level_3"),
        "state": _component(result, "administrative_area_level_1"),
    }


def _check(body: dict[str, Any]) -> dict[str, Any]:
    status = body.get("status")
    if status not in ("OK", "ZERO_RESULTS"):
        raise RuntimeError(f"Maps API status {status}: {body.get('error_message', '')}".strip())
    return body


def geocode(query: str, limit: int = 5) -> list[dict[str, Any]]:
    res = httpx.get(GEOCODE_URL, params={"address": query, "region": "in", "components": "country:IN",
                                         "key": _key()}, timeout=TIMEOUT)
    res.raise_for_status()
    return [_place(r) for r in _check(res.json()).get("results", [])[:limit]]


@lru_cache(maxsize=512)
def reverse_geocode(lat: float, lon: float) -> dict[str, Any] | None:
    res = httpx.get(GEOCODE_URL, params={"latlng": f"{lat},{lon}", "key": _key()}, timeout=TIMEOUT)
    res.raise_for_status()
    results = _check(res.json()).get("results", [])
    if not results:
        return None
    place = _place(results[0])
    # the first result is often a premise; take village / district from the first result that has them
    for key in ("village", "sub_district", "district", "state"):
        if not place[key]:
            place[key] = next((v for r in results[1:] if (v := _place(r)[key])), None)
    return place


def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    (lat1, lon1), (lat2, lon2) = (tuple(map(math.radians, p)) for p in (a, b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def drive_route(origin: tuple[float, float], dest: tuple[float, float]) -> dict[str, Any] | None:
    res = httpx.post(ROUTES_URL, timeout=TIMEOUT, headers={
        "X-Goog-Api-Key": _key(), "X-Goog-FieldMask": "routes.distanceMeters,routes.duration"}, json={
        "origin": {"location": {"latLng": {"latitude": origin[0], "longitude": origin[1]}}},
        "destination": {"location": {"latLng": {"latitude": dest[0], "longitude": dest[1]}}},
        "travelMode": "DRIVE"})
    res.raise_for_status()
    routes = res.json().get("routes") or []
    if not routes or "distanceMeters" not in routes[0]:
        return None
    return {"distance_km": round(routes[0]["distanceMeters"] / 1000, 1),
            "duration_min": round(int(str(routes[0].get("duration", "0s")).rstrip("s") or 0) / 60)}


@lru_cache(maxsize=256)
def nearest_support(lat: float, lon: float, limit: int = 3) -> dict[str, Any]:
    """Nearest KVKs / agriculture offices within ~60 km, with driving distance and time."""
    seen: dict[str, dict[str, Any]] = {}
    for query in SUPPORT_QUERIES:
        res = httpx.get(PLACES_TEXT_URL, params={"query": query, "location": f"{lat},{lon}", "radius": 60000,
                                                 "region": "in", "key": _key()}, timeout=TIMEOUT)
        res.raise_for_status()
        for r in _check(res.json()).get("results", []):
            loc = r["geometry"]["location"]
            seen.setdefault(r["place_id"], {
                "name": r.get("name"), "address": r.get("formatted_address"), "lat": loc["lat"], "lon": loc["lng"],
                "kind": "Krishi Vigyan Kendra" if "krishi" in (r.get("name") or "").lower() else "Agriculture office",
                "straight_km": round(_haversine_km((lat, lon), (loc["lat"], loc["lng"])), 1),
                "maps_url": f"https://www.google.com/maps/search/?api=1&query={loc['lat']},{loc['lng']}"
                            f"&query_place_id={r['place_id']}",
            })
    places = sorted((p for p in seen.values() if p["straight_km"] <= 80), key=lambda p: p["straight_km"])[:limit]
    for p in places:
        try:
            p.update(drive_route((lat, lon), (p["lat"], p["lon"])) or {})
        except Exception as exc:  # distance is optional; keep the place
            log.warning("Routes API failed: %s", exc)
    return {"places": places, "mode": "live", "source": "Google Maps Places (Text Search) + Routes API",
            "retrieved_at": datetime.now(UTC).isoformat()}
