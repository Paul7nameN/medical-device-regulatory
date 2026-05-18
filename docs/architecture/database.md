# Schema Bazei de Date

> Acest fisier a fost mutat din `docs/database-schema-module.md`.

---

## Overview

The **Database Schema Module** (`backend/app/database.py`, `backend/app/models/`) provides the foundational PostgreSQL database schema for the MED-THERM Compliance Platform. It enables persistence of device data, analysis sessions, log entries, regulatory violations, compliance reports, and immutable audit trails required for MED-THERM-2026 regulatory compliance.

## What It Does

The module provides:

1. **Database Connection Management** - Async and sync SQLAlchemy engines with session management
2. **ORM Models** - SQLAlchemy declarative models for all domain entities
3. **Pydantic Models** - Type-safe data models for API request/response validation
4. **Enum Definitions** - Standardized enumerations for status codes, severity levels, and log types
5. **Migration Support** - Alembic migrations for schema versioning and deployment
6. **Audit Trail Immutability** - Database-level enforcement of immutable audit logs (REG-DATA-1)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Database Layer                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              SQLAlchemy ORM Models                        │  │
│  │                                                         │  │
│  │  Device              AnalysisSession                       │  │
│  │  LogEntry            DetectedViolation                    │  │
│  │  ComplianceReport    AuditLog                             │  │
│  └─────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Pydantic Data Models                        │  │
│  │                                                         │  │
│  │  LogEntry (Pydantic)    Finding                         │  │
│  │  ComplianceReport (Pydantic)  CategorySummary          │  │
│  └─────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              PostgreSQL Database                        │  │
│  │                                                         │  │
│  │  Tables: devices, analysis_sessions, log_entries,       │  │
│  │          detected_violations, compliance_reports,       │  │
│  │          audit_log                                       │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Module Structure

```
backend/app/
├── database.py              # Database engines and session management
├── models/
│   ├── __init__.py         # Model exports
│   ├── orm.py              # SQLAlchemy ORM models
│   ├── enums.py            # Enum definitions
│   ├── findings.py         # Pydantic compliance models
│   └── logs.py             # Pydantic log models
│
backend/
├── alembic.ini             # Alembic configuration
└── migrations/
    ├── env.py               # Alembic environment
    └── versions/
        ├── 0001_initial_schema.py
        └── 0002_audit_log_immutability.py
```

## Database Tables

### 1. devices

Stores medical device inventory and metadata.

**Columns:**
- `id` (UUID, PK) - Unique device identifier
- `name` (TEXT, NOT NULL) - Device name
- `model` (TEXT, NULLABLE) - Device model
- `serial_number` (TEXT, UNIQUE, NULLABLE) - Serial number
- `status` (ENUM, NOT NULL) - Device status: ONLINE, OFFLINE, MAINTENANCE, REGISTERED
- `last_seen_at` (DATETIME, NULLABLE) - Last communication timestamp
- `created_at` (DATETIME, NOT NULL) - Record creation timestamp
- `updated_at` (DATETIME, NOT NULL) - Last update timestamp

**Indexes:**
- `idx_devices_serial_number` (UNIQUE) - Serial number lookup

**Relationships:**
- One-to-many with `analysis_sessions`
- One-to-many with `log_entries`
- One-to-many with `detected_violations`
- One-to-many with `compliance_reports`

**Cascade Behavior:**
- DELETE device → CASCADE to log_entries
- DELETE device → SET NULL for analysis_sessions, violations, reports

### 2. analysis_sessions

Tracks VLLM-based document/image analysis sessions.

**Columns:**
- `id` (UUID, PK) - Session identifier
- `device_id` (UUID, FK, NULLABLE) - Associated device
- `status` (ENUM, NOT NULL) - Session status: PENDING, COMPLETED, FAILED
- `config` (JSONB, NULLABLE) - Analysis configuration
- `result_summary` (TEXT, NULLABLE) - Analysis result summary
- `result_path` (TEXT, NULLABLE) - Path to analysis results
- `started_at` (DATETIME, NOT NULL) - Session start timestamp
- `completed_at` (DATETIME, NULLABLE) - Session completion timestamp
- `created_at` (DATETIME, NOT NULL) - Record creation timestamp
- `updated_at` (DATETIME, NOT NULL) - Last update timestamp

