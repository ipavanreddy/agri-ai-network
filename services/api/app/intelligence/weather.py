"""Weather adapter: Open-Meteo (keyless, live) with a labelled sample fallback in the same response shape."""

import logging
from datetime import UTC, date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from app.canonical.models import (
    DailyWeather,
    GeoPoint,
    Provenance,
    WeatherAlert,
    WeatherObservation,
)
from app.config import settings
from app.sample_data import load_sample, sample_provenance

log = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_PARAMS = {
    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max",
    "hourly": "soil_moisture_3_to_9cm",
    "past_days": 14,
    "forecast_days": 7,
    "timezone": "Asia/Kolkata",
}


def fetch_open_meteo(lat: float, lon: float) -> dict[str, Any]:
    res = httpx.get(OPEN_METEO_URL, params={"latitude": lat, "longitude": lon, **OPEN_METEO_PARAMS},
                    timeout=settings.public_api_timeout_s)
    res.raise_for_status()
    return res.json()


def _num(v: Any) -> float | None:
    return None if v is None else float(v)


def derive_alerts(obs: WeatherObservation) -> list[WeatherAlert]:
    """Simple, explainable rule-based alerts (IMD-style thresholds)."""
    alerts: list[WeatherAlert] = []
    forecast = [d for d in obs.daily if d.is_forecast]
    heavy = [d for d in forecast[:3] if (d.rain_mm or 0) >= 64.5]
    if heavy:
        alerts.append(WeatherAlert(code="heavy_rain", severity="high",
                                   message=f"Heavy rain forecast ({heavy[0].rain_mm:.0f} mm on {heavy[0].date})"))
    elif (obs.rain_next_3d_mm or 0) >= 10:
        alerts.append(WeatherAlert(code="rain_expected", severity="low",
                                   message=f"{obs.rain_next_3d_mm:.0f} mm rain expected in the next 3 days"))
    if obs.rain_past_14d_mm is not None and obs.rain_past_14d_mm < 5:
        alerts.append(WeatherAlert(code="dry_spell", severity="medium",
                                   message=f"Dry spell: only {obs.rain_past_14d_mm:.0f} mm rain in the last 14 days"))
    if obs.rain_past_14d_mm is not None and obs.rain_past_14d_mm >= 120:
        alerts.append(WeatherAlert(code="excess_rain", severity="medium",
                                   message=f"Excess rain: {obs.rain_past_14d_mm:.0f} mm in the last 14 days"))
    if (obs.humidity_pct or 0) >= 85:
        alerts.append(WeatherAlert(code="high_humidity", severity="medium",
                                   message=f"High humidity ({obs.humidity_pct:.0f}%) favours fungal disease"))
    if obs.tmax_next_7d_c is not None and obs.tmax_next_7d_c >= 40:
        alerts.append(WeatherAlert(code="heat", severity="high", message=f"Heat: up to {obs.tmax_next_7d_c:.0f} °C forecast"))
    winds = [d.wind_max_kmh or 0 for d in forecast[:3]]
    if winds and max(winds) >= 40:
        alerts.append(WeatherAlert(code="strong_wind", severity="medium", message=f"Strong wind up to {max(winds):.0f} km/h"))
    return alerts


def parse_open_meteo(payload: dict[str, Any], provenance: Provenance) -> WeatherObservation:
    """Parse an Open-Meteo forecast response (live or sample-shaped) into the canonical model."""
    cur = payload.get("current", {})
    daily = payload.get("daily", {})
    ref_day = date.fromisoformat(cur["time"][:10]) if cur.get("time") else date.today()
    days: list[DailyWeather] = []
    for i, d in enumerate(daily.get("time", [])):
        dd = date.fromisoformat(d)
        days.append(DailyWeather(
            date=dd,
            tmax_c=_num(daily["temperature_2m_max"][i]),
            tmin_c=_num(daily["temperature_2m_min"][i]),
            rain_mm=_num(daily["precipitation_sum"][i]),
            rain_probability_pct=_num((daily.get("precipitation_probability_max") or [None] * (i + 1))[i]),
            wind_max_kmh=_num(daily["wind_speed_10m_max"][i]),
            is_forecast=dd >= ref_day,
        ))
    past = [d for d in days if not d.is_forecast]
    fut = [d for d in days if d.is_forecast]
    sm = [v for v in (payload.get("hourly", {}).get("soil_moisture_3_to_9cm") or []) if v is not None]
    obs = WeatherObservation(
        location=GeoPoint(lat=payload["latitude"], lon=payload["longitude"]),
        temperature_c=_num(cur.get("temperature_2m")),
        humidity_pct=_num(cur.get("relative_humidity_2m")),
        wind_kmh=_num(cur.get("wind_speed_10m")),
        precipitation_mm=_num(cur.get("precipitation")),
        soil_moisture_m3_m3=round(sm[len(sm) // 2], 3) if sm else None,
        daily=days,
        rain_past_14d_mm=round(sum(d.rain_mm or 0 for d in past[-14:]), 1) if past else None,
        rain_next_3d_mm=round(sum(d.rain_mm or 0 for d in fut[:3]), 1) if fut else None,
        rain_next_7d_mm=round(sum(d.rain_mm or 0 for d in fut[:7]), 1) if fut else None,
        tmax_next_7d_c=max((d.tmax_c for d in fut[:7] if d.tmax_c is not None), default=None),
        timestamp=datetime.fromisoformat(cur["time"]).replace(tzinfo=ZoneInfo(payload.get("timezone") or "UTC"))
        if cur.get("time") else None,
        provenance=provenance,
    )
    obs.alerts = derive_alerts(obs)
    return obs


def sample_weather(state: str, note: str | None = None) -> WeatherObservation:
    payload = load_sample(f"weather/{state}.json")
    return parse_open_meteo(payload, sample_provenance(payload["_meta"], note))


def get_weather(lat: float, lon: float, state: str, force_sample: bool = False) -> WeatherObservation:
    if settings.use_public_apis and not force_sample:
        try:
            payload = fetch_open_meteo(lat, lon)
            return parse_open_meteo(payload, Provenance(
                source="Open-Meteo forecast API (ECMWF/GFS/ICON blend)",
                source_url="https://open-meteo.com",
                reference_timestamp=datetime.now(UTC),
                geographic_scope=f"{lat:.4f},{lon:.4f}",
                mode="live",
            ))
        except Exception as exc:
            log.warning("Open-Meteo unavailable: %s", exc)
            return sample_weather(state, f"Live weather unavailable ({type(exc).__name__}); showing {state} sample scenario")
    return sample_weather(state, f"Sample weather for the {state} demo scenario (not live for this field)")
