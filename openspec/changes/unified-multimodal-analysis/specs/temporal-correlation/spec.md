## ADDED Requirements

### Requirement: Temporal correlation engine
The system SHALL perform window-by-window temporal comparison between log-derived readings and chart-extracted values to detect matching patterns and conflicts.

#### Scenario: Time window comparison
- **WHEN** both log data and aligned chart data are available
- **THEN** system creates sliding time windows (default: ±60 seconds) and compares values from both sources

#### Scenario: Matching violation detection
- **WHEN** log shows violation at time T and aligned chart shows similar pattern within ±60 seconds
- **THEN** finding is marked as "multi-modal confirmed" with confidence boost

#### Scenario: Log-only violation
- **WHEN** log shows violation but chart shows no corresponding pattern at that time
- **THEN** finding stands (logs are ground truth) with note: "Chart at this time does not show corresponding violation"

#### Scenario: Chart-only potential issue
- **WHEN** chart suggests violation but logs show compliant values at that time
- **THEN** NOT added as violation (logs are ground truth), but added to "Discrepancies for Review" section with note: "Visual chart suggests potential issue not reflected in sensor logs"

### Requirement: Correlation confidence scoring
Each correlated finding SHALL have a confidence score that combines: log confidence, chart extraction confidence, and alignment confidence.

#### Scenario: Multi-modal confidence calculation
- **WHEN** finding has both log and chart evidence
- **THEN** confidence = min(log_confidence, chart_confidence) * alignment_confidence * 1.1 (boost for multi-modal)

#### Scenario: Log-only confidence
- **WHEN** finding has only log evidence
- **THEN** confidence = log_confidence (no boost, no penalty)

#### Scenario: Chart-only discrepancy
- **WHEN** chart suggests issue not in logs
- **THEN** discrepancy record includes: chart_value, chart_confidence, log_value, log_compliant = true

### Requirement: Correlation insights generation
The system SHALL generate narrative insights describing temporal relationships between events visible in multiple modalities.

#### Scenario: Door-event correlation
- **WHEN** log shows DOOR_OPEN at T1 followed by temperature spike at T2, and chart shows corresponding pattern
- **THEN** insight generated: "Door opening at [T1] correlated with temperature spike visible in both logs and chart. Temperature exceeded limit at [T2]."

#### Scenario: Recovery correlation
- **WHEN** both logs and chart show temperature returning to range after door event
- **THEN** insight includes: "Recovery time: [X] minutes (compliant with REG-TEMP-3)" or "[X] minutes (exceeds 3min limit)"

#### Scenario: Conflict insight
- **WHEN** discrepancy exists between log and chart
- **THEN** insight generated: "Potential discrepancy: Logs show compliant temperature [value] at [T], but chart visual suggests reading of [value]. Recommended: review chart alignment and sensor calibration."

### Requirement: Correlation results storage
Correlation results SHALL be stored in AnalysisSession.config for retrieval and display.

#### Scenario: Store correlated findings
- **WHEN** correlation engine completes
- **THEN** `config._correlation.correlated_findings` array contains all multi-modal matches

#### Scenario: Store conflicting findings
- **WHEN** discrepancies detected
- **THEN** `config._correlation.conflicting_findings` array contains all log-chart discrepancies

#### Scenario: Correlation summary
- **WHEN** storing results
- **THEN** `config._correlation.summary` contains: total_correlated, total_conflicting, avg_correlation_confidence