**Indexes:**
- `idx_analysis_sessions_device_id` - Device lookup
- `idx_analysis_sessions_device_id_started_at` - Device time-range queries
- `idx_analysis_sessions_status` - Status filtering

**Relationships:**
- Many-to-one with `device`
- One-to-many with `log_entries`
- One-to-many with `detected_violations`

**Cascade Behavior:**
- DELETE device → SET NULL for device_id
- DELETE session → SET NULL for log_entries, violations

### 3. log_entries

Stores time-series device telemetry and event logs.

**Columns:**
- `id` (UUID, PK) - Log entry identifier
- `device_id` (UUID, FK, NOT NULL) - Source device
- `analysis_session_id` (UUID, FK, NULLABLE) - Associated analysis session
- `timestamp` (DATETIME, NOT NULL) - Event timestamp
- `log_type` (ENUM, NOT NULL) - Log type: TELEMETRY, EVENT, ALERT, STATUS
- `source` (TEXT, NULLABLE) - Log source identifier
- `payload` (JSONB, NULLABLE) - Log payload data
- `created_at` (DATETIME, NOT NULL) - Record creation timestamp
- `updated_at` (DATETIME, NOT NULL) - Last update timestamp

**Indexes:**
- `idx_log_entries_timestamp` - Time-range queries
- `idx_log_entries_device_id` - Device lookup
- `idx_log_entries_analysis_session_id` - Session lookup
- `idx_log_entries_log_type` - Log type filtering
- `idx_log_entries_device_timestamp` - Composite device + time queries

**Relationships:**
- Many-to-one with `device`
- Many-to-one with `analysis_session`
- One-to-many with `detected_violations`

**Cascade Behavior:**
- DELETE device → CASCADE to log_entries
- DELETE session → SET NULL for analysis_session_id
- DELETE log_entry → SET NULL for violations

### 4. detected_violations

Stores detected MED-THERM-2026 regulatory violations.

**Columns:**
- `id` (UUID, PK) - Violation identifier
- `device_id` (UUID, FK, NULLABLE) - Associated device
- `analysis_session_id` (UUID, FK, NULLABLE) - Analysis session
- `log_entry_id` (UUID, FK, NULLABLE) - Related log entry
- `reg_code` (TEXT, NOT NULL) - MED-THERM-2026 rule code (e.g., "REG-TEMP-1")
- `severity` (ENUM, NOT NULL) - Severity: CRITICAL, HIGH, MEDIUM, LOW, INFO
- `status` (ENUM, NOT NULL) - Violation status: OPEN, ACKNOWLEDGED, RESOLVED
- `description` (TEXT, NULLABLE) - Violation description
- `evidence` (JSONB, NULLABLE) - Violation evidence data
- `risk_score` (FLOAT, NULLABLE) - Calculated risk score
- `detected_at` (DATETIME, NOT NULL) - Detection timestamp
- `resolved_at` (DATETIME, NULLABLE) - Resolution timestamp
- `created_at` (DATETIME, NOT NULL) - Record creation timestamp
- `updated_at` (DATETIME, NOT NULL) - Last update timestamp

**Indexes:**
- `idx_violations_device_id` - Device lookup
- `idx_violations_analysis_session_id` - Session lookup
- `idx_violations_log_entry_id` - Log entry lookup
- `idx_violations_reg_code` - Rule code filtering
- `idx_violations_severity` - Severity filtering
- `idx_violations_status` - Status filtering
- `idx_violations_device_id_detected_at` - Device time-range queries

**Relationships:**
- Many-to-one with `device`
- Many-to-one with `analysis_session`
- Many-to-one with `log_entry`

**Cascade Behavior:**
- DELETE device/session/log_entry → SET NULL for respective FKs

### 5. compliance_reports

Stores generated regulatory compliance reports.

