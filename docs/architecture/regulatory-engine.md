# Regulatory Engine

## Overview

The **Regulatory Engine** is a Python backend module that validates medical device logs against the **MED-THERM-2026** regulatory standard for portable temperature-controlled plasma transport units.

### Purpose

This module serves as the core validation engine for the MED-THERM Compliance Platform. It:

1. **Parses** raw device logs into structured data
2. **Normalizes** and validates log sequences
3. **Applies** 21 regulatory rules across 8 categories
4. **Generates** structured compliance reports with severity classification
5. **Provides** FastAPI endpoints for integration with frontend systems

### Key Features

- **Zero-code rule registration** - Decorator-based pattern for adding new rules
- **Temporal analysis** - Handles time-dependent rule logic (excursions, recovery, cumulative durations)
- **Evidence linking** - Each violation references specific log entries
- **Severity classification** - Critical, High, Medium, Low, Info levels

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      FastAPI Application Layer                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  /api/logs   │  │  /api/validate│  │  /api/health  │   │
│  │  (ingestion)  │  │  (engine)     │  │  (metadata)    │   │
│  └──────┬────────┘  └──────┬────────┘  └──────┬────────┘   │
│         │                    │                    │                │
│         └────────────────────┴────────────────────┴────────────────┘   │
│                              ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              Regulatory Engine Core                       │   │
│  │                                                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │   │
│  │  │  Parser   │  │Normalizer│  │  Engine   │       │   │
│  │  └─────┬────┘  └─────┬────┘  └─────┬────┘       │   │
│  │        │                │                │                │   │
│  │        ▼                ▼                ▼                │   │
│  │  ┌─────────────────────────────────────────────────────┐       │   │
│  │  │              Rule Registry (21 rules)             │       │   │
│  │  │                                                       │       │   │
│  │  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ │       │   │
│  │  │  │TEMP│ │SENS│ │ALRM│ │DATA│ │... │       │   │
│  │  │  │ 4  │ │ 3  │ │ 3  │ │ 3  │     │       │   │
│  │  │  └────┘ └────┘ └────┘ └────┘ └────┘ │       │   │
│  │  └─────────────────────────────────────────────────────┘       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## MED-THERM-2026 Rule Mapping

The engine implements all 21 MED-THERM-2026 regulatory rules organized into 8 categories:

### 1. Thermal Safety (REG-TEMP 1-4)

| Rule ID | Description | Implementation Notes |
|----------|-------------|---------------------|
| **REG-TEMP-1** | Maintain internal temperature: 2°C ≤ T ≤ 8°C | Filters `TEMP_READING` entries, checks each reading against range, generates evidence for violations |
| **REG-TEMP-2** | Excursion limits: max 5min/event, 10min cumulative/24h | Detects contiguous out-of-range periods, tracks cumulative duration, CRITICAL if exceeded |
| **REG-TEMP-3** | Recovery time ≤ 3min after disturbance | Monitors `DOOR_OPEN` events, measures time to return to range |
| **REG-TEMP-4** | Sampling frequency ≤ 30 seconds | Calculates time deltas between consecutive readings, flags gaps > 30s |

**Implementation Decision:** Temporal rules (REG-TEMP-2, REG-TEMP-3) maintain state across log entries to track excursions and recovery windows.

### 2. Sensor Redundancy (REG-SENS 1-3)

| Rule ID | Description | Implementation Notes |
|----------|-------------|---------------------|
| **REG-SENS-1** | At least one primary + one redundant secondary sensor | Detects `SENSOR_TIMEOUT` events, checks for PRIMARY/SECONDARY failures |
| **REG-SENS-2** | Sensors must not be placed within 15cm of airflow outlet | Returns INFO finding with `needs_visual_verification=True` - requires VLLM/blueprint analysis |
| **REG-SENS-3** | Sensor agreement: \|T1 - T2\| ≤ 0.5°C | Compares primary/secondary readings at same timestamps, calculates differences |

