# G7 — Guard Mode: Proactive Environmental Agent

## Objective

Transform Ambient Guard from a request-response decision assistant into a **proactive, quiet, evidence-driven agent** that monitors upcoming activities and surfaces alerts only when decisions materially change.

## Guard Concept

A **Guard** represents one relevant upcoming Bee-derived activity that Ambient Guard monitors over time.

### Guard Lifecycle States

```
DISCOVERED → ACTIVE → [UNCHANGED | MATERIAL_CHANGE_DETECTED] → ALERT_READY → ACKNOWLEDGED → EXPIRED
                     ↓                                          ↓
                  INSUFFICIENT_DATA                         CANCELLED
```

**States:**
- **DISCOVERED**: Initial state when a guard-worthy Bee intent is found
- **ACTIVE**: Baseline assessment completed, monitoring in progress
- **UNCHANGED**: Reassessment completed, no material decision change
- **MATERIAL_CHANGE_DETECTED**: Decision state changed significantly
- **ALERT_READY**: Alert prepared for delivery
- **ACKNOWLEDGED**: User has seen/acted on the alert
- **EXPIRED**: Activity time passed or guard no longer relevant
- **CANCELLED**: User or system cancelled the guard
- **INSUFFICIENT_DATA**: Cannot assess due to missing environmental/personal data

## Guard Creation Policy

**Guard-worthy activities:**
- jogging / running
- walking
- cycling
- hiking
- outdoor exercise
- outdoor work
- outdoor commute
- picnic / outdoor family activity

**Creation criteria:**
- Activity is environmentally relevant
- Time is sufficiently specific (within configurable window, default 24 hours)
- Event is upcoming (not past)
- Context confidence is adequate (≥0.7)

**Non-qualifying:**
- Vague or past events
- Indoor activities
- Non-time-specific todos
- Already-expired intents

## Decision Change Detection

### Material Change Criteria

A change qualifies as material when one or more occur:

1. **Decision state change** (e.g., KEEP_PLANNED_TIME → BETTER_WINDOW_AVAILABLE)
2. **Severity category change** (info → caution → warning)
3. **Environmental threshold crossing** (AQI crosses 100, UV crosses 8, etc.)
4. **Alternative window appearance/disappearance** (≥15% improvement threshold)
5. **Personal context conflict introduction/removal**
6. **Forecast confidence change** affecting decision reliability

### Silent-by-Default Principle

- No alert for insignificant numeric changes
- No alert for unchanged decision state
- Record UNCHANGED internally but no user notification
- **Product principle:** "Ambient Guard interrupts only when the decision changes enough to matter"

## Reassessment Schedule

**Default frequency:** Every 30-60 minutes

**Constraints:**
- Do NOT poll Bee or environmental providers excessively
- Use APScheduler for in-process scheduling (lightweight, no external dependencies)
- Respect API rate limits (Open-Meteo: reasonable use, no explicit limit documented)
- Back off on repeated failures

## Data Model

### Database Schema (PostgreSQL)

```sql
CREATE TABLE guards (
    id SERIAL PRIMARY KEY,
    guard_id VARCHAR(36) UNIQUE NOT NULL,  -- UUID
    activity VARCHAR(100) NOT NULL,
    planned_time TIMESTAMPTZ NOT NULL,
    location_lat DOUBLE PRECISION,
    location_lon DOUBLE PRECISION,
    location_name VARCHAR(200),
    bee_source_type VARCHAR(50),  -- 'bee_todo' | 'bee_conversation'
    bee_source_reference_hash VARCHAR(64),  -- SHA-256 hash, not raw text
    status VARCHAR(30) NOT NULL DEFAULT 'discovered',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    last_assessed_at TIMESTAMPTZ,
    next_assessment_at TIMESTAMPTZ,
    assessment_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE guard_assessments (
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

CREATE TABLE guard_alerts (
    id SERIAL PRIMARY KEY,
    guard_id VARCHAR(36) NOT NULL REFERENCES guards(guard_id) ON DELETE CASCADE,
    previous_state VARCHAR(50) NOT NULL,
    new_state VARCHAR(50) NOT NULL,
    change_type VARCHAR(50) NOT NULL,  -- 'decision_change' | 'severity_change' | 'window_appeared' | etc.
    reason_codes JSONB NOT NULL,
    evidence JSONB NOT NULL,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_guards_status ON guards(status);
CREATE INDEX idx_guards_planned_time ON guards(planned_time);
CREATE INDEX idx_guards_next_assessment ON guards(next_assessment_at) WHERE status = 'active';
CREATE INDEX idx_guard_assessments_guard ON guard_assessments(guard_id);
CREATE INDEX idx_guard_alerts_guard ON guard_alerts(guard_id);
```

## Privacy Considerations

**Stored (normalized):**
- Activity type
- Planned time
- Location coordinates (hashed reference available)
- Decision states
- Reason codes
- Environmental summaries
- Assessment timestamps

**NOT stored:**
- Raw Bee recordings
- Full transcripts
- Unrelated conversations
- Unnecessary location history

**Retention:** 7 days automatic deletion after guard expiration

## Alert Delivery

**G7 V1 implementation:**
1. In-app notification (API endpoint + UI badge)
2. Decision history in Guard Mode UI

**Future considerations:**
- Browser notifications (if practical)
- Email/webhook (only if clear product value)

## API Endpoints

### Guard Management

- `POST /api/v1/guards` - Create guard from Bee context or manual input
- `GET /api/v1/guards` - List active guards
- `GET /api/v1/guards/{guard_id}` - Get guard details + decision history
- `POST /api/v1/guards/{guard_id}/acknowledge` - Acknowledge alert
- `DELETE /api/v1/guards/{guard_id}` - Cancel guard

### Guard Discovery

- `POST /api/v1/guards/discover` - Scan Bee context for guard-worthy activities

### Scheduler (Internal)

- Background worker runs every 30 minutes
- Discovers new guards from Bee
- Reassesses active guards
- Generates alerts for material changes
- Cleans up expired guards

## UI Components

### Active Guards Section

```
# Active Guards

🏃 Jogging
Today · 5:00 PM

Status: Watching
Last assessed: 3:15 PM
Decision: Keep planned time
No material change

[View details]
```

### Decision History

```
Decision Timeline

12:00  KEEP_PLANNED_TIME
14:00  KEEP_PLANNED_TIME
15:30  BETTER_WINDOW_AVAILABLE
       AQI worsened, better window at 7 PM
```

## Test Coverage

- Guard creation from valid Bee intent
- Unsupported activity ignored
- Stale intent ignored
- Baseline assessment stored
- Unchanged reassessment (no alert)
- Decision-state transition detected
- Material environmental change triggers alert
- Insignificant change remains silent
- Better window appearance/disappearance
- Personal conflict introduction/removal
- Insufficient environmental data handling
- Guard expiration
- Duplicate guard prevention
- Privacy-safe serialization
- Retention/deletion behavior
- Timezone correctness

## Success Criteria

- [ ] Bee-derived upcoming activity creates a Guard
- [ ] Baseline assessment is stored
- [ ] Guard reassessment works on schedule
- [ ] Insignificant changes remain silent
- [ ] Decision-state transitions are detected
- [ ] Material environmental changes trigger alerts
- [ ] Personal-context changes affect Guard decisions
- [ ] Guard lifecycle is explicit and correct
- [ ] Persistence is privacy-minimized
- [ ] Guard Mode UI renders active guards
- [ ] Decision history displays correctly
- [ ] Real alert delivery works
- [ ] All G1-G4 regressions pass
- [ ] New G7 tests pass
- [ ] Production deployment succeeds
