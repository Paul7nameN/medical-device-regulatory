## ADDED Requirements

### Requirement: Unified report structure
The system SHALL generate a single unified compliance report that incorporates findings from all modalities with source tracking and multi-modal confidence.

#### Scenario: Report includes source tracking
- **WHEN** generating unified report
- **THEN** each finding includes `data_sources` array listing which modalities contributed (e.g., ["logs"], ["logs", "chart"])

#### Scenario: Report includes confidence per finding
- **WHEN** generating unified report
- **THEN** each finding includes `confidence` score (0.0-1.0) calculated by correlation engine

#### Scenario: Report includes correlation insights section
- **WHEN** correlation insights exist
- **THEN** report has dedicated "Correlation Insights" section with narrative multi-modal observations

#### Scenario: Report includes discrepancies section
- **WHEN** conflicting_findings exist
- **THEN** report has dedicated "Discrepancies for Human Review" section with log-chart conflicts

### Requirement: Multi-modal timeline display
The system SHALL display a unified timeline combining events from all modalities with visual source indicators.

#### Scenario: Timeline includes all event types
- **WHEN** rendering unified timeline
- **THEN** includes: log events (TEMP_READING, DOOR_OPEN, ALARM), violations, chart-derived violations, correlation markers

#### Scenario: Visual source distinction
- **WHEN** displaying timeline events
- **THEN** different colors/icons distinguish: log-only events, chart-only events, multi-modal correlated events

#### Scenario: Timeline legend
- **WHEN** unified timeline is displayed
- **THEN** legend explains visual coding for sources and correlation status

### Requirement: Finding detail with evidence
Each finding detail SHALL show supporting evidence from all contributing modalities.

#### Scenario: Multi-modal evidence display
- **WHEN** user views finding with `data_sources = ["logs", "chart"]`
- **THEN** detail shows: log entry snippet, chart-extracted value at that time, alignment info, correlation confidence

#### Scenario: Log-only finding display
- **WHEN** user views finding with `data_sources = ["logs"]`
- **THEN** detail shows: log evidence, note "Chart data at this time: [no corresponding pattern | compliant reading]"

#### Scenario: Discrepancy review display
- **WHEN** user views discrepancy
- **THEN** side-by-side display: Log value/status vs Chart value/interpretation, with recommended actions

### Requirement: Alignment warning banner
When chart alignment is uncertain, the system SHALL display a prominent warning at the top of analysis results.

#### Scenario: Uncertain alignment warning
- **WHEN** `alignment.uncertain = true` or `alignment.confidence < 0.70`
- **THEN** warning banner displayed: "Chart time alignment is uncertain (confidence: X%). Correlated findings should be reviewed carefully."

#### Scenario: Warning dismissible
- **WHEN** warning banner is shown
- **THEN** user can dismiss it (dismissal not persisted - reappears on next view)

#### Scenario: Confidence reduction visibility
- **WHEN** alignment is uncertain
- **THEN** all chart-influenced findings show visibly reduced confidence (e.g., orange instead of green)