**Implementation Decision:** REG-SENS-2 and REG-INS rules require visual analysis - they return INFO findings explaining the limitation for log-only validation.

### 3. Alarm System (REG-ALARM 1-3)

| Rule ID | Description | Implementation Notes |
|----------|-------------|---------------------|
| **REG-ALARM-1** | Alarm shall activate if temperature out of range for ≥ 2min | Detects excursions, checks if `ALARM_TRIGGERED` occurs within 2min window |
| **REG-ALARM-2** | Notification latency ≤ 10 seconds | Returns INFO - logs don't contain notification timestamps, requires end-to-end verification |
| **REG-ALARM-3** | Support: audible, visual dashboard, remote mobile | Returns INFO - logs show `ALARM_TRIGGERED` but can't verify 3 channels without physical testing |

**Implementation Decision:** REG-ALARM-2 and REG-ALARM-3 have limited log visibility - they document what can and cannot be verified from logs alone.

### 4. Data Integrity (REG-DATA 1-3)

| Rule ID | Description | Implementation Notes |
|----------|-------------|---------------------|
| **REG-DATA-1** | Immutable audit log of: temp, alarms, config, sensor status | Checks for required event types in logs, conceptual design-level guarantee |
| **REG-DATA-2** | Data gaps in telemetry ≤ 90 seconds | Analyzes all log entry time deltas, flags gaps > 90s, counts `TELEMETRY_SYNC_FAILED` |
| **REG-DATA-3**` | Local data retention ≥ 72 hours | Checks log time span if available, returns INFO for verification requirement |

### 5. Power System (REG-POWER 1-2)

| Rule ID | Description | Implementation Notes |
|----------|-------------|---------------------|
| **REG-POWER-1** | Battery backup ≥ 4 hours continuous operation | Calculates drain rate from `BATTERY_LEVEL` readings, estimates runtime |
| **REG-POWER-2** | Temperature compliance in battery mode | Checks `VOLTAGE` drops (battery mode indicator), correlates with temp readings |

**Implementation Decision:** REG-POWER-1 extrapolates runtime from observed drain rates - actual verification requires full discharge test.

### 6. Cooling System (REG-COOL 1-2)

| Rule ID | Description | Implementation Notes |
|----------|-------------|---------------------|
| **REG-COOL-1** | At least 2 airflow paths | Returns INFO - requires schematic or physical inspection to verify |
| **REG-COOL-2** | Single-point failure tolerance ≤ 3min | Detects fan anomalies (`FAN_SPEED`=0` or drops), monitors temp during failures |

### 7. Structural & Insulation (REG-INS 1-2)

| Rule ID | Description | Implementation Notes |
|----------|-------------|---------------------|
| **REG-INS-1** | Insulation thickness ≥ 4 cm on all chamber walls | Returns INFO with `needs_visual_verification=True` - requires blueprint analysis |
| **REG-INS-2** | Battery compartment physically/thermally isolated | Returns INFO - requires schematic analysis or physical inspection |

**Implementation Decision:** Both REG-INS rules require visual/blueprint analysis - they return INFO findings explaining the limitation.

### 8. Operational Behavior (REG-OPS 1-2)

| Rule ID | Description | Implementation Notes |
|----------|-------------|---------------------|
| **REG-OPS-1** | Door recovery: stabilize ≤ 3min, temp ≤ 8°C | Monitors `DOOR_OPEN` → `DOOR_CLOSE`, checks temp during recovery window |
| **REG-OPS-2** | Access frequency warning: > 10 events/hour | Counts `DOOR_OPEN` per rolling hour, triggers warning if exceeded |

---

## Data Models

### LogEntry

Represents a single parsed log line from the device.

```python
class LogEntry(BaseModel):
    timestamp: datetime          # When the event occurred
    log_type: LogType          # Type of log (TEMP_READING, ALARM_TRIGGERED, etc.)
    raw_value: str              # Original value from log line
    parsed_value: Optional[Any]  # Extracted numeric value (float, int, etc.)
    sensor_id: Optional[str]      # Sensor identifier (PRIMARY/SECONDARY)
    metadata: dict              # Additional context
```

