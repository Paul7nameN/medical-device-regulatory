## ADDED Requirements

### Requirement: Detected violation storage
The system SHALL persist detected regulatory violations with reference to MED-THERM-2026 REG-* codes and severity levels.

#### Scenario: Create violation record
- **WHEN** VLLM analysis or rule engine detects a compliance violation
- **THEN** a record is created in `detected_violations` with `reg_code`, `severity`, and violation details

#### Scenario: REG code reference
- **WHEN** storing a violation related to a specific regulation
- **THEN** `reg_code` field uses MED-THERM-2026 format (e.g., 'REG-TEMP-1', 'REG-DATA-1')

#### Scenario: Severity classification
- **WHEN** classifying violation impact
- **THEN** `severity` field uses enum: 'critical', 'high', 'medium', 'low', 'info'

### Requirement: Violation context and linking
The `detected_violations` table SHALL link to source data and track resolution status.

#### Scenario: Link to analysis session
- **WHEN** violation is detected during VLLM analysis
- **THEN** `analysis_session_id` foreign key references the originating session

#### Scenario: Link to log entry
- **WHEN** violation is detected from a specific log entry
- **THEN** `log_entry_id` foreign key references the source `log_entries` record

#### Scenario: Link to device
- **WHEN** violation belongs to a specific device
- **THEN** `device_id` foreign key references the associated device

#### Scenario: Track resolution
- **WHEN** a violation is acknowledged or resolved
- **THEN** `status` field transitions from 'open' to 'acknowledged' to 'resolved'

### Requirement: Violation details
The `detected_violations` table SHALL store detailed violation information for audit and reporting.

#### Scenario: Violation description
- **WHEN** recording a detected violation
- **THEN** `description` field stores human-readable details of the violation

#### Scenario: Evidence reference
- **WHEN** evidence supports the violation
- **THEN** `evidence` JSON field stores references to supporting data

#### Scenario: Detect timestamp
- **WHEN** violation is first detected
- **THEN** `detected_at` timestamp records the detection time

#### Scenario: Risk score
- **WHEN** assessing violation risk
- **THEN** `risk_score` (numeric 0-100) quantifies the risk level
