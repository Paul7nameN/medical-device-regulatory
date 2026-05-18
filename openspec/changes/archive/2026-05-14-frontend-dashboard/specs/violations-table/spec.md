## ADDED Requirements

### Requirement: Violations data table
The violations table SHALL display all detected violations with REG-* code, severity, description, and timestamp.

#### Scenario: Table columns
- **WHEN** viewing violations table
- **THEN** columns include: REG Code, Severity, Description, Timestamp, Device

#### Scenario: Sort by timestamp
- **WHEN** user clicks timestamp column header
- **THEN** table sorts violations by time (newest first or oldest first)

#### Scenario: Empty state
- **WHEN** no violations exist
- **THEN** table displays message: "No violations detected" with icon

### Requirement: Severity color coding
The violations table SHALL display severity levels with color coding: Critical (red), High (orange), Medium (yellow), Low (green), Info (blue).

#### Scenario: Critical severity display
- **WHEN** violation has severity "critical"
- **THEN** severity cell shows red background/badge with "Critical" text

#### Scenario: High severity display
- **WHEN** violation has severity "high"
- **THEN** severity cell shows orange background/badge with "High" text

#### Scenario: Medium severity display
- **WHEN** violation has severity "medium"
- **THEN** severity cell shows yellow background/badge with "Medium" text

#### Scenario: Low/Info severity display
- **WHEN** violation has severity "low" or "info"
- **THEN** severity cell shows green or blue badge respectively

### Requirement: Filtering capabilities
The violations table SHALL support filtering by severity level, REG category, and date range.

#### Scenario: Filter by severity
- **WHEN** user selects "Critical" from severity filter
- **THEN** table displays only critical violations

#### Scenario: Filter by REG category
- **WHEN** user selects "REG-TEMP" from category filter
- **THEN** table displays only violations related to thermal safety

#### Scenario: Filter by date range
- **WHEN** user selects start and end dates
- **THEN** table displays only violations within that time period

#### Scenario: Clear all filters
- **WHEN** user clicks "Clear Filters" button
- **THEN** all filters reset and full table displays

### Requirement: Violation detail view
The violations table SHALL allow users to view detailed information about a specific violation.

#### Scenario: View violation details
- **WHEN** user clicks on a violation row or "View Details" button
- **THEN** modal or expanded row shows full violation details, evidence, and remediation hint

#### Scenario: Evidence display
- **WHEN** viewing violation with evidence
- **THEN** evidence displays with source log entry reference and explanation

#### Scenario: REG code link
- **WHEN** user clicks on a REG-* code
- **THEN** tooltip or link shows full regulation description