**Supported Log Types:**
- `TEMP_READING` - Temperature measurements
- `FAN_SPEED` - Cooling fan RPM
- `VOLTAGE` - Power voltage
- `HUMIDITY` - Ambient humidity
- `BATTERY_LEVEL` - Battery percentage
- `DOOR_OPEN` / `DOOR_CLOSE` - Access events
- `DEVICE_START` - System startup
- `ALARM_TRIGGERED` - Alarm activation
- `TEMP_WARNING` - Temperature warning
- `SENSOR_TIMEOUT` - Sensor failure
- `TELEMETRY_SYNC_FAILED` - Telemetry communication failure
- `COOLING_RECOVERY_START` - Cooling system recovery initiation

### Finding

Represents a rule evaluation result.

```python
class Finding(BaseModel):
    rule_id: str                    # e.g., "REG-TEMP-1"
    rule_description: str           # Human-readable rule description
    category: str                  # "thermal", "sensor", "alarm", etc.
    severity: Severity              # CRITICAL, HIGH, MEDIUM, LOW, INFO
    passed: bool                   # True if rule passed
    message: str                   # Explanation of result
    evidence: List[Evidence]        # Links to specific log entries
    timestamp: datetime              # When finding was generated
    remediation_hint: Optional[str]  # Suggested fix
    needs_visual_verification: bool   # True if VLLM/blueprint analysis needed
```

### ComplianceReport

Aggregates all findings into a complete compliance assessment.

```python
class ComplianceReport(BaseModel):
    device_id: str                          # Device identifier
    analyzed_at: datetime                    # When validation ran
    total_entries: int                       # Number of log entries processed
    time_range_start: Optional[datetime]         # First log timestamp
    time_range_end: Optional[datetime]           # Last log timestamp

    summary: Dict[str, CategorySummary]         # Per-category results
    findings: List[Finding]                   # All rule results
    passed_count: int                          # Number of rules that passed
    failed_count: int                          # Number of rules that failed
    critical_count: int                        # Number of CRITICAL findings
```

---

## API Endpoints

### Health & Metadata

#### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "app_name": "MED-THERM Compliance Engine",
  "app_version": "0.1.0",
  "rules_loaded": 21,
  "categories": ["thermal", "sensor", "alarm", "data", "power", "cooling", "insulation", "operational"],
  "debug": true
}
```

#### GET /api/health/rules

List all registered rules.

**Response:**
```json
{
  "total": 21,
  "rules": [
    {
      "rule_id": "REG-TEMP-1",
      "description": "Maintain internal temperature: 2°C ≤ T ≤ 8°C at all times...",
      "category": "thermal",
      "default_severity": "high"
    },
    ...
  ]
}
```

#### GET /api/health/categories

List rules by category.

**Response:**
```json
{
  "thermal": {
    "count": 4,
    "rules": ["REG-TEMP-1", "REG-TEMP-2", "REG-TEMP-3", "REG-TEMP-4"]
  },
  "sensor": {
    "count": 3,
    "rules": ["REG-SENS-1", "REG-SENS-2", "REG-SENS-3"]
  },
  ...
}
```

### Log Ingestion

#### POST /api/logs/ingest

Parse and ingest raw log lines.

**Request:**
```json
{
  "raw_logs": [
    "2026-05-14 14:00:10 TEMP_READING 4.3C",
    "2026-05-14 14:00:20 FAN_SPEED 2029RPM",
    "2026-05-14 14:00:30 TELEMETRY_SYNC_FAILED"
  ],
  "device_id": "CRYOSAFE-001"  // optional
}
```

**Response:**
```json
{
  "ingested": 3,
  "normalized": 3,
  "warnings": [],
  "sample_entries": [
    {
      "timestamp": "2026-05-14T14:00:10",
      "log_type": "TEMP_READING",
      "raw_value": "4.3C",
      "parsed_value": 4.3,
      "sensor_id": null
    },
    ...
  ]
}
```

#### POST /api/logs/ingest/file

Ingest logs from file upload.

**Request:** `multipart/form-data`
- `file`: Log file
- `device_id`: Optional device identifier

**Response:** Same as `/api/logs/ingest`

### Validation

#### POST /api/validate

Run full validation against all rules.

**Request:**
```json
{
  "raw_logs": [...],           // optional: raw log lines
  "entries": [...],            // optional: pre-parsed log entries
  "filter_rules": [...],       // optional: specific rules to run
  "device_id": "CRYOSAFE-001"  // optional
}
```

**Response:**
```json
{
  "report": {
    "device_id": "CRYOSAFE-001",
    "analyzed_at": "2026-05-12T14:30:00",
    "total_entries": 1000,
    "time_range_start": "2026-05-14T14:00:00",
    "time_range_end": "2026-05-14T14:16:30",

    "summary": {
      "thermal": {
        "passed": 2,
        "failed": 2,
        "total": 4
      },
      "sensor": {
        "passed": 1,
        "failed": 2,
        "total": 3
      },
      ...
    },

    "findings": [
      {
        "rule_id": "REG-TEMP-1",
        "rule_description": "Maintain internal temperature: 2°C ≤ T ≤ 8°C...",
        "category": "thermal",
        "severity": "critical",
        "passed": false,
        "message": "Found 5 temperature reading(s) outside range [2°C, 8°C]",
        "evidence": [
          {
            "entry_index": 0,
            "timestamp": "2026-05-14T14:00:40",
            "log_type": "TEMP_READING",
            "raw_value": "9.1C",
            "explanation": "Log entry: 2026-05-14 14:00:40 TEMP_READING 9.1C"
          },
          ...
        ],
        "timestamp": "2026-05-12T14:30:00",
        "remediation_hint": "Check cooling system performance...",
        "needs_visual_verification": false
      },
      ...
    ],

    "passed_count": 12,
    "failed_count": 13,
    "critical_count": 3
  }
}
```

#### GET /api/validate/quick-test

Quick validation endpoint with sample data for testing.

**Response:** Same as `/api/validate` with pre-configured test logs.

---

## Implementation Details

### Rule Registration Pattern

All rules use a decorator-based registration pattern:

```python
from app.regulatory.rules.base import BaseRule, register_rule

@register_rule
class RegTemp1(BaseRule):
    rule_id = "REG-TEMP-1"
    description = "Maintain internal temperature: 2°C ≤ T ≤ 8°C"
    category = "thermal"
    default_severity = Severity.HIGH

    def validate(self, logs: List[LogEntry], context: Dict[str, Any]) -> List[Finding]:
        # Implementation here
        pass
```

**Benefits:**
- **Zero-code registration** - Adding `@register_rule` decorator automatically registers the rule
- **Type safety** - Abstract base class enforces `validate()` method signature
- **Consistent interface** - All rules return `List[Finding]`
- **Easy discovery** - `RuleRegistry.get_all()` returns all registered rules

### Rule Execution Order

Rules execute in category order to handle dependencies:

1. **thermal** - REG-TEMP-1 to 4
2. **sensor** - REG-SENS-1 to 3
3. **alarm** - REG-ALARM-1 to 3
4. **data** - REG-DATA-1 to 3
5. **power** - REG-POWER-1 to 2
6. **cooling** - REG-COOL-1 to 2
7. **insulation** - REG-INS-1 to 2
8. **operational** - REG-OPS-1 to 2

**Rationale:** Some rules depend on context built by earlier rules (e.g., alarm rules benefit from thermal rule results).

### Context Building

The `LogNormalizer` builds shared context for all rules:

```python
context = {
    "time_range_start": datetime,
    "time_range_end": datetime,
    "duration_seconds": float,
    "duration_hours": float,
    "door_events_per_hour": Dict[datetime, int],
    "door_open_count": int,
    "door_close_count": int,
    "sensor_availability": {
        "primary": bool,
        "secondary": bool
    },
    "sensor_timeouts": List[Dict],
    "temp_reading_count": int,
    "alarm_count": int,
    "sync_failures": int,
    "logs_sorted": List[LogEntry]
}
```

This context is passed to every rule's `validate()` method, enabling efficient cross-rule analysis.

### Evidence Generation

The `BaseRule.create_finding()` helper automatically generates evidence:

```python
finding = self.create_finding(
    passed=False,
    message="Temperature out of range",
    evidence_logs=[log1, log2, log3],  # Up to 10 entries
    severity=Severity.CRITICAL,
    remediation_hint="Check cooling system"
)
```

Each evidence entry includes:
- **entry_index** - Position in evidence list
- **timestamp** - When the log occurred
- **log_type** - Type of log
- **raw_value** - Original log line
- **explanation** - Human-readable description

---

## Usage Examples

### Python API Usage

```python
from app.regulatory.parser import parse_raw_logs
from app.regulatory.engine import RegulatoryEngine

