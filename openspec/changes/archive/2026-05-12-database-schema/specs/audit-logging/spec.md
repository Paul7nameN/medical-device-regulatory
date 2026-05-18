## ADDED Requirements

### Requirement: Immutable audit log (REG-DATA-1)
The system SHALL maintain an immutable audit trail that cannot be modified or deleted once written, in compliance with REG-DATA-1 data integrity requirements.

#### Scenario: Append-only audit log
- **WHEN** an auditable action occurs
- **THEN** a new record is appended to `audit_log` table; no existing record can be updated or deleted

#### Scenario: Database-level immutability enforcement
- **WHEN** attempting UPDATE or DELETE on `audit_log` table
- **THEN** the database rejects the operation via permissions and row-level security policies

#### Scenario: REG-DATA-1 compliance
- **WHEN** auditor verifies data integrity
- **THEN** the `audit_log` records demonstrate that historical actions cannot be tampered with

### Requirement: Audit log entry structure
The `audit_log` table SHALL capture action details, actor, resource, and timestamp for each auditable event.

#### Scenario: Action type
- **WHEN** recording an audit event
- **THEN** `action` field describes the operation: 'create', 'read', 'update', 'delete', 'login', 'export', 'generate_report'

#### Scenario: Actor identification
- **WHEN** tracking who performed an action
- **THEN** `actor` field identifies the user or system component

#### Scenario: Resource reference
- **WHEN** an action affects a resource
- **THEN** `resource_type` and `resource_id` identify the affected entity

#### Scenario: Event timestamp
- **WHEN** an auditable event occurs
- **THEN** `created_at` timestamp records the event time with sub-second precision

### Requirement: Audit log detail
The `audit_log` table SHALL store sufficient detail for forensic analysis and compliance auditing.

#### Scenario: Before/After state
- **WHEN** an update operation is audited
- **THEN** `old_value` and `new_value` JSON fields capture the state change

#### Scenario: Description
- **WHEN** recording audit details
- **THEN** `description` field stores human-readable context

#### Scenario: Request context
- **WHEN** action originates from an API request
- **THEN** `request_context` JSON field stores IP address, user agent, and request ID

#### Scenario: Query by time range
- **WHEN** reviewing audit history
- **THEN** index on `created_at` enables efficient time-range queries
