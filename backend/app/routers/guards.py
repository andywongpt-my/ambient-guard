"""G7 Guard Mode — API endpoints for guard management.

Provides REST endpoints for:
- Listing and viewing guards
- Manual guard creation
- Alert acknowledgment
- Guard cancellation
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.guards import (
    Guard,
    GuardStatus,
    GuardLifecycle,
    GuardLifecycleError,
    get_guard_store,
    start_guard_scheduler,
    get_guard_scheduler,
)


router = APIRouter(prefix="/api/v1/guards", tags=["guards"])


class CreateGuardRequest(BaseModel):
    """Manual guard creation request."""
    activity: str
    planned_time: str  # ISO format
    lat: float | None = None
    lon: float | None = None
    location_name: str | None = None


class GuardResponse(BaseModel):
    """Guard API response."""
    guard_id: str
    activity: str
    planned_time: str
    status: str
    location: dict[str, Any] | None
    created_at: str
    expires_at: str
    last_assessed_at: str | None
    next_assessment_at: str | None
    assessment_count: int


class GuardDetailResponse(BaseModel):
    """Detailed guard response with assessment history."""
    guard: GuardResponse
    latest_assessment: dict[str, Any] | None
    assessment_history: list[dict[str, Any]]
    alerts: list[dict[str, Any]]


class AlertResponse(BaseModel):
    """Alert API response."""
    alert_id: str
    guard_id: str
    previous_state: str
    new_state: str
    change_type: str
    reason_codes: list[str]
    evidence: dict[str, Any]
    acknowledged: bool
    created_at: str


@router.get("", response_model=list[GuardResponse])
async def list_guards(
    status: GuardStatus | None = Query(default=None, description="Filter by status"),
) -> list[GuardResponse]:
    """List all active guards, optionally filtered by status."""
    store = await get_guard_store()
    guards = await store.list_guards(status=status, include_expired=False)
    
    return [
        GuardResponse(
            guard_id=g.guard_id,
            activity=g.activity,
            planned_time=g.planned_time.isoformat(),
            status=g.status.value,
            location={
                "lat": g.location_lat,
                "lon": g.location_lon,
                "name": g.location_name,
            } if g.location_lat is not None else None,
            created_at=g.created_at.isoformat() if g.created_at else "",
            expires_at=g.expires_at.isoformat() if g.expires_at else "",
            last_assessed_at=g.last_assessed_at.isoformat() if g.last_assessed_at else None,
            next_assessment_at=g.next_assessment_at.isoformat() if g.next_assessment_at else None,
            assessment_count=g.assessment_count,
        )
        for g in guards
    ]


@router.get("/{guard_id}", response_model=GuardDetailResponse)
async def get_guard(guard_id: str) -> GuardDetailResponse:
    """Get detailed guard information with assessment history."""
    store = await get_guard_store()
    
    guard = await store.get_guard(guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail=f"Guard not found: {guard_id}")
    
    # Get assessments
    assessments = await store.list_assessments(guard_id)
    latest = assessments[-1] if assessments else None
    
    # Get alerts
    alerts = await store.list_alerts(guard_id=guard_id)
    
    return GuardDetailResponse(
        guard=GuardResponse(
            guard_id=guard.guard_id,
            activity=guard.activity,
            planned_time=guard.planned_time.isoformat(),
            status=guard.status.value,
            location={
                "lat": guard.location_lat,
                "lon": guard.location_lon,
                "name": guard.location_name,
            } if guard.location_lat is not None else None,
            created_at=guard.created_at.isoformat() if guard.created_at else "",
            expires_at=guard.expires_at.isoformat() if guard.expires_at else "",
            last_assessed_at=guard.last_assessed_at.isoformat() if guard.last_assessed_at else None,
            next_assessment_at=guard.next_assessment_at.isoformat() if guard.next_assessment_at else None,
            assessment_count=guard.assessment_count,
        ),
        latest_assessment=latest.to_dict() if latest else None,
        assessment_history=[a.to_dict() for a in assessments],
        alerts=[a.to_dict() for a in alerts],
    )


@router.post("", response_model=GuardResponse)
async def create_guard(req: CreateGuardRequest) -> GuardResponse:
    """Create a new guard manually.
    
    Note: Automatic guard creation from Bee context is handled by the scheduler.
    Use this endpoint for testing or manual override.
    """
    store = await get_guard_store()
    lifecycle = GuardLifecycle(store=store)
    
    # Parse planned time
    try:
        planned_time = datetime.fromisoformat(req.planned_time)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid planned_time format. Use ISO format.")
    
    # Create guard
    guard = Guard.create(
        activity=req.activity,
        planned_time=planned_time,
        location_lat=req.lat,
        location_lon=req.lon,
        location_name=req.location_name,
        bee_source_type="manual",
        bee_source_reference=f"manual:{req.activity}:{req.planned_time}",
    )
    
    # Check if guard-worthy
    if not guard.is_guard_worthy():
        raise HTTPException(
            status_code=422,
            detail=f"Activity '{req.activity}' is not guard-worthy. Supported: outdoor activities like jogging, cycling, hiking."
        )
    
    # Check if already expired
    if guard.is_expired():
        raise HTTPException(status_code=422, detail="Planned time is in the past.")
    
    # Store guard
    await store.create_guard(guard)
    
    # Run baseline assessment
    await lifecycle.assess_guard(guard)
    
    # Re-fetch updated guard
    guard = await store.get_guard(guard.guard_id)
    
    return GuardResponse(
        guard_id=guard.guard_id,
        activity=guard.activity,
        planned_time=guard.planned_time.isoformat(),
        status=guard.status.value,
        location={
            "lat": guard.location_lat,
            "lon": guard.location_lon,
            "name": guard.location_name,
        } if guard.location_lat is not None else None,
        created_at=guard.created_at.isoformat() if guard.created_at else "",
        expires_at=guard.expires_at.isoformat() if guard.expires_at else "",
        last_assessed_at=guard.last_assessed_at.isoformat() if guard.last_assessed_at else None,
        next_assessment_at=guard.next_assessment_at.isoformat() if guard.next_assessment_at else None,
        assessment_count=guard.assessment_count,
    )


@router.post("/discover")
async def discover_guards() -> dict[str, Any]:
    """Trigger manual guard discovery from Bee context.
    
    Scans Bee today context for guard-worthy activities and creates guards.
    """
    lifecycle = GuardLifecycle()
    
    try:
        guards = await lifecycle.discover_guards_from_bee()
        return {
            "guards_created": len(guards),
            "guards": [g.to_dict() for g in guards],
        }
    except GuardLifecycleError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{guard_id}/assess")
async def assess_guard(guard_id: str) -> dict[str, Any]:
    """Run a baseline or follow-up assessment for a guard.
    
    Transitions DISCOVERED guards to ACTIVE after baseline assessment.
    """
    store = await get_guard_store()
    lifecycle = GuardLifecycle(store=store)
    
    guard = await store.get_guard(guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail=f"Guard not found: {guard_id}")
    
    try:
        assessment = await lifecycle.assess_guard(guard)
        
        # Refresh guard to get updated status
        guard = await store.get_guard(guard_id)
        
        return {
            "guard_id": guard_id,
            "assessment_number": assessment.assessment_number,
            "decision_state": assessment.decision_state,
            "severity": assessment.severity,
            "reason_codes": assessment.reason_codes,
            "guard_status": guard.status.value if guard else None,
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{guard_id}/acknowledge")
async def acknowledge_guard_alert(guard_id: str) -> dict[str, Any]:
    """Acknowledge the latest alert for a guard."""
    store = await get_guard_store()
    lifecycle = GuardLifecycle(store=store)
    
    guard = await store.get_guard(guard_id)
    if not guard:
        raise HTTPException(status_code=404, detail=f"Guard not found: {guard_id}")
    
    # Get latest unacknowledged alert
    alerts = await store.list_alerts(guard_id=guard_id, unacknowledged_only=True)
    if not alerts:
        return {"acknowledged": False, "message": "No unacknowledged alerts for this guard."}
    
    latest_alert = alerts[0]
    success = await lifecycle.acknowledge_alert(latest_alert.alert_id)
    
    return {
        "acknowledged": success,
        "alert_id": latest_alert.alert_id,
    }


@router.delete("/{guard_id}")
async def cancel_guard(guard_id: str) -> dict[str, Any]:
    """Cancel a guard."""
    store = await get_guard_store()
    lifecycle = GuardLifecycle(store=store)
    
    success = await lifecycle.cancel_guard(guard_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Guard not found: {guard_id}")
    
    return {"cancelled": True, "guard_id": guard_id}


@router.get("/alerts/unacknowledged")
async def list_unacknowledged_alerts() -> list[AlertResponse]:
    """List all unacknowledged alerts across all guards."""
    store = await get_guard_store()
    alerts = await store.list_alerts(unacknowledged_only=True)
    
    return [
        AlertResponse(
            alert_id=a.alert_id,
            guard_id=a.guard_id,
            previous_state=a.previous_state,
            new_state=a.new_state,
            change_type=a.change_type.value,
            reason_codes=a.reason_codes,
            evidence=a.evidence,
            acknowledged=a.acknowledged,
            created_at=a.created_at.isoformat() if a.created_at else "",
        )
        for a in alerts
    ]


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str) -> dict[str, Any]:
    """Acknowledge a specific alert."""
    store = await get_guard_store()
    lifecycle = GuardLifecycle(store=store)
    
    success = await lifecycle.acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Alert not found or already acknowledged: {alert_id}")
    
    return {"acknowledged": True, "alert_id": alert_id}


@router.get("/scheduler/status")
async def scheduler_status() -> dict[str, Any]:
    """Get guard scheduler status."""
    scheduler = get_guard_scheduler()
    if not scheduler:
        return {"running": False, "message": "Scheduler not initialized"}
    
    return scheduler.get_status()


@router.post("/scheduler/start")
async def start_scheduler() -> dict[str, Any]:
    """Start the guard scheduler.
    
    This is normally called during app startup, but can be triggered manually.
    """
    await start_guard_scheduler()
    scheduler = get_guard_scheduler()
    return scheduler.get_status() if scheduler else {"running": False}


@router.post("/reassess")
async def reassess_guards() -> dict[str, Any]:
    """Manually trigger guard reassessment.
    
    Reassesses all active guards and detects material changes.
    """
    lifecycle = GuardLifecycle()
    
    try:
        stats = await lifecycle.reassess_active_guards()
        return stats
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/maintenance/run")
async def run_maintenance() -> dict[str, Any]:
    """Manually trigger maintenance tasks.
    
    - Expire guards whose planned time has passed
    - Clean up old data beyond retention period
    """
    store = await get_guard_store()
    lifecycle = GuardLifecycle(store=store)
    
    stats = await lifecycle.run_maintenance()
    return stats
