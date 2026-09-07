"""Context normalization — raw Bee context -> structured ContextIntent.

Rule-based and deterministic (no LLM in this layer): keyword activity match + time
expression parsing + location resolution. Every populated field is traceable via
`notes` and `source_ref`; undetermined fields stay None and lower `confidence`
rather than being guessed (FR-2.3).

Time is resolved relative to a supplied `now` so the layer is testable and does not
depend on wall-clock. "5 PM" resolves to 17:00 on `now`'s date (or the next day if
that time has already passed today).
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timedelta

from app.agent.models import ContextIntent, SourceRef
from app.bee.models import BeeCurrentLocation, BeeSearchResult, BeeTodayContext

# Activity keyword -> canonical activity. Order matters (first match wins).
_ACTIVITY_KEYWORDS: list[tuple[str, str]] = [
    (r"\bjog(ging|ged)?\b", "jogging"),
    (r"\brun(ning)?\b", "running"),
    (r"\bwalk(ing|ed)?\b", "walking"),
    (r"\bcycl(e|ing)\b|\bbike\b|\bbiking\b", "cycling"),
    (r"\bhik(e|ing)\b", "hiking"),
    (r"\bswim(ming)?\b", "swimming"),
    (r"\bworkout\b|\bexercise\b|\btrain(ing)?\b", "exercise"),
    (r"\bcommut(e|ing)\b", "commute"),
    (r"\bpicnic\b", "picnic"),
    (r"\bgarden(ing)?\b", "gardening"),
]

_OUTDOOR = {"jogging", "running", "walking", "cycling", "hiking", "swimming",
            "commute", "picnic", "gardening"}

# "5 PM", "5pm", "5:30 pm", "17:00", "17.00"
_TIME_12H = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*([ap])\.?m\.?\b", re.IGNORECASE)
_TIME_24H = re.compile(r"\b([01]?\d|2[0-3])[:.]([0-5]\d)\b")
_REL_HOURS = re.compile(r"\bin\s+(an?|\d+)\s+hours?\b", re.IGNORECASE)


def _extract_activity(text: str) -> tuple[str | None, bool]:
    low = text.lower()
    for pattern, activity in _ACTIVITY_KEYWORDS:
        if re.search(pattern, low):
            return activity, activity in _OUTDOOR
    return None, False


def _extract_time(text: str, now: datetime) -> datetime | None:
    m = _TIME_12H.search(text)
    if m:
        hour = int(m.group(1)) % 12
        minute = int(m.group(2) or 0)
        if m.group(3).lower() == "p":
            hour += 12
        cand = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return cand if cand >= now else cand + timedelta(days=1)

    m = _TIME_24H.search(text)
    if m:
        cand = now.replace(hour=int(m.group(1)), minute=int(m.group(2)),
                           second=0, microsecond=0)
        return cand if cand >= now else cand + timedelta(days=1)

    m = _REL_HOURS.search(text)
    if m:
        raw = m.group(1).lower()
        hours = 1 if raw in ("a", "an") else int(raw)
        return now + timedelta(hours=hours)

    return None


def _best_intent_text(
    today: BeeTodayContext | None, search: BeeSearchResult | None
) -> tuple[str | None, str | None]:
    """Pick the most intent-bearing phrase + its Bee ref id. Search hits first."""
    if search and search.results:
        top = search.results[0]
        txt = top.get("short_summary") or top.get("summary") or top.get("text")
        if txt:
            return txt, str(top.get("id")) if top.get("id") is not None else None
    if today and today.recentConversations:
        for conv in today.recentConversations:
            txt = conv.summary or conv.short_summary
            if txt:
                return txt, str(conv.id) if conv.id is not None else None
    return None, None


def normalize(
    today: BeeTodayContext | None,
    location: BeeCurrentLocation | None,
    search: BeeSearchResult | None = None,
    *,
    now: datetime | None = None,
    default_location: str | None = None,
) -> ContextIntent:
    now = now or datetime.now()
    default_location = default_location if default_location is not None \
        else os.getenv("AMBIENT_GUARD_DEFAULT_LOCATION")

    intent_text, ref_id = _best_intent_text(today, search)
    notes: list[str] = []
    confidence = 0.0

    if intent_text is None:
        intent_text = ""
        notes.append("no intent-bearing Bee context found")
    else:
        confidence += 0.4
        notes.append(f"intent text from Bee ref {ref_id or 'unknown'}")

    activity, is_outdoor = _extract_activity(intent_text)
    if activity:
        confidence += 0.3
        notes.append(f"activity '{activity}' matched (outdoor={is_outdoor})")
    else:
        notes.append("activity not determined")

    planned_time = _extract_time(intent_text, now)
    if planned_time:
        confidence += 0.2
        notes.append(f"planned_time parsed -> {planned_time.isoformat()}")
    else:
        notes.append("planned_time not determined")

    # Location resolution (R3): prefer a recent Bee location; else fall back.
    loc_name = lat = lon = None
    is_recent = None

    def _parse_coords(s: str | None) -> tuple[float | None, float | None]:
        # Accept "lat,lon" for AMBIENT_GUARD_DEFAULT_LOCATION; else no coords.
        if not s:
            return None, None
        parts = s.split(",")
        if len(parts) == 2:
            try:
                return float(parts[0].strip()), float(parts[1].strip())
            except ValueError:
                return None, None
        return None, None

    if location and location.location and location.location.latitude is not None:
        is_recent = location.is_recent
        if location.is_recent:
            loc_name = location.location.address
            lat, lon = location.location.latitude, location.location.longitude
            confidence += 0.1
            notes.append("location from Bee (recent)")
        else:
            notes.append(
                f"Bee location stale (age_ms={location.age_ms}); "
                + ("using AMBIENT_GUARD_DEFAULT_LOCATION" if default_location
                   else "no fallback configured")
            )
            if default_location:
                loc_name = default_location
                # prefer coords parsed from the fallback; else keep stale Bee coords as a hint
                flat, flon = _parse_coords(default_location)
                lat = flat if flat is not None else location.location.latitude
                lon = flon if flon is not None else location.location.longitude
    elif default_location:
        loc_name = default_location
        lat, lon = _parse_coords(default_location)
        notes.append("no Bee location; using AMBIENT_GUARD_DEFAULT_LOCATION")
    else:
        notes.append("location not determined")

    observed_at = None
    if location and location.location and location.location.updated_at:
        observed_at = datetime.fromtimestamp(location.location.updated_at / 1000)

    return ContextIntent(
        activity=activity,
        planned_time=planned_time,
        location=loc_name,
        latitude=lat,
        longitude=lon,
        location_is_recent=is_recent,
        intent_text=intent_text,
        source_ref=SourceRef(
            provider="bee", ref_id=ref_id, observed_at=observed_at, location=loc_name
        ),
        confidence=round(min(confidence, 1.0), 2),
        notes=notes,
    )
