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


# --------------------------------------------------------------------------- MCP

class McpBeeClient:
    """MCP backend: JSON-RPC 2.0 over HTTP to `bee mcp serve-http` (127.0.0.1:8790).

    The CLI doubles as an MCP server; each capability is a tool (bee_get_today,
    bee_get_current_location, bee_search). We call `tools/call` and unwrap the
    tool's structured result. Auth is a bearer token (>=32 chars).
    """

    def __init__(self, url: str | None = None, token: str | None = None,
                 timeout: float = 20.0) -> None:
        import httpx  # local import so cli/mock paths don't require httpx at import time
        self._httpx = httpx
        self._url = url or os.getenv("AMBIENT_GUARD_BEE_MCP_URL") or "http://127.0.0.1:8790/mcp"
        self._token = token or os.getenv("AMBIENT_GUARD_BEE_HTTP_TOKEN") or ""
        # The Bee MCP server rejects non-localhost Host/Origin headers. When reached
        # through a host forwarder (container -> host gateway), send a loopback Host so
        # the guard passes. Override via AMBIENT_GUARD_BEE_MCP_HOST if the server moves.
        self._host = os.getenv("AMBIENT_GUARD_BEE_MCP_HOST") or "127.0.0.1"
        self._timeout = timeout
        self._id = 0

    def _call_tool(self, name: str, arguments: dict) -> dict:
        if not self._token:
            raise BeeError("AMBIENT_GUARD_BEE_HTTP_TOKEN is required for the mcp backend.")
        self._id += 1
        payload = {"jsonrpc": "2.0", "id": self._id,
                   "method": "tools/call", "params": {"name": name, "arguments": arguments}}
        headers = {"Authorization": f"Bearer {self._token}",
                   "Content-Type": "application/json",
                   "Host": self._host,
                   "Origin": f"http://{self._host}"}
        try:
            r = self._httpx.post(self._url, json=payload, headers=headers, timeout=self._timeout)
            r.raise_for_status()
            body = r.json()
        except self._httpx.HTTPError as e:
            raise BeeError(f"Bee MCP request failed: {e}") from e
        except ValueError as e:
            raise BeeError(f"Bee MCP returned non-JSON: {e}") from e

        if "error" in body:
            raise BeeError(f"Bee MCP tool error: {body['error']}")
        result = body.get("result", {})
        # MCP tool results carry structuredContent, or JSON text in content[].text
        if isinstance(result, dict):
            if result.get("isError"):
                msg = ""
                for item in result.get("content") or []:
                    if item.get("type") == "text":
                        msg = item.get("text", ""); break
                raise BeeError(f"Bee MCP tool {name} returned an error: {msg or result}")
            if "structuredContent" in result and result["structuredContent"] is not None:
                return result["structuredContent"]
            content = result.get("content")
            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "text":
                        try:
                            return json.loads(item["text"])
                        except (json.JSONDecodeError, KeyError):
                            continue
        raise BeeError(f"Bee MCP result had no parseable content for tool {name}")

    def today_context(self) -> BeeTodayContext:
        # bee_get_today MCP tool takes NO arguments (the CLI's --context flag has no
        # MCP equivalent; passing {context:true} is rejected as an unknown property).
        return BeeTodayContext.model_validate(self._call_tool("bee_get_today", {}))

    def current_location(self) -> BeeCurrentLocation:
        return BeeCurrentLocation.model_validate(self._call_tool("bee_get_current_location", {}))

    def search(self, query: str, limit: int = 5) -> BeeSearchResult:
        return BeeSearchResult.model_validate(
            self._call_tool("bee_search", {"query": query, "limit": limit}))


# ----------------------------------------------------------------------- factory

def get_bee_client(mode: str | None = None) -> BeeClient:
    mode = (mode or os.getenv("AMBIENT_GUARD_BEE_MODE") or "mock").lower()
    if mode == "cli":
        return CliBeeClient()
    if mode == "mock":
        return MockBeeClient()
    if mode == "mcp":
        return McpBeeClient()
    raise BeeError(f"Unknown AMBIENT_GUARD_BEE_MODE={mode!r}. Expected cli | mcp | mock.")
