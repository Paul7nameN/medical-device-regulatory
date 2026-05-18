## 1. Database Setup & Base Configuration

- [x] 1.1 Verify SQLAlchemy declarative base exists in project
- [x] 1.2 Define UUID primary key base mixin for all models
- [x] 1.3 Define timestamp mixin (created_at, updated_at)

## 2. Core Entity Models

- [x] 2.1 Create `Device` SQLAlchemy model with: id (UUID), name, model, serial_number, status, last_seen_at, created_at, updated_at
- [x] 2.2 Create `AnalysisSession` SQLAlchemy model with: id (UUID), device_id (FK), status, config (JSONB), result_summary, result_path, started_at, completed_at, created_at
- [x] 2.3 Add foreign key relationship: AnalysisSession.device_id -> Device.id

## 3. Log Storage Model with Time-Series Optimization

- [x] 3.1 Create `LogEntry` SQLAlchemy model with: id (UUID), device_id (FK), analysis_session_id (FK, nullable), timestamp, log_type, source, payload (JSONB), created_at
- [x] 3.2 Add log_type enum: telemetry, event, alert, status
- [x] 3.3 Add foreign key relationships for device_id and analysis_session_id

## 4. Violation Tracking Model

- [x] 4.1 Create `DetectedViolation` SQLAlchemy model with: id (UUID), device_id (FK), analysis_session_id (FK), log_entry_id (FK), reg_code, severity, status, description, evidence (JSONB), risk_score, detected_at, resolved_at, created_at
- [x] 4.2 Add severity enum: critical, high, medium, low, info
- [x] 4.3 Add status enum: open, acknowledged, resolved
- [x] 4.4 Add foreign key relationships for device_id, analysis_session_id, log_entry_id

## 5. Compliance Reporting Model

- [x] 5.1 Create `ComplianceReport` SQLAlchemy model with: id (UUID), device_id (FK), status, period_start, period_end, compliance_score, summary (JSONB), report_path, generated_by, generated_at, created_at
- [x] 5.2 Add status enum: generating, completed, failed
- [x] 5.3 Add foreign key relationship for device_id

## 6. Immutable Audit Log Model (REG-DATA-1)

- [x] 6.1 Create `AuditLog` SQLAlchemy model with: id (UUID), action, actor, resource_type, resource_id, description, old_value (JSONB), new_value (JSONB), request_context (JSONB), created_at
- [x] 6.2 Add action enum: create, read, update, delete, login, export, generate_report
- [x] 6.3 Ensure model has no updated_at column (append-only pattern)

## 7. Database Indexes

- [x] 7.1 Add B-tree index on Device(serial_number) for unique lookups
- [x] 7.2 Add composite B-tree index on LogEntry(device_id, timestamp) for time-series queries
- [x] 7.3 Add B-tree index on LogEntry(timestamp) for cross-device time queries
- [x] 7.4 Add B-tree indexes on DetectedViolation(device_id, detected_at), DetectedViolation(reg_code), DetectedViolation(severity)
- [x] 7.5 Add B-tree indexes on ComplianceReport(device_id, period_start), ComplianceReport(generated_at)
- [x] 7.6 Add B-tree index on AuditLog(created_at) for audit queries
- [x] 7.7 Add B-tree indexes on AnalysisSession(device_id, started_at)

## 8. Alembic Migrations

- [x] 8.1 Create initial Alembic migration for all tables and foreign keys
- [x] 8.2 Add CREATE INDEX statements to migration for all indexes defined above
- [x] 8.3 Add migration for PostgreSQL ENUM types (log_type, severity, status, action)
- [ ] 8.4 Test migration upgrade and downgrade paths

## 9. Audit Log Immutability Enforcement (REG-DATA-1)

- [x] 9.1 Create separate Alembic migration for audit_log RLS policy
- [ ] 9.2 Add SQL: REVOKE UPDATE, DELETE ON audit_log FROM app_user (requires specific user role setup)
- [x] 9.3 RLS policies for audit_log
- [x] 9.4 Add SQL: ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
- [x] 9.5 Add SQL: CREATE POLICY audit_log_select ON audit_log FOR SELECT USING (true);
- [x] 9.6 Add SQL: CREATE POLICY audit_log_insert ON audit_log FOR INSERT WITH CHECK (true);
- [x] 9.7 Ensure no UPDATE/DELETE policies exist for audit_log (RLS defaults to deny; no update/delete policies created)

## 10. Model Validation & Basic Tests

- [x] 10.1 Verify all models have correct column types and constraints
- [ ] 10.2 Test that foreign key relationships work correctly (requires running test suite)
- [ ] 10.3 Verify that JSONB columns support dictionary operations (requires running test suite)
- [ ] 10.4 Test that UUIDs are auto-generated on insert (requires running test suite)
