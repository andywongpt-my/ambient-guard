"""Environmental layer (M2) tests — HTTP mocked with respx (no real network)."""
from __future__ import annotations

from datetime import datetime

import httpx
import pytest
import respx

from app.environmental.base import EnvironmentalError
from app.environmental.open_meteo import _AIR_URL, _FORECAST_URL, OpenMeteoProvider
from app.environmental.service import EnvironmentalService

NOW = datetime(2026, 9, 7, 12, 0, 0)

_FORECAST_JSON = {
    "hourly": {
        "time": ["2026-09-07T11:00", "2026-09-07T12:00", "2026-09-07T17:00"],
        "temperature_2m": [30.0, 31.0, 29.0],
        "relative_humidity_2m": [70, 68, 75],
        "wind_speed_10m": [10, 12, 8],
        "precipitation": [0, 0, 0.2],
        "uv_index": [6.0, 7.0, 3.0],
        "weather_code": [1, 2, 61],
    }
}
_AIR_JSON = {
    "hourly": {
        "time": ["2026-09-07T11:00", "2026-09-07T12:00", "2026-09-07T17:00"],
        "pm2_5": [20.0, 22.0, 42.0],
        "pm10": [30.0, 33.0, 55.0],
        "ozone": [40, 41, 38],
        "nitrogen_dioxide": [10, 11, 9],
        "us_aqi": [60, 62, 165],
    }
}


@respx.mock
def test_happy_path_at_17h():
    respx.get(_FORECAST_URL).mock(return_value=httpx.Response(200, json=_FORECAST_JSON))
    respx.get(_AIR_URL).mock(return_value=httpx.Response(200, json=_AIR_JSON))
    # Pass NOW as _fetched to ensure 17:00 is treated as forecast relative to "now" (noon)
    obs = OpenMeteoProvider().fetch(6.18, 116.22, when=NOW.replace(hour=17), _fetched=NOW)
    by = {o.metric: o for o in obs}
    assert by["temp_c"].value == 29.0 and by["temp_c"].unit == "°C"
    assert by["uv"].value == 3.0
    assert by["pm25"].value == 42.0 and by["pm25"].unit == "µg/m³"
    assert by["aqi"].value == 165.0
    # 17:00 is after NOW-fetch (noon) -> forecast; attribution present
    assert by["aqi"].kind == "forecast"
    assert "Open-Meteo" in by["aqi"].source.attribution


@respx.mock
def test_missing_metric_is_skipped_not_faked():
    fc = {"hourly": {"time": ["2026-09-07T12:00"], "temperature_2m": [31.0],
                     "uv_index": [None]}}  # uv null -> skipped
    respx.get(_FORECAST_URL).mock(return_value=httpx.Response(200, json=fc))
    respx.get(_AIR_URL).mock(return_value=httpx.Response(200, json={"hourly": {"time": ["2026-09-07T12:00"], "pm2_5": [22.0]}}))
    obs = OpenMeteoProvider().fetch(6.18, 116.22, when=NOW)
    metrics = {o.metric for o in obs}
    assert "temp_c" in metrics and "pm25" in metrics
    assert "uv" not in metrics


@respx.mock
def test_timeout_raises_environmental_error():
    respx.get(_FORECAST_URL).mock(side_effect=httpx.ConnectTimeout("timeout"))
    respx.get(_AIR_URL).mock(return_value=httpx.Response(200, json=_AIR_JSON))
    with pytest.raises(EnvironmentalError, match="failed after"):
        OpenMeteoProvider(retries=1).fetch(6.18, 116.22, when=NOW)


@respx.mock
def test_malformed_response_raises():
    respx.get(_FORECAST_URL).mock(return_value=httpx.Response(200, json={"nope": 1}))
    respx.get(_AIR_URL).mock(return_value=httpx.Response(200, json={"nope": 1}))
    with pytest.raises(EnvironmentalError):
        OpenMeteoProvider().fetch(6.18, 116.22, when=NOW)


@respx.mock
def test_service_collects_errors_without_hiding():
    respx.get(_FORECAST_URL).mock(side_effect=httpx.ConnectTimeout("t"))
    respx.get(_AIR_URL).mock(side_effect=httpx.ConnectTimeout("t"))
    svc = EnvironmentalService(providers=[OpenMeteoProvider(retries=0)])
    obs, errors = svc.observe(6.18, 116.22, when=NOW)
    assert obs == []
    assert errors and "open-meteo" in errors[0]


@respx.mock
def test_service_cache_hits_second_call():
    route_f = respx.get(_FORECAST_URL).mock(return_value=httpx.Response(200, json=_FORECAST_JSON))
    respx.get(_AIR_URL).mock(return_value=httpx.Response(200, json=_AIR_JSON))
    svc = EnvironmentalService(cache_ttl_s=300)
    o1, _ = svc.observe(6.18, 116.22, when=NOW)
    o2, _ = svc.observe(6.18, 116.22, when=NOW)
    assert o1 and o2
    assert route_f.call_count == 1     # second call served from cache
