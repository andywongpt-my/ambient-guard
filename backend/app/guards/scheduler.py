"""G7 Guard Mode — Background scheduler for guard reassessment.

Uses APScheduler for in-process periodic task execution:
- Discover new guards from Bee context (every 30 minutes)
- Reassess active guards (every 45 minutes)
- Run maintenance tasks (hourly)

Lightweight design suitable for the current dedicated-server architecture.
No external dependencies beyond APScheduler.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.guards.lifecycle import GuardLifecycle, GuardLifecycleError


logger = logging.getLogger(__name__)


class GuardScheduler:
    """Background scheduler for guard monitoring tasks."""
    
    def __init__(self, lifecycle: GuardLifecycle | None = None):
        self.lifecycle = lifecycle or GuardLifecycle()
        self._scheduler: AsyncIOScheduler | None = None
        self._running = False
    
    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            logger.warning("GuardScheduler already running")
            return
        
        self._scheduler = AsyncIOScheduler()
        
        # Schedule guard discovery (every 30 minutes)
        self._scheduler.add_job(
            self._discover_guards,
            trigger=IntervalTrigger(minutes=30),
            id="guard_discovery",
            name="Discover new guards from Bee context",
            max_instances=1,
            replace_existing=True,
        )
        
        # Schedule guard reassessment (every 45 minutes)
        self._scheduler.add_job(
            self._reassess_guards,
            trigger=IntervalTrigger(minutes=45),
            id="guard_reassessment",
            name="Reassess active guards",
            max_instances=1,
            replace_existing=True,
        )
        
        # Schedule maintenance (hourly)
        self._scheduler.add_job(
            self._run_maintenance,
            trigger=IntervalTrigger(hours=1),
            id="guard_maintenance",
            name="Expire and clean up guards",
            max_instances=1,
            replace_existing=True,
        )
        
        self._scheduler.start()
        self._running = True
        
        logger.info(
            "GuardScheduler started",
            extra={
                "jobs": [
                    {"id": j.id, "next_run": str(j.next_run_time)}
                    for j in self._scheduler.get_jobs()
                ]
            }
        )
    
    async def stop(self) -> None:
        """Stop the scheduler."""
        if self._scheduler and self._running:
            self._scheduler.shutdown(wait=False)
            self._running = False
            logger.info("GuardScheduler stopped")
    
    async def _discover_guards(self) -> None:
        """Discover new guards from Bee context."""
        logger.info("Guard discovery job started")
        
        try:
            guards = await self.lifecycle.discover_guards_from_bee()
            logger.info(
                "Guard discovery completed",
                extra={"guards_created": len(guards)}
            )
        except GuardLifecycleError as e:
            logger.error(f"Guard discovery failed: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error in guard discovery: {e}")
    
    async def _reassess_guards(self) -> None:
        """Reassess active guards."""
        logger.info("Guard reassessment job started")
        
        try:
            stats = await self.lifecycle.reassess_active_guards()
            logger.info(
                "Guard reassessment completed",
                extra=stats
            )
        except Exception as e:
            logger.exception(f"Unexpected error in guard reassessment: {e}")
    
    async def _run_maintenance(self) -> None:
        """Run maintenance tasks."""
        logger.info("Guard maintenance job started")
        
        try:
            stats = await self.lifecycle.run_maintenance()
            logger.info(
                "Guard maintenance completed",
                extra=stats
            )
        except Exception as e:
            logger.exception(f"Unexpected error in guard maintenance: {e}")
    
    def get_status(self) -> dict:
        """Get scheduler status."""
        if not self._running or not self._scheduler:
            return {
                "running": False,
                "jobs": [],
            }
        
        return {
            "running": True,
            "jobs": [
                {
                    "id": j.id,
                    "name": j.name,
                    "next_run": j.next_run_time.isoformat() if j.next_run_time else None,
                }
                for j in self._scheduler.get_jobs()
            ],
        }


# Global scheduler instance
_scheduler: GuardScheduler | None = None


async def start_guard_scheduler() -> GuardScheduler:
    """Start the global guard scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = GuardScheduler()
        await _scheduler.start()
    return _scheduler


async def stop_guard_scheduler() -> None:
    """Stop the global guard scheduler."""
    global _scheduler
    if _scheduler:
        await _scheduler.stop()
        _scheduler = None


def get_guard_scheduler() -> GuardScheduler | None:
    """Get the global guard scheduler."""
    return _scheduler
