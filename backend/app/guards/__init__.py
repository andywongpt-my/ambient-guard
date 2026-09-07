"""G7 Guard Mode — Proactive environmental monitoring.

This package implements the Guard Mode feature that transforms Ambient Guard
from a request-response assistant into a proactive, quiet, evidence-driven agent.

Key components:
- models: Guard, GuardAssessment, GuardAlert data models
- persistence: PostgreSQL storage layer
- lifecycle: Guard creation, assessment, and state management
- scheduler: Background reassessment loop
"""
from app.guards.models import (
    Guard,
    GuardStatus,
    GuardAssessment,
    GuardAlert,
    AlertChangeType,
    GUARD_WORTHY_ACTIVITIES,
    MIN_GUARD_CONFIDENCE,
)
from app.guards.persistence import (
    GuardStore,
    get_guard_store,
)
from app.guards.lifecycle import (
    GuardLifecycle,
    GuardLifecycleError,
)
from app.guards.scheduler import (
    GuardScheduler,
    start_guard_scheduler,
    stop_guard_scheduler,
    get_guard_scheduler,
)


__all__ = [
    # Models
    "Guard",
    "GuardStatus",
    "GuardAssessment",
    "GuardAlert",
    "AlertChangeType",
    "GUARD_WORTHY_ACTIVITIES",
    "MIN_GUARD_CONFIDENCE",
    # Persistence
    "GuardStore",
    "get_guard_store",
    # Lifecycle
    "GuardLifecycle",
    "GuardLifecycleError",
    # Scheduler
    "GuardScheduler",
    "start_guard_scheduler",
    "stop_guard_scheduler",
    "get_guard_scheduler",
]
