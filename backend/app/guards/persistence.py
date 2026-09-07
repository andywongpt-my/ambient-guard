"""G7 Guard Mode — Database persistence layer.

PostgreSQL-based storage for guards, assessments, and alerts.
Uses asyncpg for async operations with connection pooling.

Privacy considerations:
- Only normalized data is stored
- Bee source references are hashed, not stored as raw text
- Automatic retention cleanup after GUARD_RETENTION_DAYS
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any

import asyncpg

from app.guards.models import (
    Guard,
    GuardStatus,
    GuardAssessment,
    GuardAlert,
    AlertChangeType,
    GUARD_RETENTION_DAYS,
)


class GuardStore:
    """PostgreSQL-backed guard persistence."""
    
    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or os.getenv(
            "AMBIENT_GUARD_DATABASE_URL",
            "postgresql://ambientguard:ambientguard@localhost:5432/ambientguard"
        )
        self._pool: asyncpg.Pool | None = None
    
    async def connect(self) -> None:
        """Initialize connection pool and create tables."""
        if self._pool is not None:
            return
        
        self._pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10,
        )
        
        await self._create_tables()
    
    async def disconnect(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    async def _create_tables(self) -> None:
        """Create database schema if not exists."""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS guards (
                    id SERIAL PRIMARY KEY,
                    guard_id VARCHAR(36) UNIQUE NOT NULL,
                    activity VARCHAR(100) NOT NULL,
                    planned_time TIMESTAMPTZ NOT NULL,
                    location_lat DOUBLE PRECISION,
                    location_lon DOUBLE PRECISION,
                    location_name VARCHAR(200),
                    bee_source_type VARCHAR(50),
                    bee_source_reference_hash VARCHAR(64),
                    status VARCHAR(30) NOT NULL DEFAULT 'discovered',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    expires_at TIMESTAMPTZ NOT NULL,
                    last_assessed_at TIMESTAMPTZ,
                    next_assessment_at TIMESTAMPTZ,
                    assessment_count INTEGER DEFAULT 0,
                    metadata JSONB DEFAULT '{}'::jsonb
                );
                
                CREATE TABLE IF NOT EXISTS guard_assessments (
                    id SERIAL PRIMARY KEY,
                    guard_id VARCHAR(36) NOT NULL REFERENCES guards(guard_id) ON DELETE CASCADE,
                    assessment_number INTEGER NOT NULL,
                    decision_state VARCHAR(50) NOT NULL,
                    severity VARCHAR(20),
                    environmental_summary JSONB NOT NULL,
                    candidate_windows JSONB DEFAULT '[]'::jsonb,
                    reason_codes JSONB DEFAULT '[]'::jsonb,
                    personal_constraints JSONB DEFAULT '[]'::jsonb,
                    personal_feasibility JSONB,
                    assessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    data_quality JSONB DEFAULT '{}'::jsonb,
                    UNIQUE(guard_id, assessment_number)
                );
                
                CREATE TABLE IF NOT EXISTS guard_alerts (
                    id SERIAL PRIMARY KEY,
                    alert_id VARCHAR(36) UNIQUE NOT NULL,
                    guard_id VARCHAR(36) NOT NULL REFERENCES guards(guard_id) ON DELETE CASCADE,
                    previous_state VARCHAR(50) NOT NULL,
                    new_state VARCHAR(50) NOT NULL,
                    change_type VARCHAR(50) NOT NULL,
                    reason_codes JSONB NOT NULL,
                    evidence JSONB NOT NULL,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_guards_status ON guards(status);
                CREATE INDEX IF NOT EXISTS idx_guards_planned_time ON guards(planned_time);
                CREATE INDEX IF NOT EXISTS idx_guards_next_assessment ON guards(next_assessment_at) WHERE status = 'active';
                CREATE INDEX IF NOT EXISTS idx_guard_assessments_guard ON guard_assessments(guard_id);
                CREATE INDEX IF NOT EXISTS idx_guard_alerts_guard ON guard_alerts(guard_id);
            """)
    
    # --- Guard CRUD ---
    
    async def create_guard(self, guard: Guard) -> Guard:
        """Insert a new guard."""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO guards (
                    guard_id, activity, planned_time,
                    location_lat, location_lon, location_name,
                    bee_source_type, bee_source_reference_hash,
                    status, created_at, expires_at,
                    next_assessment_at, assessment_count, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """,
                guard.guard_id,
                guard.activity,
                guard.planned_time,
                guard.location_lat,
                guard.location_lon,
                guard.location_name,
                guard.bee_source_type,
                guard.bee_source_reference_hash,
                guard.status.value,
                guard.created_at,
                guard.expires_at,
                guard.next_assessment_at,
                guard.assessment_count,
                guard.metadata,
            )
        return guard
    
    async def get_guard(self, guard_id: str) -> Guard | None:
        """Fetch a guard by ID."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM guards WHERE guard_id = $1",
                guard_id
            )
            if row is None:
                return None
            return self._row_to_guard(row)
    
    async def list_guards(
        self,
        status: GuardStatus | None = None,
        include_expired: bool = False,
    ) -> list[Guard]:
        """List guards, optionally filtered by status."""
        async with self._pool.acquire() as conn:
            if status:
                rows = await conn.fetch(
                    "SELECT * FROM guards WHERE status = $1 ORDER BY planned_time ASC",
                    status.value
                )
            elif not include_expired:
                rows = await conn.fetch(
                    "SELECT * FROM guards WHERE status NOT IN ('expired', 'cancelled') ORDER BY planned_time ASC"
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM guards ORDER BY planned_time ASC"
                )
            return [self._row_to_guard(row) for row in rows]
    
    async def update_guard(self, guard: Guard) -> None:
        """Update a guard's state."""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                UPDATE guards SET
                    status = $2,
                    last_assessed_at = $3,
                    next_assessment_at = $4,
                    assessment_count = $5,
                    metadata = $6
                WHERE guard_id = $1
            """,
                guard.guard_id,
                guard.status.value,
                guard.last_assessed_at,
                guard.next_assessment_at,
                guard.assessment_count,
                guard.metadata,
            )
    
    async def delete_guard(self, guard_id: str) -> bool:
        """Delete a guard and all related data."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM guards WHERE guard_id = $1",
                guard_id
            )
            return result == "DELETE 1"
    
    async def guard_exists_by_hash(self, bee_source_hash: str) -> bool:
        """Check if a guard already exists for this Bee source (by hash)."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM guards WHERE bee_source_reference_hash = $1 AND status NOT IN ('expired', 'cancelled')",
                bee_source_hash
            )
            return row is not None
    
    # --- Assessment CRUD ---
    
    async def create_assessment(self, assessment: GuardAssessment) -> GuardAssessment:
        """Store a new assessment snapshot."""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO guard_assessments (
                    guard_id, assessment_number, decision_state, severity,
                    environmental_summary, candidate_windows, reason_codes,
                    personal_constraints, personal_feasibility, assessed_at, data_quality
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
                assessment.guard_id,
                assessment.assessment_number,
                assessment.decision_state,
                assessment.severity,
                assessment.environmental_summary,
                assessment.candidate_windows,
                assessment.reason_codes,
                assessment.personal_constraints,
                assessment.personal_feasibility,
                assessment.assessed_at,
                assessment.data_quality,
            )
        return assessment
    
    async def list_assessments(self, guard_id: str) -> list[GuardAssessment]:
        """Fetch all assessments for a guard, ordered by assessment number."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM guard_assessments WHERE guard_id = $1 ORDER BY assessment_number ASC",
                guard_id
            )
            return [self._row_to_assessment(row) for row in rows]
    
    async def get_latest_assessment(self, guard_id: str) -> GuardAssessment | None:
        """Fetch the most recent assessment for a guard."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM guard_assessments WHERE guard_id = $1 ORDER BY assessment_number DESC LIMIT 1",
                guard_id
            )
            if row is None:
                return None
            return self._row_to_assessment(row)
    
    # --- Alert CRUD ---
    
    async def create_alert(self, alert: GuardAlert) -> GuardAlert:
        """Store a new alert."""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO guard_alerts (
                    alert_id, guard_id, previous_state, new_state,
                    change_type, reason_codes, evidence,
                    acknowledged, acknowledged_at, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
                alert.alert_id,
                alert.guard_id,
                alert.previous_state,
                alert.new_state,
                alert.change_type.value,
                alert.reason_codes,
                alert.evidence,
                alert.acknowledged,
                alert.acknowledged_at,
                alert.created_at,
            )
        return alert
    
    async def list_alerts(
        self,
        guard_id: str | None = None,
        unacknowledged_only: bool = False,
    ) -> list[GuardAlert]:
        """List alerts, optionally filtered by guard or acknowledgment status."""
        async with self._pool.acquire() as conn:
            if guard_id:
                if unacknowledged_only:
                    rows = await conn.fetch(
                        "SELECT * FROM guard_alerts WHERE guard_id = $1 AND acknowledged = FALSE ORDER BY created_at DESC",
                        guard_id
                    )
                else:
                    rows = await conn.fetch(
                        "SELECT * FROM guard_alerts WHERE guard_id = $1 ORDER BY created_at DESC",
                        guard_id
                    )
            else:
                if unacknowledged_only:
                    rows = await conn.fetch(
                        "SELECT * FROM guard_alerts WHERE acknowledged = FALSE ORDER BY created_at DESC"
                    )
                else:
                    rows = await conn.fetch(
                        "SELECT * FROM guard_alerts ORDER BY created_at DESC"
                    )
            return [self._row_to_alert(row) for row in rows]
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark an alert as acknowledged."""
        async with self._pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE guard_alerts
                SET acknowledged = TRUE, acknowledged_at = NOW()
                WHERE alert_id = $1 AND acknowledged = FALSE
            """,
                alert_id
            )
            return result == "UPDATE 1"
    
    # --- Maintenance ---
    
    async def expire_guards(self) -> int:
        """Mark expired guards and return count."""
        async with self._pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE guards
                SET status = 'expired'
                WHERE expires_at < NOW() AND status NOT IN ('expired', 'cancelled')
            """)
            # Parse "UPDATE N" to get count
            count_str = result.split()[-1]
            return int(count_str) if count_str.isdigit() else 0
    
    async def cleanup_old_data(self, days: int = GUARD_RETENTION_DAYS) -> dict[str, int]:
        """Delete expired guards older than retention period."""
        async with self._pool.acquire() as conn:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Delete alerts for old guards
            await conn.execute("""
                DELETE FROM guard_alerts
                WHERE guard_id IN (
                    SELECT guard_id FROM guards
                    WHERE status IN ('expired', 'cancelled') AND expires_at < $1
                )
            """, cutoff)
            
            # Delete assessments for old guards
            await conn.execute("""
                DELETE FROM guard_assessments
                WHERE guard_id IN (
                    SELECT guard_id FROM guards
                    WHERE status IN ('expired', 'cancelled') AND expires_at < $1
                )
            """, cutoff)
            
            # Delete old guards
            result = await conn.execute("""
                DELETE FROM guards
                WHERE status IN ('expired', 'cancelled') AND expires_at < $1
            """, cutoff)
            
            count_str = result.split()[-1]
            deleted_count = int(count_str) if count_str.isdigit() else 0
            
            return {
                "guards_deleted": deleted_count,
                "retention_days": days,
            }
    
    # --- Row mappers ---
    
    def _row_to_guard(self, row: asyncpg.Record) -> Guard:
        """Convert database row to Guard object."""
        return Guard(
            guard_id=row["guard_id"],
            activity=row["activity"],
            planned_time=row["planned_time"],
            status=GuardStatus(row["status"]),
            location_lat=row["location_lat"],
            location_lon=row["location_lon"],
            location_name=row["location_name"],
            bee_source_type=row["bee_source_type"],
            bee_source_reference_hash=row["bee_source_reference_hash"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            last_assessed_at=row["last_assessed_at"],
            next_assessment_at=row["next_assessment_at"],
            assessment_count=row["assessment_count"],
            metadata=row["metadata"] or {},
        )
    
    def _row_to_assessment(self, row: asyncpg.Record) -> GuardAssessment:
        """Convert database row to GuardAssessment object."""
        return GuardAssessment(
            guard_id=row["guard_id"],
            assessment_number=row["assessment_number"],
            decision_state=row["decision_state"],
            severity=row["severity"],
            environmental_summary=row["environmental_summary"] or {},
            candidate_windows=row["candidate_windows"] or [],
            reason_codes=row["reason_codes"] or [],
            personal_constraints=row["personal_constraints"] or [],
            personal_feasibility=row["personal_feasibility"],
            assessed_at=row["assessed_at"],
            data_quality=row["data_quality"] or {},
        )
    
    def _row_to_alert(self, row: asyncpg.Record) -> GuardAlert:
        """Convert database row to GuardAlert object."""
        return GuardAlert(
            alert_id=row["alert_id"],
            guard_id=row["guard_id"],
            previous_state=row["previous_state"],
            new_state=row["new_state"],
            change_type=AlertChangeType(row["change_type"]),
            reason_codes=row["reason_codes"] or [],
            evidence=row["evidence"] or {},
            acknowledged=row["acknowledged"],
            acknowledged_at=row["acknowledged_at"],
            created_at=row["created_at"],
        )


# Global store instance (initialized on first use)
_store: GuardStore | None = None


async def get_guard_store() -> GuardStore:
    """Get or create the global guard store."""
    global _store
    if _store is None:
        _store = GuardStore()
        await _store.connect()
    return _store
