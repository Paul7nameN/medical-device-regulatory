### Requirement: Log entry storage
The system SHALL persist time-series log entries from devices including temperature readings, sensor data, and event logs.

#### Scenario: Insert log entry
- **WHEN** a device sends a telemetry reading or event
- **THEN** a record is inserted into `log_entries` with `device_id`, `timestamp`, `log_type`, and `payload`

#### Scenario: Log type categorization
- **WHEN** storing different log categories
- **THEN** `log_type` field distinguishes between 'telemetry', 'event', 'alert', and 'status' types

### Requirement: Time-series query optimization
The `log_entries` table SHALL be indexed for efficient time-range and device-specific queries.

#### Scenario: Query by device and time range
- **WHEN** querying logs for a device within a specific time window
- **THEN** the composite index on `(device_id, timestamp DESC)` is used for efficient retrieval

#### Scenario: Query across devices by time
- **WHEN** querying all logs within a time range across all devices
- **THEN** the index on `(timestamp DESC)` supports efficient time-range filtering

#### Scenario: High-volume insert performance
- **WHEN** inserting thousands of log entries per minute
- **THEN** BRIN indexes (where applicable) minimize insertion overhead compared to B-tree

### Requirement: Log data structure
The `log_entries` table SHALL support structured payloads and metadata fields.

#### Scenario: Structured JSON payload
- **WHEN** storing telemetry with multiple sensor values
- **THEN** `payload` JSONB field stores key-value pairs for flexible schema

#### Scenario: Source tracking
- **WHEN** logs come from different sources (sensor A, sensor B, system)
- **THEN** `source` field identifies the log origin

#### Scenario: Analysis session linking
- **WHEN** a log entry was processed by an analysis session
- **THEN** `analysis_session_id` foreign key links to `analysis_sessions`