**Columns:**
- `id` (UUID, PK) - Report identifier
- `device_id` (UUID, FK, NULLABLE) - Associated device
- `status` (ENUM, NOT NULL) - Report status: GENERATING, COMPLETED, FAILED
- `period_start` (DATETIME, NOT NULL) - Report period start
- `period_end` (DATETIME, NOT NULL) - Report period end
- `compliance_score` (FLOAT, NULLABLE) - Overall compliance score (0-100)
- `summary` (JSONB, NULLABLE) - Report summary data
- `report_path` (TEXT, NULLABLE) - Path to report file
- `generated_by` (TEXT, NULLABLE) - Report generator identifier
- `generated_at` (DATETIME, NOT NULL) - Generation timestamp
- `created_at` (DATETIME, NOT NULL) - Record creation timestamp
- `updated_at` (DATETIME, NOT NULL) - Last update timestamp

**Indexes:**
- `idx_reports_device_id` - Device lookup
- `idx_reports_status` - Status filtering
- `idx_reports_generated_at` - Time-range queries
- `idx_reports_device_id_period_start` - Device time-range queries

**Relationships:**
- Many-to-one with `device`

**Cascade Behavior:**
- DELETE device → SET NULL for device_id

### 6. audit_log

Immutable audit trail for regulatory compliance (REG-DATA-1).

**Columns:**
- `id` (UUID, PK) - Audit entry identifier
- `created_at` (DATETIME, NOT NULL) - Audit timestamp (no updated_at)
- `action` (ENUM, NOT NULL) - Action type: CREATE, READ, UPDATE, DELETE, LOGIN, EXPORT, GENERATE_REPORT
- `actor` (TEXT, NULLABLE) - User/system performing action
- `resource_type` (TEXT, NULLABLE) - Resource type (e.g., "device", "violation")
- `resource_id` (TEXT, NULLABLE) - Resource identifier
- `description` (TEXT, NULLABLE) - Action description
- `old_value` (JSONB, NULLABLE) - Previous state (for UPDATE)
- `new_value` (JSONB, NULLABLE) - New state (for CREATE/UPDATE)
- `request_context` (JSONB, NULLABLE) - Request metadata

**Indexes:**
- `idx_audit_log_created_at` - Time-range queries
- `idx_audit_log_action` - Action filtering
- `idx_audit_log_resource_type` - Resource type filtering
- `idx_audit_log_resource_type_resource_id` - Resource lookup

**Security Policies:**
- Row-Level Security (RLS) enabled
- SELECT policy: Allow all reads
- INSERT policy: Allow all inserts
- No UPDATE/DELETE policies (prevents modifications)

**Immutability Enforcement:**
- Database-level RLS policies prevent UPDATE/DELETE
- No `updated_at` column (only `created_at`)
- REG-DATA-1 compliance: Audit trail cannot be modified

## Enums

### DeviceStatus
- `ONLINE` - Device is currently active
- `OFFLINE` - Device is inactive
- `MAINTENANCE` - Device under maintenance
- `REGISTERED` - Device registered but not yet active

### AnalysisSessionStatus
- `PENDING` - Session queued for processing
- `COMPLETED` - Session completed successfully
- `FAILED` - Session failed

### LogType (ORM)
- `TELEMETRY` - Telemetry data
- `EVENT` - System events
- `ALERT` - Alert notifications
- `STATUS` - Status updates

### LogType (Pydantic - logs.py)
- `TEMP_READING` - Temperature sensor reading
- `FAN_SPEED` - Fan speed reading
- `VOLTAGE` - Voltage reading
- `HUMIDITY` - Humidity reading
- `BATTERY_LEVEL` - Battery level reading
- `DOOR_OPEN` - Door opened event
- `DOOR_CLOSE` - Door closed event
- `DEVICE_START` - Device started
- `ALARM_TRIGGERED` - Alarm activated
- `TEMP_WARNING` - Temperature warning
- `SENSOR_TIMEOUT` - Sensor timeout
- `TELEMETRY_SYNC_FAILED` - Telemetry sync failure
- `COOLING_RECOVERY_START` - Cooling recovery started

### Severity
- `CRITICAL` - Immediate action required (24 hours)
- `HIGH` - High priority (72 hours)
- `MEDIUM` - Medium priority (next maintenance)
- `LOW` - Low priority (monitor)
- `INFO` - Informational only

