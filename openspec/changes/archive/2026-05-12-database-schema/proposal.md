## Why

The MED-THERM Compliance Platform needs a PostgreSQL database schema to persist device data, analysis sessions, log entries, detected regulatory violations, compliance reports, and immutable audit trails. Without this foundational schema, no data persistence or regulatory compliance tracking is possible.

## What Changes

- Create `devices` table for medical device inventory and metadata
- Create `analysis_sessions` table for VLLM-based document/image analysis tracking
- Create `log_entries` table with time-series support for device telemetry and event logs
- Create `detected_violations` table with REG-* code reference and severity classification
- Create `compliance_reports` table for generated regulatory compliance reports
- Create `audit_log` immutable table for audit trails (REG-DATA-1 requirement)
- Add appropriate indexes for time-series queries on `log_entries` table

## Capabilities

### New Capabilities
- `device-management`: Device inventory and metadata persistence
- `analysis-sessions`: VLLM analysis session tracking
- `log-storage`: Time-series log entry storage with query optimization
- `violation-tracking`: Detected regulatory violation persistence with REG-* codes
- `compliance-reporting`: Compliance report generation storage
- `audit-logging`: Immutable audit trail for compliance (REG-DATA-1)

### Modified Capabilities
- None

## Impact

- New tables in PostgreSQL database
- Requires Alembic migrations for schema creation
- SQLAlchemy models need to be defined for all tables
- Time-series indexes will improve query performance on large log datasets
- Immutable `audit_log` table enables compliance with REG-DATA-1 data integrity requirements