# Parse logs
raw_logs = [
    "2026-05-14 14:00:10 TEMP_READING 4.3C",
    "2026-05-14 14:00:40 TEMP_READING 9.1C",
    "2026-05-14 14:02:30 SENSOR_TIMEOUT SECONDARY_SENSOR",
]
entries, warnings = parse_raw_logs(raw_logs)

# Validate
engine = RegulatoryEngine()
report = engine.validate(entries, device_id="test-device")

# Results
print(f"Passed: {report.passed_count}")
print(f"Failed: {report.failed_count}")
print(f"Critical: {report.critical_count}")

for finding in report.findings:
    if not finding.passed:
        print(f"[{finding.severity.value}] {finding.rule_id}: {finding.message}")
        for evidence in finding.evidence:
            print(f"  Evidence: {evidence.timestamp} - {evidence.raw_value}")
```

### HTTP API Usage

```bash
# Ingest logs
curl -X POST http://localhost:8000/api/logs/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "raw_logs": [
      "2026-05-14 14:00:10 TEMP_READING 4.3C",
      "2026-05-14 14:00:40 TEMP_READING 9.1C"
    ]
  }'

# Validate
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "raw_logs": [
      "2026-05-14 14:00:10 TEMP_READING 4.3C",
      "2026-05-14 14:00:40 TEMP_READING 9.1C"
    ],
    "device_id": "CRYOSAFE-001"
  }'
```

### Filter Specific Rules

```python
# Only run thermal and sensor rules
report = engine.validate(
    entries,
    filter_rules=["REG-TEMP-1", "REG-TEMP-2", "REG-SENS-1", "REG-SENS-3"],
    device_id="test-device"
)
```

---

## Testing

### Test Structure

```
tests/
├── test_parser.py          # Log parsing edge cases
├── test_engine.py          # Full validation integration
└── rules/
    ├── test_temp.py        # REG-TEMP rules
    ├── test_sens.py        # REG-SENS rules
    ├── test_alarm.py       # REG-ALARM rules
    ├── test_data.py        # REG-DATA rules
    ├── test_power.py       # REG-POWER rules
    ├── test_cool.py        # REG-COOL rules
    ├── test_ins.py         # REG-INS rules
    └── test_ops.py         # REG-OPS rules