### ViolationStatus
- `OPEN` - Violation detected, not addressed
- `ACKNOWLEDGED` - Violation acknowledged by user
- `RESOLVED` - Violation resolved

### ReportStatus
- `GENERATING` - Report being generated
- `COMPLETED` - Report completed
- `FAILED` - Report generation failed

### AuditAction
- `CREATE` - Resource creation
- `READ` - Resource access
- `UPDATE` - Resource modification
- `DELETE` - Resource deletion
- `LOGIN` - User login
- `EXPORT` - Data export
- `GENERATE_REPORT` - Report generation

## Inputs

### Database Configuration

```python
# From app.config.settings
database_url = "postgresql://user:pass@host:port/dbname"
database_url_async = "postgresql+asyncpg://user:pass@host:port/dbname"
```

### ORM Model Inputs

```python
# Device creation
device = Device(
    name="CRYOSAFE-001",
    model="CS-2000",
    serial_number="CS-2000-001234",
    status=DeviceStatus.REGISTERED
)

# Log entry creation
log_entry = LogEntry(
    device_id=device.id,
    timestamp=datetime.now(),
    log_type=LogType.TELEMETRY,
    source="PRIMARY",
    payload={"temperature": 5.2, "sensor_id": "PRIMARY"}
)

# Violation creation
violation = DetectedViolation(
    device_id=device.id,
    reg_code="REG-TEMP-1",
    severity=Severity.CRITICAL,
    status=ViolationStatus.OPEN,
    description="Temperature reading 9.2°C exceeds maximum 8°C",
    evidence={"entry_index": 123, "raw_value": "9.2"},
    risk_score=0.95
)

# Audit log creation
audit_entry = AuditLog(
    action=AuditAction.CREATE,
    actor="system",
    resource_type="device",
    resource_id=str(device.id),
    description="Device registered",
    new_value={"name": "CRYOSAFE-001", "status": "registered"}
)
```

### Pydantic Model Inputs

```python
# Log entry (Pydantic)
log_entry = LogEntry(
    timestamp=datetime.now(),
    log_type=LogType.TEMP_READING,
    raw_value="5.2",
    parsed_value=5.2,
    sensor_id="PRIMARY"
)

# Finding (Pydantic)
finding = Finding(
    rule_id="REG-TEMP-1",
    rule_description="Temperature readings within 2-8°C range",
    category="temperature",
    severity=Severity.CRITICAL,
    passed=False,
    message="Temperature reading 9.2°C exceeds maximum 8°C",
    evidence=[...],
    timestamp=datetime.now(),
    remediation_hint="Verify cooling system is operating correctly"
)
```

## Outputs

### ORM Model Outputs

```python
# Query device
device = session.query(Device).filter_by(serial_number="CS-2000-001234").first()

# Query log entries with time range
logs = session.query(LogEntry).filter(
    LogEntry.device_id == device.id,
    LogEntry.timestamp >= start_time,
    LogEntry.timestamp <= end_time
).order_by(LogEntry.timestamp).all()

# Query violations by severity
violations = session.query(DetectedViolation).filter(
    DetectedViolation.device_id == device.id,
    DetectedViolation.severity == Severity.CRITICAL,
    DetectedViolation.status == ViolationStatus.OPEN
).all()

# Query compliance reports
reports = session.query(ComplianceReport).filter(
    ComplianceReport.device_id == device.id,
    ComplianceReport.status == ReportStatus.COMPLETED
).order_by(ComplianceReport.generated_at.desc()).all()

# Query audit log
audit_entries = session.query(AuditLog).filter(
    AuditLog.resource_type == "device",
    AuditLog.resource_id == str(device.id)
).order_by(AuditLog.created_at.desc()).all()
```

### Pydantic Model Outputs

```python
# Compliance report (Pydantic)
compliance_report = ComplianceReport(
    device_id="CRYOSAFE-001",
    analyzed_at=datetime.now(),
    total_entries=1000,
    time_range_start=start_time,
    time_range_end=end_time,
    summary={
        "temperature": CategorySummary(passed=8, failed=2, total=10),
        "sensor": CategorySummary(passed=5, failed=1, total=6)
    },
    findings=[...],
    passed_count=13,
    failed_count=3,
    critical_count=2
)

# JSON serialization
report_json = compliance_report.model_dump_json()
```

