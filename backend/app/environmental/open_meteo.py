"""Open-Meteo provider — weather + UV (forecast API) and air quality (air-quality API).

No API key required. Two endpoints:
  https://api.open-meteo.com/v1/forecast          -> temp, humidity, wind, precip, uv, weather_code
  https://air-quality-api.open-meteo.com/v1/air-quality -> pm2_5, pm10, ozone, no2, us_aqi

We request hourly series and select the hour nearest `when` (default: now). Values
selected from a future hour are tagged kind="forecast", past/current as "observed".
Failures raise EnvironmentalError (surfaced, never hidden — FR-3.3).
"""
from __future__ import annotations

from datetime import datetime

import httpx

from app.environmental.base import EnvironmentalError, Observation, ObservationSource

_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

_FORECAST_HOURLY = [
    "temperature_2m", "relative_humidity_2m", "wind_speed_10m",
    "precipitation", "uv_index", "weather_code",
]
_AIR_HOURLY = ["pm2_5", "pm10", "ozone", "nitrogen_dioxide", "us_aqi"]

# hourly key -> (metric, unit)
_FORECAST_MAP = {
    "temperature_2m": ("temp_c", "°C"),
    "relative_humidity_2m": ("humidity", "%"),
    "wind_speed_10m": ("wind_kmh", "km/h"),
    "precipitation": ("precip_mm", "mm"),
    "uv_index": ("uv", "index"),
    "weather_code": ("weather", "wmo"),
}
_AIR_MAP = {
    "pm2_5": ("pm25", "µg/m³"),
    "pm10": ("pm10", "µg/m³"),
    "ozone": ("ozone", "µg/m³"),
    "nitrogen_dioxide": ("no2", "µg/m³"),
    "us_aqi": ("aqi", "AQI"),
}


class OpenMeteoProvider:
    name = "open-meteo"

    def __init__(self, timeout: float = 10.0, retries: int = 2) -> None:
        self._timeout = timeout
        self._retries = retries

    def _get(self, url: str, params: dict) -> dict:
        last: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                r = httpx.get(url, params=params, timeout=self._timeout)
                r.raise_for_status()
                return r.json()
            except (httpx.HTTPError, ValueError) as e:   # includes timeout + bad JSON
                last = e
        raise EnvironmentalError(f"open-meteo request failed after {self._retries + 1} tries: {last}")

    @staticmethod
    def _nearest_index(times: list[str], when: datetime) -> int:
        target = when.replace(minute=0, second=0, microsecond=0)
        best_i, best_gap = 0, None
        for i, t in enumerate(times):
            try:
                ts = datetime.fromisoformat(t)
            except ValueError:
                continue
            gap = abs((ts - target).total_seconds())
            if best_gap is None or gap < best_gap:
                best_i, best_gap = i, gap
        return best_i

    def _series_to_obs(self, data: dict, mapping: dict, lat: float, lon: float,
                       when: datetime, fetched: datetime) -> list[Observation]:
        hourly = data.get("hourly") or {}
        times = hourly.get("time") or []
        if not times:
            raise EnvironmentalError("open-meteo response missing hourly.time")
        idx = self._nearest_index(times, when)
        try:
            obs_at = datetime.fromisoformat(times[idx])
        except ValueError:
            obs_at = None
        kind = "forecast" if obs_at and obs_at > fetched else "observed"

        out: list[Observation] = []
        for key, (metric, unit) in mapping.items():
            arr = hourly.get(key)
            if not arr or idx >= len(arr) or arr[idx] is None:
                continue                        # missing metric: skip, don't fabricate
            val = arr[idx]
            if not isinstance(val, (int, float)):
                continue                        # validation: reject non-numeric
            out.append(Observation(
                metric=metric, value=float(val), unit=unit, kind=kind,
                source=ObservationSource(
                    provider=self.name, fetched_at=fetched, observed_at=obs_at,
                    latitude=lat, longitude=lon,
                    attribution="Open-Meteo (CC BY 4.0)",
                ),
            ))
        return out

    def fetch(self, latitude: float, longitude: float,
              when: datetime | None = None) -> list[Observation]:
        when = when or datetime.now()
        fetched = datetime.now()
        common = {"latitude": latitude, "longitude": longitude,
                  "timezone": "auto", "forecast_days": 2}

        weather = self._get(_FORECAST_URL,
                            {**common, "hourly": ",".join(_FORECAST_HOURLY)})
        air = self._get(_AIR_URL,
                        {**common, "hourly": ",".join(_AIR_HOURLY)})

        obs = self._series_to_obs(weather, _FORECAST_MAP, latitude, longitude, when, fetched)
        obs += self._series_to_obs(air, _AIR_MAP, latitude, longitude, when, fetched)
        if not obs:
            raise EnvironmentalError("open-meteo returned no usable observations")
        return obs
