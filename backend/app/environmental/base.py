"""Environmental base types: Observation, source attribution, Provider protocol.

Every value the layer emits is an Observation carrying its metric, value, unit,
kind (observed/forecast/estimate), and source (provider + fetch time + location).
This makes downstream reasoning fully attributable (FR-3.2 / FR-3.4).
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Protocol

from pydantic import BaseModel

Kind = Literal["observed", "forecast", "estimate", "direct-measurement"]


class EnvironmentalError(RuntimeError):
    """Raised when a provider fails. Surfaced explicitly — never hidden (FR-3.3)."""


class ObservationSource(BaseModel):
    provider: str
    fetched_at: datetime
    observed_at: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    attribution: str | None = None


class Observation(BaseModel):
    metric: str            # pm25 | pm10 | aqi | ozone | no2 | uv | temp_c | humidity | wind_kmh | precip_mm | weather
    value: float
    unit: str
    kind: Kind
    source: ObservationSource


class Provider(Protocol):
    name: str

    def fetch(
        self, latitude: float, longitude: float, when: datetime | None = None
    ) -> list[Observation]: ...