## API Endpoints

### Database Access Patterns

The database schema module does not directly expose API endpoints. Instead, it provides data models and session management used by other API modules:

**API modules using database schema:**
- `api/validate.py` - Uses LogEntry, ComplianceReport models
- `api/reports.py` - Uses AggregatedComplianceReport models
- `api/logs.py` - Uses LogEntry models
- `api/ai.py` - Uses Finding models

**Session Management:**

```python
from app.database import get_db, get_async_db

# Sync session (for non-async operations)
def some_function():
    db = next(get_db())
    try:
        device = db.query(Device).first()
        # ... operations ...
        db.commit()
    finally:
        db.close()

# Async session (for async operations)
async def some_async_function():
    async for session in get_async_db():
        devices = await session.execute(
            select(Device).where(Device.status == DeviceStatus.ONLINE)
        )
        # ... operations ...
        await session.commit()
```

## MED-THERM-2026 Regulation Mapping

### REG-DATA-1: Audit Trail Immutability

**Requirement:** Audit trails must be immutable and tamper-evident.

**Implementation:**
- `audit_log` table has no `updated_at` column (only `created_at`)
- Row-Level Security (RLS) policies prevent UPDATE/DELETE operations
- Database-level enforcement (cannot bypass from application)
- All CRUD operations logged with `AuditAction` enum

**Table:** `audit_log`

**Columns:**
- `action` - Tracks CREATE, READ, UPDATE, DELETE, LOGIN, EXPORT, GENERATE_REPORT
- `actor` - Identifies user/system performing action
- `resource_type` + `resource_id` - Identifies affected resource
- `old_value` + `new_value` - Captures state changes
- `request_context` - Captures request metadata

**Compliance:** ✅ Fully compliant

### REG-TEMP-1: Temperature Range Monitoring

**Requirement:** Temperature readings must be within 2-8°C range.

**Implementation:**
- `LogEntry.log_type` includes `TEMP_READING`
- `DetectedViolation.reg_code` stores "REG-TEMP-1"
- `DetectedViolation.severity` classified as CRITICAL/HIGH based on violation count
- Evidence stored in `DetectedViolation.evidence` (JSONB)

**Tables:** `log_entries`, `detected_violations`

**Compliance:** ✅ Fully compliant

### REG-SENS-1: Sensor Redundancy

**Requirement:** Sensor redundancy must be maintained with dual sensors.

**Implementation:**
- `LogEntry.sensor_id` identifies PRIMARY/SECONDARY sensors
- `DetectedViolation.reg_code` stores "REG-SENS-1"
- Severity classified as CRITICAL (dual failure) or HIGH (single failure)
- Sensor timeout events tracked in `log_entries`

**Tables:** `log_entries`, `detected_violations`

**Compliance:** ✅ Fully compliant

### REG-ALARM-1: Alarm Activation

**Requirement:** Alarms must activate within 2 minutes of excursion.

**Implementation:**
- `LogEntry.log_type` includes `ALARM_TRIGGERED`
- `DetectedViolation.reg_code` stores "REG-ALARM-1"
- Severity classified as HIGH
- Alarm events tracked in `log_entries`

**Tables:** `log_entries`, `detected_violations`

**Compliance:** ✅ Fully compliant

### REG-DATA-2: Telemetry Continuity

**Requirement:** Telemetry data gaps must not exceed 90 seconds.

**Implementation:**
- `LogEntry.timestamp` enables gap detection
- `DetectedViolation.reg_code` stores "REG-DATA-2"
- Index `idx_log_entries_device_timestamp` optimizes gap analysis
- Time-series queries supported via BRIN/B-tree indexes

**Tables:** `log_entries`, `detected_violations`

**Compliance:** ✅ Fully compliant

### Severity Classification Matrix

