"""Bee MCP backend (M1.3) tests — JSON-RPC mocked with respx (no live server)."""
from __future__ import annotations

import httpx
import pytest
import respx

from app.bee.client import McpBeeClient
from app.bee import BeeError

URL = "http://127.0.0.1:8790/mcp"
TOKEN = "x" * 40


def _rpc_structured(obj):
    return {"jsonrpc": "2.0", "id": 1, "result": {"structuredContent": obj}}


def _rpc_text(obj):
    import json
    return {"jsonrpc": "2.0", "id": 1,
            "result": {"content": [{"type": "text", "text": json.dumps(obj)}]}}


@respx.mock
def test_current_location_structured():
    loc = {"location": {"latitude": 6.18, "longitude": 116.22, "address": "Tuaran"},
           "age_ms": 1000, "is_recent": True, "recent_threshold_ms": 1800000}
    respx.post(URL).mock(return_value=httpx.Response(200, json=_rpc_structured(loc)))
    c = McpBeeClient(url=URL, token=TOKEN)
    out = c.current_location()
    assert out.is_recent is True
    assert out.location.latitude == pytest.approx(6.18)


@respx.mock
def test_search_text_envelope():
    res = {"results": [{"id": 7, "short_summary": "jog at 5 PM"}], "search_mode": "bm25"}
    respx.post(URL).mock(return_value=httpx.Response(200, json=_rpc_text(res)))
    c = McpBeeClient(url=URL, token=TOKEN)
    out = c.search("jog")
    assert out.results[0]["short_summary"] == "jog at 5 PM"


@respx.mock
def test_rpc_error_surfaces():
    respx.post(URL).mock(return_value=httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "error": {"code": -32000, "message": "boom"}}))
    with pytest.raises(BeeError, match="tool error"):
        McpBeeClient(url=URL, token=TOKEN).current_location()


def test_missing_token_refuses():
    with pytest.raises(BeeError, match="TOKEN is required"):
        McpBeeClient(url=URL, token="").current_location()
