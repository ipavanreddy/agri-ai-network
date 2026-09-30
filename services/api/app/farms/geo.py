"""Small geometry helpers for field polygons (GeoJSON, [lon, lat])."""

import math
from typing import Any

SQM_PER_ACRE = 4046.8564224
EARTH_R = 6_371_008.8


class GeometryError(ValueError):
    pass


def ring_of(geometry: dict[str, Any]) -> list[list[float]]:
    if geometry.get("type") != "Polygon" or not geometry.get("coordinates"):
        raise GeometryError("geometry must be a GeoJSON Polygon")
    ring = [[float(p[0]), float(p[1])] for p in geometry["coordinates"][0]]
    if ring and ring[0] != ring[-1]:
        ring.append(ring[0])
    if len({tuple(p) for p in ring}) < 3:
        raise GeometryError("polygon needs at least 3 distinct points")
    for lon, lat in ring:
        if not (6.0 <= lat <= 37.5 and 68.0 <= lon <= 98.0):
            raise GeometryError("field must be inside India (lat 6-37.5, lon 68-98)")
    return ring


def normalize(geometry: dict[str, Any]) -> dict[str, Any]:
    return {"type": "Polygon", "coordinates": [ring_of(geometry)]}


def area_acres(geometry: dict[str, Any]) -> float:
    """Planar area on a local equirectangular projection (accurate for field-sized polygons)."""
    ring = ring_of(geometry)
    lat0 = math.radians(sum(p[1] for p in ring[:-1]) / (len(ring) - 1))
    pts = [(math.radians(lon) * EARTH_R * math.cos(lat0), math.radians(lat) * EARTH_R) for lon, lat in ring]
    s = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:]))
    return round(abs(s) / 2 / SQM_PER_ACRE, 3)


def centroid(geometry: dict[str, Any]) -> tuple[float, float]:
    """Returns (lat, lon): vertex mean, good enough for convex-ish field polygons."""
    ring = ring_of(geometry)[:-1]
    return (round(sum(p[1] for p in ring) / len(ring), 6), round(sum(p[0] for p in ring) / len(ring), 6))
