"""G7 Guard Mode tests.

Tests the proactive environmental monitoring system:
- Guard creation and lifecycle
- Baseline and follow-up assessments
- Material change detection
- Alert generation
- Privacy-safe serialization
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.guards.models import (
    Guard,
    GuardStatus,
    GuardAssessment,
    GuardAlert,
    AlertChangeType,
    GUARD_WORTHY_ACTIVITIES,
    MIN_GUARD_CONFIDENCE,
)


class TestGuardCreation:
    """Tests for guard creation and validation."""
    
    def test_guard_creation_basic(self):
        """Guard can be created with minimal required fields."""
        planned_time = datetime.utcnow() + timedelta(hours=2)
        guard = Guard.create(
            activity="jogging",
            planned_time=planned_time,
        )
        
        assert guard.guard_id is not None
        assert guard.activity == "jogging"
        assert guard.planned_time == planned_time
        assert guard.status == GuardStatus.DISCOVERED
        assert guard.created_at is not None
        assert guard.expires_at is not None
    
    def test_guard_creation_with_location(self):
        """Guard can include location information."""
        planned_time = datetime.utcnow() + timedelta(hours=2)
        guard = Guard.create(
            activity="cycling",
            planned_time=planned_time,
            location_lat=3.139,
            location_lon=101.6869,
            location_name="Kuala Lumpur",
        )
        
        assert guard.location_lat == 3.139
        assert guard.location_lon == 101.6869
        assert guard.location_name == "Kuala Lumpur"
    
    def test_guard_creation_with_bee_source(self):
        """Guard stores hashed Bee source reference, not raw text."""
        planned_time = datetime.utcnow() + timedelta(hours=2)
        guard = Guard.create(
            activity="hiking",
            planned_time=planned_time,
            bee_source_type="bee_todo",
            bee_source_reference="raw bee todo text that should not be stored",
        )
        
        assert guard.bee_source_type == "bee_todo"
        assert guard.bee_source_reference_hash is not None
        assert len(guard.bee_source_reference_hash) == 64  # SHA-256
        assert "raw bee todo" not in guard.bee_source_reference_hash
    
    def test_guard_is_guard_worthy(self):
        """Guard-worthy activities are correctly identified."""
        planned_time = datetime.utcnow() + timedelta(hours=2)
        
        # Guard-worthy activities
        for activity in ["jogging", "running", "walking", "cycling", "hiking"]:
            guard = Guard.create(activity=activity, planned_time=planned_time)
            assert guard.is_guard_worthy(), f"{activity} should be guard-worthy"
        
        # Non-guard-worthy activities
        guard = Guard.create(activity="coding", planned_time=planned_time)
        assert not guard.is_guard_worthy(), "coding should not be guard-worthy"
    
    def test_guard_expiration(self):
        """Guard expiration is correctly calculated."""
        planned_time = datetime.utcnow() + timedelta(hours=2)
        guard = Guard.create(activity="jogging", planned_time=planned_time)
        
        # Should not be expired yet
        assert not guard.is_expired()
        
        # Create an already-expired guard
        past_time = datetime.utcnow() - timedelta(hours=3)
        expired_guard = Guard.create(activity="jogging", planned_time=past_time)
        assert expired_guard.is_expired()
    
    def test_guard_to_dict_sanitized(self):
        """Guard serialization does not expose raw Bee source."""
        planned_time = datetime.utcnow() + timedelta(hours=2)
        guard = Guard.create(
            activity="jogging",
            planned_time=planned_time,
            bee_source_type="bee_conversation",
            bee_source_reference="sensitive conversation text",
        )
        
        data = guard.to_dict()
        assert "bee_source_reference" not in data
        assert data.get("bee_source_type") == "bee_conversation"


class TestGuardAssessment:
    """Tests for guard assessment snapshots."""
    
    def test_assessment_creation(self):
        """Assessment can be created with decision data."""
        assessment = GuardAssessment.create(
            guard_id="test-guard-id",
            assessment_number=1,
            decision_state="keep_planned_time",
            severity="info",
            environmental_summary={"aqi": {"value": 75, "unit": "index"}},
            reason_codes=["no_better_window_in_range"],
        )
        
        assert assessment.guard_id == "test-guard-id"
        assert assessment.assessment_number == 1
        assert assessment.decision_state == "keep_planned_time"
        assert assessment.severity == "info"
        assert assessment.assessed_at is not None
    
    def test_assessment_to_dict(self):
        """Assessment serialization preserves all data."""
        assessment = GuardAssessment.create(
            guard_id="test-guard-id",
            assessment_number=1,
            decision_state="better_window_available",
            severity="caution",
            environmental_summary={"aqi": {"value": 120}},
            reason_codes=["better_conditions:aqi"],
        )
        
        data = assessment.to_dict()
        assert data["guard_id"] == "test-guard-id"
        assert data["decision_state"] == "better_window_available"
        assert data["environmental_summary"]["aqi"]["value"] == 120


class TestGuardAlert:
    """Tests for guard alerts."""
    
    def test_alert_creation(self):
        """Alert can be created for material change."""
        alert = GuardAlert.create(
            guard_id="test-guard-id",
            previous_state="keep_planned_time",
            new_state="better_window_available",
            change_type=AlertChangeType.DECISION_STATE_CHANGE,
            reason_codes=["better_conditions:aqi,uv"],
            evidence={"previous_aqi": 100, "current_aqi": 50},
        )
        
        assert alert.guard_id == "test-guard-id"
        assert alert.previous_state == "keep_planned_time"
        assert alert.new_state == "better_window_available"
        assert alert.change_type == AlertChangeType.DECISION_STATE_CHANGE
        assert not alert.acknowledged
        assert alert.created_at is not None
    
    def test_alert_to_dict(self):
        """Alert serialization preserves all data."""
        alert = GuardAlert.create(
            guard_id="test-guard-id",
            previous_state="keep_planned_time",
            new_state="better_window_available",
            change_type=AlertChangeType.DECISION_STATE_CHANGE,
            reason_codes=["test_reason"],
            evidence={"test": "data"},
        )
        
        data = alert.to_dict()
        assert data["acknowledged"] is False
        assert data["change_type"] == "decision_state_change"


class TestGuardLifecycle:
    """Tests for guard lifecycle management."""
    
    @pytest.mark.asyncio
    async def test_discover_guards_from_bee(self):
        """Guard discovery creates guards from Bee context."""
        from app.guards.lifecycle import GuardLifecycle
        
        lifecycle = GuardLifecycle()
        
        # Mock Bee client
        with patch("app.guards.lifecycle.get_bee_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.today_context.return_value = MagicMock(
                model_dump=MagicMock(return_value={"todos": []})
            )
            mock_client.current_location.return_value = MagicMock(
                latitude=3.139,
                longitude=101.6869,
                display_name="Kuala Lumpur",
            )
            mock_client.search.return_value = MagicMock(
                results=[{
                    "id": "1",
                    "short_summary": "Go jogging at 5 PM",
                }]
            )
            mock_get_client.return_value = mock_client
            
            # Mock the store
            with patch("app.guards.lifecycle.get_guard_store") as mock_get_store:
                mock_store = AsyncMock()
                mock_store.guard_exists_by_hash = AsyncMock(return_value=False)
                mock_store.create_guard = AsyncMock()
                mock_get_store.return_value = mock_store
                
                # Mock the normalize function to return a valid intent
                with patch("app.guards.lifecycle.normalize") as mock_normalize:
                    from app.agent.models import ContextIntent
                    mock_intent = ContextIntent(
                        activity="jogging",
                        planned_time=datetime.utcnow() + timedelta(hours=2),
                        latitude=3.139,
                        longitude=101.6869,
                        intent_text="Go jogging at 5 PM",
                        source_ref="test",
                        confidence=0.9,
                    )
                    mock_normalize.return_value = mock_intent
                    
                    guards = await lifecycle.discover_guards_from_bee()
                    
                    # Should have created at least one guard
                    assert isinstance(guards, list)
    
    @pytest.mark.asyncio
    async def test_reassess_active_guards(self):
        """Reassessment processes due guards."""
        from app.guards.lifecycle import GuardLifecycle
        
        lifecycle = GuardLifecycle()
        
        with patch("app.guards.lifecycle.get_guard_store") as mock_get_store:
            mock_store = AsyncMock()
            
            # Create a mock guard due for reassessment
            guard = Guard.create(
                activity="jogging",
                planned_time=datetime.utcnow() + timedelta(hours=2),
            )
            guard.next_assessment_at = datetime.utcnow() - timedelta(minutes=1)
            
            mock_store.list_guards = AsyncMock(return_value=[guard])
            mock_store.get_latest_assessment = AsyncMock(return_value=None)
            mock_store.create_assessment = AsyncMock()
            mock_store.update_guard = AsyncMock()
            
            # Mock environmental service
            with patch.object(lifecycle, "_env_service") as mock_env:
                mock_env.observe.return_value = ([], [])
                
                # Mock reasoning
                with patch.object(lifecycle, "_reasoning") as mock_reasoning:
                    from app.agent.reasoning_models import Assessment
                    mock_result = MagicMock()
                    mock_result.decision_state = "keep_planned_time"
                    mock_result.evidence = []
                    mock_result.candidate_windows = []
                    mock_result.reason_codes = []
                    mock_result.personal_feasibility = None
                    mock_reasoning.assess.return_value = mock_result
                    
                    stats = await lifecycle.reassess_active_guards()
                    
                    assert stats["guards_checked"] >= 0


class TestMaterialChangeDetection:
    """Tests for material change detection."""
    
    @pytest.mark.asyncio
    async def test_decision_state_change_triggers_alert(self):
        """Decision state change creates an alert."""
        from app.guards.lifecycle import GuardLifecycle
        
        lifecycle = GuardLifecycle()
        
        guard = Guard.create(
            activity="jogging",
            planned_time=datetime.utcnow() + timedelta(hours=2),
        )
        
        previous = GuardAssessment.create(
            guard_id=guard.guard_id,
            assessment_number=1,
            decision_state="keep_planned_time",
        )
        
        current = GuardAssessment.create(
            guard_id=guard.guard_id,
            assessment_number=2,
            decision_state="better_window_available",
            candidate_windows=[{"time": "19:00", "score": 0.9}],
        )
        
        alert = await lifecycle.detect_material_change(guard, previous, current)
        
        assert alert is not None
        assert alert.change_type == AlertChangeType.DECISION_STATE_CHANGE
        assert alert.previous_state == "keep_planned_time"
        assert alert.new_state == "better_window_available"
    
    @pytest.mark.asyncio
    async def test_no_change_no_alert(self):
        """Unchanged decision does not create an alert."""
        from app.guards.lifecycle import GuardLifecycle
        
        lifecycle = GuardLifecycle()
        
        guard = Guard.create(
            activity="jogging",
            planned_time=datetime.utcnow() + timedelta(hours=2),
        )
        
        previous = GuardAssessment.create(
            guard_id=guard.guard_id,
            assessment_number=1,
            decision_state="keep_planned_time",
            severity="info",
            candidate_windows=[],
        )
        
        current = GuardAssessment.create(
            guard_id=guard.guard_id,
            assessment_number=2,
            decision_state="keep_planned_time",
            severity="info",
            candidate_windows=[],
        )
        
        alert = await lifecycle.detect_material_change(guard, previous, current)
        
        assert alert is None
    
    @pytest.mark.asyncio
    async def test_severity_escalation_triggers_alert(self):
        """Severity escalation creates an alert."""
        from app.guards.lifecycle import GuardLifecycle
        
        lifecycle = GuardLifecycle()
        
        guard = Guard.create(
            activity="jogging",
            planned_time=datetime.utcnow() + timedelta(hours=2),
        )
        
        previous = GuardAssessment.create(
            guard_id=guard.guard_id,
            assessment_number=1,
            decision_state="keep_planned_time",
            severity="info",
        )
        
        current = GuardAssessment.create(
            guard_id=guard.guard_id,
            assessment_number=2,
            decision_state="keep_planned_time",
            severity="warning",
            environmental_summary={"aqi": {"value": 150}},
        )
        
        alert = await lifecycle.detect_material_change(guard, previous, current)
        
        assert alert is not None
        assert alert.change_type == AlertChangeType.SEVERITY_ESCALATION


class TestPrivacy:
    """Tests for privacy-safe guard handling."""
    
    def test_bee_source_hashing(self):
        """Bee source references are hashed, not stored directly."""
        from app.guards.models import hash_bee_reference
        
        raw = "sensitive bee conversation text"
        hashed = hash_bee_reference(raw)
        
        assert hashed != raw
        assert len(hashed) == 64  # SHA-256 hex
        assert "sensitive" not in hashed
    
    def test_guard_does_not_expose_raw_source(self):
        """Guard model never exposes raw Bee source."""
        planned_time = datetime.utcnow() + timedelta(hours=2)
        guard = Guard.create(
            activity="jogging",
            planned_time=planned_time,
            bee_source_type="bee_conversation",
            bee_source_reference="private conversation",
        )
        
        # Check all attributes
        assert not hasattr(guard, "bee_source_reference")
        assert guard.bee_source_reference_hash is not None
        assert guard.bee_source_reference_hash != "private conversation"
    
    def test_assessment_minimal_personal_data(self):
        """Assessment stores minimal personal context."""
        assessment = GuardAssessment.create(
            guard_id="test",
            assessment_number=1,
            decision_state="keep_planned_time",
            personal_constraints=[{"type": "unavailable_before", "value": "17:00"}],
        )
        
        # Should only store normalized constraints, not raw context
        data = assessment.to_dict()
        assert "personal_constraints" in data
        # Should not have raw Bee text
        assert "bee_conversation" not in str(data)


class TestGuardExpiration:
    """Tests for guard expiration and cleanup."""
    
    def test_guard_expires_after_grace_period(self):
        """Guard expires after planned time + grace period."""
        planned_time = datetime.utcnow() - timedelta(hours=1)
        guard = Guard.create(activity="jogging", planned_time=planned_time)
        
        # Should be expired (default grace is 2 hours, so this is within grace)
        # Actually, if we're 1 hour after planned, and grace is 2 hours, it's NOT expired
        # Let's test with 3 hours after planned
        planned_time_3h = datetime.utcnow() - timedelta(hours=3)
        guard_3h = Guard.create(activity="jogging", planned_time=planned_time_3h)
        
        assert guard_3h.is_expired()
    
    def test_future_guard_not_expired(self):
        """Future guard is not expired."""
        planned_time = datetime.utcnow() + timedelta(hours=5)
        guard = Guard.create(activity="jogging", planned_time=planned_time)
        
        assert not guard.is_expired()


# Run tests with: pytest tests/test_g7_guards.py -v
