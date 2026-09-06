"""Bee integration layer — turns real Bee CLI/MCP output into raw context the
normalization layer consumes. Backend selected by AMBIENT_GUARD_BEE_MODE."""
from app.bee.client import BeeClient, BeeError, get_bee_client

__all__ = ["BeeClient", "BeeError", "get_bee_client"]
