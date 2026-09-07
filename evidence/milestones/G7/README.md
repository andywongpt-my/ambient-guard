# G7 — Guard Mode Evidence

This directory contains evidence for G7 (Proactive Environmental Agent) certification.

## Evidence Checklist

### Guard Creation
- [ ] Guard creation from valid Bee intent
- [ ] Unsupported activity ignored
- [ ] Duplicate guard prevention
- [ ] Expired intent not creating guard

### Baseline Assessment
- [ ] Baseline assessment stored
- [ ] Decision state recorded
- [ ] Environmental summary captured
- [ ] Personal constraints included (G3)

### Reassessment
- [ ] Scheduled reassessment works
- [ ] Assessment frequency correct (45 min default)
- [ ] Guard status updated after assessment

### Material Change Detection
- [ ] Decision-state transition detected
- [ ] Severity escalation triggers alert
- [ ] Better window appearance triggers alert
- [ ] Better window disappearance triggers alert
- [ ] Personal conflict introduction triggers alert
- [ ] Insignificant change remains silent

### Alert Generation
- [ ] Alert object created correctly
- [ ] Alert stored in database
- [ ] Guard status updated to ALERT_READY
- [ ] Alert contains structured evidence

### Lifecycle
- [ ] Guard expires after planned time + grace period
- [ ] Cancelled guards marked correctly
- [ ] Expired guards cleaned up
- [ ] Retention period enforced (7 days)

### Privacy
- [ ] Bee source references hashed (not stored raw)
- [ ] Guard serialization sanitized
- [ ] Assessment data minimal
- [ ] No raw conversation text persisted

### UI
- [ ] Active guards list renders
- [ ] Guard detail page shows decision history
- [ ] Alert notification works
- [ ] Acknowledgment works

### Production
- [ ] Database migrations run
- [ ] Scheduler starts on app startup
- [ ] Health endpoint shows guard_mode status
- [ ] Live Bee path works end-to-end

## Directory Structure

```
G7/
├── README.md                           # This file
├── 01_guard_creation.json              # Guard creation evidence
├── 02_baseline_assessment.json         # Baseline assessment evidence
├── 03_reassessment.json                # Reassessment evidence
├── 04_material_change.json             # Material change detection evidence
├── 05_alert_generation.json            # Alert generation evidence
├── 06_ui_screenshot.png                # Guard Mode UI screenshot
├── 07_production_health.json           # Production health check
├── 08_test_results.txt                 # Test execution results
└── 09_final_commit.txt                 # Final commit hash
```

## Production Validation

### Endpoint Checklist
- [ ] GET /api/v1/guards - List guards
- [ ] GET /api/v1/guards/{id} - Guard detail
- [ ] POST /api/v1/guards - Create guard
- [ ] POST /api/v1/guards/discover - Trigger discovery
- [ ] POST /api/v1/guards/{id}/acknowledge - Acknowledge alert
- [ ] DELETE /api/v1/guards/{id} - Cancel guard
- [ ] GET /api/v1/guards/alerts/unacknowledged - List alerts
- [ ] GET /api/v1/guards/scheduler/status - Scheduler status
- [ ] GET /health - Health check (guard_mode field)

### Database Verification
```sql
-- Verify tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('guards', 'guard_assessments', 'guard_alerts');

-- Verify indexes
SELECT indexname FROM pg_indexes WHERE tablename = 'guards';
```

## Final Report

See `G7_final_report.md` for the complete certification report.
