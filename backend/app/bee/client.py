"""Bee client — the single boundary between Ambient Guard and Bee.

Backends (selected by AMBIENT_GUARD_BEE_MODE):
  cli   -> shell out to the local `bee` CLI with --json (LIVE, default on dev host)
  mock  -> fixture-backed, for tests / offline dev ONLY (never the demo path)
  mcp   -> reserved (M1.3); raises until implemented

Privacy (SECURITY_AND_PRIVACY.md): raw Bee payloads are returned to the caller for
immediate normalization and never persisted here. Tokens live only in the Bee
credential store; this module never reads or logs them.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Protocol

from app.bee.models import BeeCurrentLocation, BeeSearchResult, BeeTodayContext


class BeeError(RuntimeError):
    """Raised when Bee is unreachable, not authenticated, or returns bad data.

    Surfaced explicitly to the API layer — Bee failures are never silently
    swallowed into empty context (FR-1.2).
    """


class BeeClient(Protocol):
    def today_context(self) -> BeeTodayContext: ...
    def current_location(self) -> BeeCurrentLocation: ...
    def search(self, query: str, limit: int = 5) -> BeeSearchResult: ...


# --------------------------------------------------------------------------- CLI

class CliBeeClient:
    """Live backend: runs `bee <cmd> --json` as a subprocess and parses stdout."""

    def __init__(self, bee_bin: str | None = None, timeout: float = 20.0) -> None:
        self._bin = bee_bin or os.getenv("AMBIENT_GUARD_BEE_BIN") or "bee"
        self._timeout = timeout

    def _run(self, args: list[str]) -> dict:
        exe = shutil.which(self._bin)
        if exe is None:
            raise BeeError(
                f"Bee CLI '{self._bin}' not found on PATH. Install @beeai/cli and run `bee login`."
            )
        try:
            proc = subprocess.run(
                [exe, *args, "--json"],
                capture_output=True,
                text=True,
                timeout=self._timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            raise BeeError(f"Bee CLI timed out after {self._timeout}s: bee {' '.join(args)}") from e

        if proc.returncode != 0:
            stderr = (proc.stderr or "").strip()
            if "not logged in" in (stderr + proc.stdout).lower():
                raise BeeError("Bee CLI is not authenticated. Run `bee login`.")
            raise BeeError(f"Bee CLI failed (exit {proc.returncode}): {stderr or proc.stdout[:200]}")

        out = (proc.stdout or "").strip()
        if not out:
            raise BeeError(f"Bee CLI returned empty output for: bee {' '.join(args)}")
        try:
            return json.loads(out)
        except json.JSONDecodeError as e:
            raise BeeError(f"Bee CLI returned non-JSON output for: bee {' '.join(args)}") from e

    def today_context(self) -> BeeTodayContext:
        return BeeTodayContext.model_validate(self._run(["today", "--context"]))

    def current_location(self) -> BeeCurrentLocation:
        return BeeCurrentLocation.model_validate(self._run(["locations", "current"]))

    def search(self, query: str, limit: int = 5) -> BeeSearchResult:
        return BeeSearchResult.model_validate(
            self._run(["search", "--query", query, "--limit", str(limit)])
        )


# -------------------------------------------------------------------------- Mock

class MockBeeClient:
    """Fixture-backed backend for tests/offline dev ONLY. Never the demo path."""

    def __init__(self, fixtures_dir: str | None = None) -> None:
        here = os.path.dirname(__file__)
        self._dir = fixtures_dir or os.path.join(here, "fixtures")

    def _load(self, name: str) -> dict:
        with open(os.path.join(self._dir, name), encoding="utf-8") as fh:
            return json.load(fh)

    def today_context(self) -> BeeTodayContext:
        return BeeTodayContext.model_validate(self._load("today_context.json"))

    def current_location(self) -> BeeCurrentLocation:
        return BeeCurrentLocation.model_validate(self._load("current_location.json"))

    def search(self, query: str, limit: int = 5) -> BeeSearchResult:
        return BeeSearchResult.model_validate(self._load("search.json"))


# ----------------------------------------------------------------------- factory

def get_bee_client(mode: str | None = None) -> BeeClient:
    mode = (mode or os.getenv("AMBIENT_GUARD_BEE_MODE") or "mock").lower()
    if mode == "cli":
        return CliBeeClient()
    if mode == "mock":
        return MockBeeClient()
    if mode == "mcp":
        raise BeeError("Bee MCP backend not yet implemented (tracked as M1.3). Use cli or mock.")
    raise BeeError(f"Unknown AMBIENT_GUARD_BEE_MODE={mode!r}. Expected cli | mcp | mock.")
