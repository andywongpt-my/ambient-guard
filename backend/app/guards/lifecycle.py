"""G7 Guard Mode — Guard lifecycle management.

Handles:
- Guard discovery from Bee context
- Baseline and follow-up assessments
- Material change detection
- Alert generation
- Lifecycle state transitions
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.agent.decision_state import DecisionState
from app.agent.models import ContextIntent
from app.agent.normalize import normalize
from app.agent.reasoning import ReasoningEngine, ReasoningError
from app.agent.reasoning_models import Assessment
from app.bee import get_bee_client, BeeError
from app.bee.models import BeeSearchResult
from app.environmental import EnvironmentalService
from app.guards.models import (
    Guard,
    GuardStatus,
    GuardAssessment,
    GuardAlert,
    AlertChangeType,
    GUARD_WORTHY_ACTIVITIES,
    MIN_GUARD_CONFIDENCE,
    DEFAULT_REASSESSMENT_INTERVAL_MINUTES,
    hash_bee_reference,
)
from app.guards.persistence import GuardStore, get_guard_store


class GuardLifecycleError(RuntimeError):
    """Error in guard lifecycle management."""
    pass


class GuardLifecycle:
    """Manages the complete lifecycle of environmental guards."""
    
    def __init__(
        self,
        store: GuardStore | None = None,
        env_service: EnvironmentalService | None = None,
    ):
        self._store = store
        self._env_service = env_service or EnvironmentalService()
        self._reasoning = ReasoningEngine()
    
    async def _get_store(self) -> GuardStore:
        if self._store is None:
            self._store = await get_guard_store()
        return self._store
    
    # --- Guard Discovery ---
    
    async def discover_guards_from_bee(self) -> list[Guard]:
        """Scan Bee context for guard-worthy activities and create guards.
        
        This is the entry point for proactive guard creation.
        """
        store = await self._get_store()
        created_guards = []
        
        try:
            client = get_bee_client()
            today = client.today_context()
            location = client.current_location()
            
            # Search for relevant activities
            search = client.search(
                query=" ".join(GUARD_WORTHY_ACTIVITIES),
                limit=20,
            )
        except BeeError as e:
            raise GuardLifecycleError(f"Failed to retrieve Bee context: {e}") from e
        
        # Normalize Bee context into intents
        intent = normalize(today, location, search)
        
        # Check if this intent qualifies for a guard
        if not self._is_guard_worthy(intent):
            return []
        
        # Check confidence threshold
        if intent.confidence < MIN_GUARD_CONFIDENCE:
            return []
        
        # Check if planned time is in the future
        if intent.planned_time is None or intent.planned_time < datetime.utcnow():
            return []
        
        # Create a source reference hash to prevent duplicates
        source_ref = f"{intent.activity}:{intent.planned_time.isoformat()}:{intent.source_ref}"
        source_hash = hash_bee_reference(source_ref)
        
        # Check for existing guard
        if await store.guard_exists_by_hash(source_hash):
            return []
        
        # Create the guard
        guard = Guard.create(
            activity=intent.activity,
            planned_time=intent.planned_time,
            location_lat=intent.latitude,
            location_lon=intent.longitude,
            location_name=location.display_name if location else None,
            bee_source_type="bee_today_context",
            bee_source_reference=source_ref,
        )
        
        # Store the guard
        await store.create_guard(guard)
        created_guards.append(guard)
        
        return created_guards
    
    def _is_guard_worthy(self, intent: ContextIntent) -> bool:
        """Check if an intent qualifies for guard monitoring."""
        if not intent.activity:
            return False
        
        activity_lower = intent.activity.lower()
        return any(
            worthy in activity_lower or activity_lower in worthy
            for worthy in GUARD_WORTHY_ACTIVITIES
        )
    
    # --- Assessment ---
    
    async def assess_guard(self, guard: Guard) -> GuardAssessment:
        """Run a baseline or follow-up assessment for a guard.
        
        This runs the full G2/G3 reasoning pipeline for the guard's
        activity, time, and location.
        """
        store = await self._get_store()
        
        # Get environmental data
        if guard.location_lat is None or guard.location_lon is None:
            # No location - cannot assess
            assessment = GuardAssessment.create(
                guard_id=guard.guard_id,
                assessment_number=guard.assessment_count + 1,
                decision_state=DecisionState.INSUFFICIENT_ENVIRONMENTAL_DATA.value,
                data_quality={"error": "No location available for guard"},
            )
            await store.create_assessment(assessment)
            return assessment
        
        try:
            observations, provider_errors = self._env_service.observe(
                guard.location_lat,
                guard.location_lon,
                when=guard.planned_time,
            )
        except Exception as e:
            assessment = GuardAssessment.create(
                guard_id=guard.guard_id,
                assessment_number=guard.assessment_count + 1,
                decision_state=DecisionState.INSUFFICIENT_ENVIRONMENTAL_DATA.value,
                data_quality={"error": f"Environmental data fetch failed: {e}"},
            )
            await store.create_assessment(assessment)
            return assessment
        
        # Build ContextIntent for reasoning
        intent = ContextIntent(
            activity=guard.activity,
            planned_time=guard.planned_time,
            latitude=guard.location_lat,
            longitude=guard.location_lon,
            intent_text=f"Guard monitoring for {guard.activity}",
            source_ref=guard.guard_id,
            confidence=1.0,
        )
        
        # Run reasoning (G2/G3)
        try:
            # Get Bee context for personal feasibility (G3)
            bee_today_context = None
            try:
                client = get_bee_client()
                bee_today_context = client.today_context().model_dump()
            except BeeError:
                pass  # Personal context is optional
            
            result = self._reasoning.assess(
                intent,
                observations,
                provider_errors,
                observe_func=self._env_service.observe,
                lat=guard.location_lat,
                lon=guard.location_lon,
                bee_today_context=bee_today_context,
            )
        except ReasoningError as e:
            assessment = GuardAssessment.create(
                guard_id=guard.guard_id,
                assessment_number=guard.assessment_count + 1,
                decision_state=DecisionState.INSUFFICIENT_ENVIRONMENTAL_DATA.value,
                data_quality={"error": f"Reasoning failed: {e}"},
            )
            await store.create_assessment(assessment)
            return assessment
        
        # Build assessment snapshot
        assessment = GuardAssessment.create(
            guard_id=guard.guard_id,
            assessment_number=guard.assessment_count + 1,
            decision_state=result.decision_state,
            severity=self._extract_severity(result.evidence),
            environmental_summary=self._extract_environmental_summary(observations),
            candidate_windows=[
                w.model_dump(mode="json") for w in (result.candidate_windows or [])
            ],
            reason_codes=result.reason_codes,
            personal_constraints=self._extract_personal_constraints(result),
            personal_feasibility=result.personal_feasibility.model_dump(mode="json") if result.personal_feasibility else None,
            data_quality={"provider_errors": provider_errors},
        )
        
        await store.create_assessment(assessment)
        
        # Update guard
        guard.assessment_count += 1
        guard.last_assessed_at = datetime.utcnow()
        guard.next_assessment_at = datetime.utcnow() + timedelta(
            minutes=DEFAULT_REASSESSMENT_INTERVAL_MINUTES
        )
        
        # Determine status
        if guard.status == GuardStatus.DISCOVERED:
            guard.status = GuardStatus.ACTIVE
        
        await store.update_guard(guard)
        
        return assessment
    
    def _extract_severity(self, evidence: list[Any]) -> str | None:
        """Extract the highest severity from evidence items."""
        severities = [e.severity for e in evidence if hasattr(e, 'severity') and e.severity]
        if not severities:
            return None
        
        severity_order = {"warning": 3, "caution": 2, "info": 1}
        highest = max(severities, key=lambda s: severity_order.get(s, 0))
        return highest
    
    def _extract_environmental_summary(self, observations: list[Any]) -> dict[str, Any]:
        """Extract a compact environmental summary from observations."""
        summary = {}
        for obs in observations:
            if hasattr(obs, 'metric') and hasattr(obs, 'value'):
                summary[obs.metric] = {
                    "value": obs.value,
                    "unit": getattr(obs, 'unit', None),
                    "severity": getattr(obs, 'severity', None),
                }
        return summary
    
    def _extract_personal_constraints(self, result: Assessment) -> list[dict[str, Any]]:
        """Extract personal constraints from assessment result."""
        constraints = []
        if hasattr(result, 'personal_context') and result.personal_context:
            for c in getattr(result.personal_context, 'constraints', []):
                constraints.append({
                    "type": c.constraint_type.value if hasattr(c, 'constraint_type') else str(c),
                    "value": c.value if hasattr(c, 'value') else str(c),
                })
        return constraints
    
    # --- Change Detection ---
    
    async def detect_material_change(
        self,
        guard: Guard,
        previous_assessment: GuardAssessment,
        current_assessment: GuardAssessment,
    ) -> GuardAlert | None:
        """Detect if a material change occurred between assessments.
        
        Returns a GuardAlert if material change detected, None otherwise.
        """
        # Decision state change
        if previous_assessment.decision_state != current_assessment.decision_state:
            return GuardAlert.create(
                guard_id=guard.guard_id,
                previous_state=previous_assessment.decision_state,
                new_state=current_assessment.decision_state,
                change_type=AlertChangeType.DECISION_STATE_CHANGE,
                reason_codes=current_assessment.reason_codes,
                evidence=self._build_change_evidence(
                    previous_assessment,
                    current_assessment,
                    "decision_state_change"
                ),
            )
        
        # Severity escalation
        severity_order = {"warning": 3, "caution": 2, "info": 1}
        prev_sev = severity_order.get(previous_assessment.severity or "info", 0)
        curr_sev = severity_order.get(current_assessment.severity or "info", 0)
        
        if curr_sev > prev_sev:
            return GuardAlert.create(
                guard_id=guard.guard_id,
                previous_state=previous_assessment.severity or "info",
                new_state=current_assessment.severity or "info",
                change_type=AlertChangeType.SEVERITY_ESCALATION,
                reason_codes=current_assessment.reason_codes,
                evidence=self._build_change_evidence(
                    previous_assessment,
                    current_assessment,
                    "severity_escalation"
                ),
            )
        
        # Better window appeared
        prev_had_window = len(previous_assessment.candidate_windows) > 0
        curr_has_window = len(current_assessment.candidate_windows) > 0
        
        if curr_has_window and not prev_had_window:
            return GuardAlert.create(
                guard_id=guard.guard_id,
                previous_state=previous_assessment.decision_state,
                new_state=current_assessment.decision_state,
                change_type=AlertChangeType.BETTER_WINDOW_APPEARED,
                reason_codes=current_assessment.reason_codes,
                evidence=self._build_change_evidence(
                    previous_assessment,
                    current_assessment,
                    "better_window_appeared"
                ),
            )
        
        # Better window disappeared
        if prev_had_window and not curr_has_window:
            return GuardAlert.create(
                guard_id=guard.guard_id,
                previous_state=previous_assessment.decision_state,
                new_state=current_assessment.decision_state,
                change_type=AlertChangeType.BETTER_WINDOW_DISAPPEARED,
                reason_codes=current_assessment.reason_codes,
                evidence=self._build_change_evidence(
                    previous_assessment,
                    current_assessment,
                    "better_window_disappeared"
                ),
            )
        
        # Personal conflict introduced
        prev_conflicts = len(previous_assessment.personal_constraints)
        curr_conflicts = len(current_assessment.personal_constraints)
        
        if curr_conflicts > prev_conflicts:
            return GuardAlert.create(
                guard_id=guard.guard_id,
                previous_state=previous_assessment.decision_state,
                new_state=current_assessment.decision_state,
                change_type=AlertChangeType.PERSONAL_CONFLICT_INTRODUCED,
                reason_codes=current_assessment.reason_codes,
                evidence=self._build_change_evidence(
                    previous_assessment,
                    current_assessment,
                    "personal_conflict_introduced"
                ),
            )
        
        # No material change
        return None
    
    def _build_change_evidence(
        self,
        previous: GuardAssessment,
        current: GuardAssessment,
        change_type: str,
    ) -> dict[str, Any]:
        """Build evidence object for a material change alert."""
        return {
            "change_type": change_type,
            "previous_assessment": {
                "decision_state": previous.decision_state,
                "severity": previous.severity,
                "environmental_summary": previous.environmental_summary,
                "candidate_windows_count": len(previous.candidate_windows),
                "reason_codes": previous.reason_codes[:5],  # Limit for brevity
            },
            "current_assessment": {
                "decision_state": current.decision_state,
                "severity": current.severity,
                "environmental_summary": current.environmental_summary,
                "candidate_windows_count": len(current.candidate_windows),
                "reason_codes": current.reason_codes[:5],
            },
            "assessed_at": current.assessed_at.isoformat(),
        }
    
    # --- Reassessment Loop ---
    
    async def reassess_active_guards(self) -> dict[str, Any]:
        """Reassess all active guards that are due for assessment.
        
        This is the main worker function called by the scheduler.
        Returns stats about the reassessment run.
        """
        store = await self._get_store()
        
        # Get guards due for reassessment
        all_guards = await store.list_guards(status=GuardStatus.ACTIVE)
        due_guards = [
            g for g in all_guards
            if g.next_assessment_at and g.next_assessment_at <= datetime.utcnow()
        ]
        
        stats = {
            "guards_checked": 0,
            "assessments_run": 0,
            "material_changes": 0,
            "alerts_created": 0,
            "errors": [],
        }
        
        for guard in due_guards:
            stats["guards_checked"] += 1
            
            try:
                # Get previous assessment
                previous = await store.get_latest_assessment(guard.guard_id)
                
                # Run new assessment
                current = await self.assess_guard(guard)
                stats["assessments_run"] += 1
                
                # Check for material change (only if we have a previous assessment)
                if previous:
                    alert = await self.detect_material_change(
                        guard, previous, current
                    )
                    
                    if alert:
                        stats["material_changes"] += 1
                        
                        # Store the alert
                        await store.create_alert(alert)
                        stats["alerts_created"] += 1
                        
                        # Update guard status
                        guard.status = GuardStatus.ALERT_READY
                        await store.update_guard(guard)
                    else:
                        # No change - mark as unchanged
                        guard.status = GuardStatus.UNCHANGED
                        await store.update_guard(guard)
                
            except Exception as e:
                stats["errors"].append({
                    "guard_id": guard.guard_id,
                    "error": str(e),
                })
        
        return stats
    
    # --- Lifecycle Management ---
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert and update guard status."""
        store = await self._get_store()
        
        success = await store.acknowledge_alert(alert_id)
        if not success:
            return False
        
        # Get the alert to find the guard
        alerts = await store.list_alerts(unacknowledged_only=False)
        alert = next((a for a in alerts if a.alert_id == alert_id), None)
        if not alert:
            return True
        
        # Update guard status
        guard = await store.get_guard(alert.guard_id)
        if guard and guard.status == GuardStatus.ALERT_READY:
            guard.status = GuardStatus.ACKNOWLEDGED
            await store.update_guard(guard)
        
        return True
    
    async def cancel_guard(self, guard_id: str) -> bool:
        """Cancel a guard."""
        store = await self._get_store()
        
        guard = await store.get_guard(guard_id)
        if not guard:
            return False
        
        guard.status = GuardStatus.CANCELLED
        await store.update_guard(guard)
        return True
    
    async def run_maintenance(self) -> dict[str, Any]:
        """Run periodic maintenance tasks.
        
        - Expire guards whose planned time has passed
        - Clean up old data beyond retention period
        """
        store = await self._get_store()
        
        expired = await store.expire_guards()
        cleaned = await store.cleanup_old_data()
        
        return {
            "guards_expired": expired,
            "guards_deleted": cleaned.get("guards_deleted", 0),
        }
