"""Environmental timeline (M5).

Builds an hourly timeline of environmental conditions and labels each entry along
TWO independent axes, per the spec's exposure terminology:

  data_kind      : observed | forecast   — derived from each Observation's own `kind`
                   (the provider tags a reading observed if its hour <= fetch time,
                   forecast if it is in the future). Per entry we take the WORST/most-
                   forward kind across that hour's metrics (forecast if any metric is
                   forecast, else observed).
  exposure_kind  : estimate | direct-measurement — how the exposure was obtained.
                   Absent a physical personal sensor, ALL current readings are
                   location/API-based, i.e. `estimate` ("estimated environmental
                   exposure"). A future BLE PM2.5/CO2/VOC sensor would yield
                   `direct-measurement`. This is set from the provider/source, never
                   claimed as a personal measurement (SECURITY_AND_PRIVACY.md).

The entry whose hour contains the planned activity time is flagged is_planned.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from pydantic import BaseModel

from app.environmental.base import Observation

# Providers that represent location/API-based estimates (not a personal sensor).
_ESTIMATE_PROVIDERS = {"open-meteo", "openaq"}


class TimelineEntry(BaseModel):
    time: datetime
    data_kind: str          # observed | forecast
    exposure_kind: str      # estimate | direct-measurement
    is_planned: bool = False
    aqi: float | None = None
    uv: float | None = None
    temp_c: float | None = None
    pm25: float | None = None
    sources: list[str] = []


def _exposure_kind(obs: list[Observation]) -> str:
    # direct-measurement only if EVERY reading came from a physical sensor source.
    if obs and all(o.source.provider not in _ESTIMATE_PROVIDERS for o in obs):
        # a non-API provider present today would be a real sensor; none exist yet
        if all(o.kind == "direct-measurement" for o in obs):
            return "direct-measurement"
    return "estimate"


def build_timeline(
    observe,                      # callable(lat, lon, when) -> (list[Observation], errors)
    lat: float,
    lon: float,
    *,
    hours: int = 6,
    now: datetime | None = None,
    planned_time: datetime | None = None,
) -> list[TimelineEntry]:
    now = (now or datetime.now()).replace(minute=0, second=0, microsecond=0)
    planned_hour = planned_time.replace(minute=0, second=0, microsecond=0) if planned_time else None

    entries: list[TimelineEntry] = []
    for h in range(hours + 1):
        when = now + timedelta(hours=h)
        obs, _errors = observe(lat, lon, when=when)
        by = {o.metric: o for o in obs}
        # data_kind from the observations themselves: forecast if any metric is forecast.
        kinds = {o.kind for o in obs}
        data_kind = "forecast" if ("forecast" in kinds or when > datetime.now()) else "observed"
        entries.append(TimelineEntry(
            time=when,
            data_kind=data_kind,
            exposure_kind=_exposure_kind(obs),
            is_planned=(planned_hour is not None and when == planned_hour),
            aqi=by["aqi"].value if "aqi" in by else None,
            uv=by["uv"].value if "uv" in by else None,
            temp_c=by["temp_c"].value if "temp_c" in by else None,
            pm25=by["pm25"].value if "pm25" in by else None,
            sources=sorted({o.source.provider for o in obs}),
        ))
    return entries
