"""EnvironmentalService — orchestrates providers with a short TTL cache and
explicit failure collection. Provider errors are returned to the caller, never
silently swallowed (FR-3.3).
"""
from __future__ import annotations

import time
from datetime import datetime

from app.environmental.base import EnvironmentalError, Observation, Provider
from app.environmental.open_meteo import OpenMeteoProvider


class EnvironmentalService:
    def __init__(self, providers: list[Provider] | None = None,
                 cache_ttl_s: float = 300.0) -> None:
        self._providers = providers if providers is not None else [OpenMeteoProvider()]
        self._ttl = cache_ttl_s
        self._cache: dict[tuple, tuple[float, list[Observation]]] = {}

    def observe(self, latitude: float, longitude: float,
                when: datetime | None = None) -> tuple[list[Observation], list[str]]:
        """Return (observations, provider_errors). Errors are explicit, not hidden."""
        key = (round(latitude, 3), round(longitude, 3),
               when.replace(minute=0, second=0, microsecond=0).isoformat() if when else "now")
        now = time.monotonic()
        cached = self._cache.get(key)
        if cached and (now - cached[0]) < self._ttl:
            return cached[1], []

        observations: list[Observation] = []
        errors: list[str] = []
        for p in self._providers:
            try:
                observations.extend(p.fetch(latitude, longitude, when))
            except EnvironmentalError as e:
                errors.append(f"{getattr(p, 'name', 'provider')}: {e}")

        if observations:
            self._cache[key] = (now, observations)
        return observations, errors