| MED-THERM-2026 Rule | Database Severity | Response Time |
|---------------------|-------------------|---------------|
| REG-TEMP-1 (>3 violations) | CRITICAL | 24 hours |
| REG-TEMP-2 (any violation) | CRITICAL | 24 hours |
| REG-SENS-1 (dual failure) | CRITICAL | 24 hours |
| REG-TEMP-1 (1-3 violations) | HIGH | 72 hours |
| REG-SENS-1 (single failure) | HIGH | 72 hours |
| REG-ALARM-1 | HIGH | 72 hours |
| REG-TEMP-3 | HIGH | 72 hours |
| REG-SENS-3 | HIGH | 72 hours |
| REG-TEMP-4 | MEDIUM | Next maintenance |
| REG-DATA-2 | MEDIUM | Next maintenance |
| REG-ALARM-2 | MEDIUM | Next maintenance |
| REG-ALARM-3 | MEDIUM | Next maintenance |
| REG-SENS-2 | INFO | Monitor only |

## Important Implementation Decisions

### 1. UUID Primary Keys

**Decision:** Use UUID v4 as primary keys for all tables.

**Rationale:**
- Better for distributed systems (no coordination needed)
- Avoids ID enumeration security concerns (non-guessable)
- Consistent pattern across all tables
- PostgreSQL UUID type with `gen_random_uuid()` server default

**Trade-offs:**
- Slightly larger storage (16 bytes vs 8 bytes for BIGINT)
- Slightly slower INSERT performance (acceptable for compliance platform)
- Index fragmentation potential (mitigated by UUID v7 in future)

### 2. Snake_case Naming Convention

**Decision:** Use snake_case for table and column names.

**Rationale:**
- PostgreSQL convention
- Consistent with SQLAlchemy's typical usage
- Avoids case-sensitivity issues in PostgreSQL
- SQL best practice

**Alternatives considered:**
- PascalCase - Not standard in SQL databases
- camelCase - Can cause case-sensitivity issues

### 3. Time-Series Indexing Strategy


**Decision:** B-tree indexes on `log_entries.timestamp` and composite `(device_id, timestamp)`.

**Rationale:**
- B-tree indexes provide efficient time-range queries
- Composite index optimizes device-specific time-range queries
- Supports both cross-device and per-device time-series analysis
- Sufficient for current scale (future BRIN/partitioning available)

**Trade-offs:**
- Larger index size compared to BRIN
- Slower bulk ingest compared to BRIN
- Acceptable for initial deployment scale

**Future optimization:** BRIN indexes for very large datasets

### 4. Audit Log Immutability

**Decision:** Database-level enforcement via Row-Level Security (RLS) policies.

**Implementation:**
- RLS enabled on `audit_log` table
- SELECT and INSERT policies allow all operations
- No UPDATE or DELETE policies (prevents modifications)
- No `updated_at` column (only `created_at`)

**Rationale:**
- REG-DATA-1 compliance requires immutable audit trails
- Database-level enforcement cannot be bypassed from application
- Tamper-evident by design

**Alternatives considered:**
- Application-only enforcement - Can be bypassed
- Triggers - More complex, same result

### 5. JSONB for Flexible Data

**Decision:** Use JSONB for `payload` (log_entries), `evidence` (violations), `summary` (reports), and audit log fields.

**Rationale:**
- Flexible schema for evolving data structures
- Efficient storage and querying (PostgreSQL JSONB)
- Supports complex nested data (evidence, config, etc.)
- JSONB operators for querying

**Trade-offs:**
- No schema validation at database level
- Relies on application-level validation (Pydantic models)
- Acceptable for compliance platform with strong API validation

### 6. Cascade Delete Strategy

**Decision:** Mixed cascade behavior based on data importance.

**Implementation:**
- `devices` → `log_entries`: CASCADE (logs are device-specific)
- `devices` → `analysis_sessions`: SET NULL (preserve session history)
- `devices` → `detected_violations`: SET NULL (preserve violation history)
- `devices` → `compliance_reports`: SET NULL (preserve report history)

**Rationale:**
- Log entries are device-specific, safe to cascade delete
- Violations and reports are regulatory artifacts, must be preserved
- Analysis sessions may have independent value

**Compliance impact:**
- Violations preserved even if device deleted (audit trail)
- Reports preserved for historical compliance tracking

