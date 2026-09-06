"""Pydantic models mirroring the real `bee ... --json` payload shapes.

Shapes captured live from @beeai/cli 0.7.3 (see evidence/M1_bee_login.md):

  bee today --context --json  -> BeeTodayContext
  bee locations current --json -> BeeCurrentLocation
  bee search --query <q> --json -> BeeSearchResult

Models are permissive (extra="ignore", most fields optional) so a schema tweak on
Bee's side degrades gracefully instead of hard-failing the whole request (R8).
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class _Base(BaseModel):
    model_config = ConfigDict(extra="ignore")


class BeeConversation(_Base):
    id: int | None = None
    start_time: int | None = None          # epoch ms
    end_time: int | None = None
    device_type: str | None = None
    summary: str | None = None
    short_summary: str | None = None
    state: str | None = None
    created_at: int | None = None
    updated_at: int | None = None
    utterances_count: int | None = None
    primary_location: dict | None = None


class BeeTodayBrief(_Base):
    calendar_events: list[dict] = []
    emails: list[dict] = []
    timezone: str | None = None


class BeeTodayContext(_Base):
    date: str | None = None
    todayBrief: BeeTodayBrief | None = None
    dailySummary: str | dict | None = None
    activeTodos: list[dict] = []
    recentNotes: list[dict] = []
    recentConversations: list[BeeConversation] = []


class BeeLocation(_Base):
    id: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    address: str | None = None
    source_device_id: str | None = None
    created_at: int | None = None          # epoch ms
    updated_at: int | None = None


class BeeCurrentLocation(_Base):
    location: BeeLocation | None = None
    age_ms: int | None = None
    is_recent: bool | None = None
    recent_threshold_ms: int | None = None
    timezone: str | None = None


class BeeSearchResult(_Base):
    results: list[dict] = []
    next_cursor: str | None = None
    search_mode: str | None = None
    timezone: str | None = None
