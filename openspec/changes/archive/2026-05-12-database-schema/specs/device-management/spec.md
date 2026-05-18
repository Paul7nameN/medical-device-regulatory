## ADDED Requirements

### Requirement: Device metadata storage
The system SHALL persist device metadata including unique identifier, name, model, serial number, and registration status.

#### Scenario: Create device record
- **WHEN** a new medical device is registered
- **THEN** a record is created in the `devices` table with UUID primary key

#### Scenario: Retrieve device by ID
- **WHEN** querying for a device by UUID
- **THEN** the system returns the complete device metadata

#### Scenario: Update device status
- **WHEN** updating a device's registration status
- **THEN** the `devices` table record is updated with the new status and `updated_at` timestamp

### Requirement: Device status tracking
The `devices` table SHALL include fields for operational status, last seen timestamp, and audit timestamps.

#### Scenario: Device operational status
- **WHEN** a device's operational status changes (online/offline/maintenance)
- **THEN** the `status` field is updated and `updated_at` is set to current time

#### Scenario: Last seen tracking
- **WHEN** a device reports data
- **THEN** the `last_seen_at` timestamp is updated