### 7. Timestamp Handling

**Decision:** Use UTC timestamps with `TIMEZONE('utc', NOW())` server default.

**Implementation:**
- All timestamp columns use UTC
- Server defaults ensure consistency
- Application can set explicit values

**Rationale:**
- Consistent timezone handling across application
- Avoids timezone-related bugs
- MED-THERM-2026 requires accurate timestamping

### 8. Status Enums

**Decision:** Use PostgreSQL ENUM types for status fields.

**Implementation:**
- `device_status_enum`: ONLINE, OFFLINE, MAINTENANCE, REGISTERED
- `analysis_session_status_enum`: PENDING, COMPLETED, FAILED
- `severity_enum`: CRITICAL, HIGH, MEDIUM, LOW, INFO
- `violation_status_enum`: OPEN, ACKNOWLEDGED, RESOLVED
- `report_status_enum`: GENERATING, COMPLETED, FAILED
- `audit_action_enum`: CREATE, READ, UPDATE, DELETE, LOGIN, EXPORT, GENERATE_REPORT

**Rationale:**
- Type safety at database level
- Efficient storage (4 bytes vs VARCHAR)
- Clear documentation of valid values
- Consistent with SQLAlchemy enum handling

### 9. Dual ORM and Pydantic Models

**Decision:** Maintain both SQLAlchemy ORM models and Pydantic data models.

**Rationale:**
- SQLAlchemy ORM models for database operations
- Pydantic models for API request/response validation
- Type safety and validation at both layers
- Pydantic provides automatic JSON serialization

**Separation:**
- `models/orm.py` - SQLAlchemy models (Device, LogEntry, etc.)
- `models/findings.py` - Pydantic models (Finding, ComplianceReport)
- `models/logs.py` - Pydantic models (LogEntry)

### 10. Migration Strategy

**Decision:** Use Alembic for database migrations with explicit versioning.

**Implementation:**
- `0001_initial_schema.py` - Initial schema creation
- `0002_audit_log_immutability.py` - RLS policies for audit_log
- Both upgrade and downgrade paths defined

**Rationale:**
- Version-controlled schema changes
- Reproducible deployments
- Rollback capability
- Team collaboration support

## Usage Examples

### Creating a Device

```python
from app.database import get_db
from app.models.orm import Device, DeviceStatus

def create_device(name: str, serial_number: str):
    db = next(get_db())
    try:
        device = Device(
            name=name,
            serial_number=serial_number,
            status=DeviceStatus.REGISTERED
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        return device
    finally:
        db.close()

device = create_device("CRYOSAFE-001", "CS-2000-001234")
```

### Ingesting Log Entries

```python
from datetime import datetime
from app.database import get_db
from app.models.orm import LogEntry, LogType

def ingest_log_entries(device_id: uuid.UUID, logs: List[dict]):
    db = next(get_db())
    try:
        for log in logs:
            entry = LogEntry(
                device_id=device_id,
                timestamp=datetime.fromisoformat(log["timestamp"]),
                log_type=LogType(log["log_type"]),
                source=log.get("source"),
                payload=log.get("payload")
            )
            db.add(entry)
        db.commit()
    finally:
        db.close()
```

### Querying Violations

```python
from app.database import get_db
from app.models.orm import DetectedViolation, Severity, ViolationStatus

def get_open_critical_violations(device_id: uuid.UUID):
    db = next(get_db())
    try:
        violations = db.query(DetectedViolation).filter(
            DetectedViolation.device_id == device_id,
            DetectedViolation.severity == Severity.CRITICAL,
            DetectedViolation.status == ViolationStatus.OPEN
        ).order_by(DetectedViolation.detected_at.desc()).all()
        return violations
    finally:
        db.close()
```

### Creating Audit Log Entry

```python
from app.database import get_db
from app.models.orm import AuditLog, AuditAction

def log_audit_action(
    action: AuditAction,
    actor: str,
    resource_type: str,
    resource_id: str,
    old_value: dict = None,
    new_value: dict = None
):
    db = next(get_db())
    try:
        audit_entry = AuditLog(
            action=action,
            actor=actor,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value
        )
        db.add(audit_entry)
        db.commit()
    finally:
        db.close()
```