```

### Running Tests

```bash
cd backend
pytest -v
```

### Test Coverage

- **Parser tests:** Verify all 14 log types parse correctly
- **Rule tests:** Each rule has dedicated tests for happy paths and violations
- **Engine tests:** End-to-end validation with sample log file
- **Sample data:** Uses `docs/client/medical_device_logs_1000.txt`

---

## Important Implementation Decisions

### 1. Log-Only Validation Scope

**Decision:** This PoC focuses on log validation only.

**Rationale:**
- Reduces complexity for initial implementation
- VLLM integration will handle images and documents in a separate change
- Allows clear separation of concerns

**Impact:**
- REG-SENS-2, REG-INS-1, REG-INS-2 return INFO findings
- REG-ALARM-2, REG-ALARM-3 have limited log visibility
- Future VLLM integration can fill these gaps

### 2. In-Memory State

**Decision:** Validation runs are stateless; no database persistence in this change.

**Rationale:**
- Simplifies PoC implementation
- Each validation run is independent
- No need for database setup or migrations

**Impact:**
- Cannot track compliance history across runs
- Future changes can add PostgreSQL persistence

### 3. Rule Severity Classification

**Decision:** Default severity levels defined per rule, but can be overridden in findings.

**Rationale:**
- CRITICAL: Immediate patient safety risk (REG-TEMP-2, REG-SENS-1)
- HIGH: Significant compliance gap (most REG-TEMP violations)
- MEDIUM: Non-critical deviation (data gaps, missing sensors)
- LOW: Operational warnings (access frequency)
- INFO: Limitations or design notes

**Impact:**
- Clear prioritization for remediation
- Audit-ready severity classification

### 4. Temporal Rule State

**Decision:** Rules requiring temporal analysis maintain state during validation.

**Rationale:**
- REG-TEMP-2 needs to track excursion duration
- REG-TEMP-3 needs to monitor recovery windows
- REG-OPS-2 needs rolling hour counts

**Implementation:**
- State variables in `validate()` method
- Reset between validation runs
- No cross-run state persistence

### 5. Evidence Limiting

**Decision:** Limit evidence to 10 entries per finding.

**Rationale:**
- Prevents excessive report size
- Shows most relevant violations
- Full logs available for detailed analysis

**Impact:**
- Reports remain actionable
- All violations still counted in summary

---

## Future Enhancements

### Database Persistence

Add PostgreSQL storage for:
- Validation history
- Compliance trends over time
- Device tracking
- Report archival

### VLLM Integration

Connect to vision/language models for:
- REG-SENS-2: Blueprint sensor placement analysis
- REG-INS-1, REG-INS-2: Insulation verification from blueprints
- Document parsing for requirement extraction

### Real-Time Validation

Add WebSocket or streaming support for:
- Live log monitoring
- Real-time rule evaluation
- Instant alerting on CRITICAL violations

### Report Generation

Add:
- PDF export of compliance reports
- HTML dashboard views
- CSV export for regulatory submissions

---

## Performance Considerations

### Scalability

| Metric | Target | Notes |
|---------|--------|-------|
| Log throughput | 1000 entries in < 1s | O(n) parsing, O(r×n) validation |
| API latency | < 200ms p95 | For typical validation requests |
| Memory usage | < 100MB for 10K entries | In-memory processing |

### Optimization Strategies

- **Early filtering** - Skip irrelevant log types per rule
- **Efficient lookups** - Use dictionaries for sensor tracking
- **Batch processing** - Process logs in chunks for large datasets
- **Caching** - Cache rule instances (already done with singleton pattern)

---

## Troubleshooting

### Common Issues

**Issue:** "No temperature readings found"
- **Cause:** Log format mismatch or missing TEMP_READING events
- **Fix:** Verify log format matches `YYYY-MM-DD HH:MM:SS TYPE VALUE`

**Issue:** "Rule execution error"
- **Cause:** Unhandled exception in rule validation
- **Fix:** Check rule implementation, add error handling

**Issue:** "Sensor timeout detected"
- **Cause:** Device sensor failure or communication issue
- **Fix:** Check sensor wiring, power, and controller connectivity

### Debug Mode

Enable debug logging in `app/config.py`:

```python
class Settings(BaseSettings):
    debug: bool = True  # Enable detailed logging
```

Debug logs include:
- Rule execution start/end times
- Context building details
- Evidence generation steps

---

## References

- **MED-THERM-2026 Specification:** `../docs/client/Medical Device Regulatory Constraints.md`
- **Sample Logs:** `../docs/client/medical_device_logs_1000.txt`
- **OpenSpec Change:** `../openspec/changes/archive/2026-05-12-regulatory-engine/`
- **API Documentation:** http://localhost:8000/docs (when running)
