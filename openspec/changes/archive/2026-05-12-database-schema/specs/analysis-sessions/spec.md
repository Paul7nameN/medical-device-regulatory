## ADDED Requirements

### Requirement: Analysis session tracking
The system SHALL track VLLM analysis sessions with device association, session status, and timing information.

#### Scenario: Create analysis session
- **WHEN** a new VLLM analysis starts for a document/image
- **THEN** a record is created in `analysis_sessions` with `status = 'pending'` and `started_at` timestamp

#### Scenario: Associate session with device
- **WHEN** an analysis session is linked to a specific device
- **THEN** the `device_id` foreign key references the corresponding `devices` record

#### Scenario: Track session completion
- **WHEN** an analysis completes successfully or fails
- **THEN** `status` is updated ('completed'/'failed') and `completed_at` timestamp is set

### Requirement: Analysis configuration and results
The `analysis_sessions` table SHALL store VLLM configuration, input document reference, and result summary.

#### Scenario: Store configuration
- **WHEN** starting an analysis with specific VLLM parameters
- **THEN** `config` JSON field stores the VLLM provider, model, and parameters

#### Scenario: Store results reference
- **WHEN** analysis generates output
- **THEN** `result_summary` field stores key findings, and `result_path` points to full output

#### Scenario: Query sessions by device
- **WHEN** retrieving all analyses for a device
- **THEN** the query filters by `device_id` and orders by `started_at` DESC