### Async Query Example

```python
from sqlalchemy import select
from app.database import get_async_db
from app.models.orm import Device, DeviceStatus

async def get_online_devices():
    async for session in get_async_db():
        result = await session.execute(
            select(Device).where(Device.status == DeviceStatus.ONLINE)
        )
        devices = result.scalars().all()
        return devices
```

## Database Migration

### Running Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Upgrade to latest
alembic upgrade head

# Downgrade one step
alembic downgrade -1

# Downgrade to specific version
alembic downgrade 0001

# View current version
alembic current

# View migration history
alembic history
```

### Migration Files

**0001_initial_schema.py:**
- Creates all tables
- Creates all ENUM types
- Creates all indexes
- Creates foreign key constraints

**0002_audit_log_immutability.py:**
- Enables RLS on `audit_log` table
- Creates SELECT and INSERT policies
- Prevents UPDATE and DELETE operations
- Enforces REG-DATA-1 compliance

## Performance Considerations

### Index Strategy

| Table | Index | Purpose | Type |
|-------|-------||---------|------|
| devices | serial_number | Unique device lookup | B-tree (UNIQUE) |
| log_entries | timestamp | Time-range queries | B-tree |
| log_entries | device_id, timestamp | Device time-range queries | B-tree (composite) |
| detected_violations | device_id, detected_at | Device violation timeline | B-tree (composite) |
| compliance_reports | device_id, period_start | Device report history | B-tree (composite) |
| audit_log | created_at | Audit trail queries | B-tree |

### Query Optimization

1. **Time-series queries** use `idx_log_entries_device_timestamp` for efficient filtering
2. **Violation queries** use composite indexes for device + time filtering
3. **Audit log queries** use time-based indexes for chronological access
4. **Device lookups** use unique index on serial_number

### Storage Considerations

- UUID primary keys: 16 bytes per row
- JSONB columns: Variable size, efficient for nested data
- Timestamp columns: 8 bytes each
- ENUM columns: 4 bytes each

**Estimated row sizes:**
- `devices`: ~100 bytes
- `log_entries`: ~200 bytes (payload varies)
- `detected_violations`: ~300 bytes (evidence varies)
- `compliance_reports`: ~500 bytes (summary varies)
- `audit_log`: ~400 bytes (context varies)

## Dependencies

### Internal Modules

- `app.config` - Database configuration settings

### Python Packages

- `sqlalchemy` - ORM and database toolkit
- `asyncpg` - Async PostgreSQL driver
- `psycopg2` - Sync PostgreSQL driver
- `alembic` - Database migration tool
- `pydantic` - Data validation and serialization

### Database

- PostgreSQL 14+ with pgcrypto extension

## Security Considerations

### Row-Level Security (RLS)

**audit_log table:**
- RLS enabled
- SELECT policy: Allow all reads
- INSERT policy: Allow all inserts
- No UPDATE/DELETE policies (prevents modifications)

### Cascade Delete Protection

**Regulatory artifacts preserved:**
- Violations: SET NULL on device delete (preserve history)
- Reports: SET NULL on device delete (preserve history)
- Analysis sessions: SET NULL on device delete (preserve history)

### Audit Trail

**All operations logged:**
- CREATE, READ, UPDATE, DELETE actions tracked
- Actor identification (user/system)
- Resource tracking (type + ID)
- State capture (old_value, new_value)
- Request context (IP, headers, etc.)

## Future Enhancements

1. **BRIN Indexes** - For very large log_entries table
2. **Table Partitioning** - Time-based partitioning for log_entries
3. **Materialized Views** - Pre-computed compliance summaries
4. **Full-Text Search** - Search across audit_log descriptions
5. **Data Retention Policies** - Automated archival of old data
6. **Replication** - Read replicas for reporting queries
7. **Connection Pooling** - Advanced pool configuration
8. **Query Performance Monitoring** - pg_stat_statements integration

## References

- MED-THERM-2026 Regulatory Specification
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Alembic Documentation: https://alembic.sqlalchemy.org/
- Pydantic Documentation: https://docs.pydantic.dev/
