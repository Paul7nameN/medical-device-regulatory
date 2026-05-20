## MODIFIED Requirements

### Requirement: Report summary and statistics
The `compliance_reports` table SHALL store summary statistics including violation counts by severity and regulation, AND ruleset attribution.

#### Scenario: Violation summary
- **WHEN** a report summarizes detected violations
- **THEN** `summary` JSON field contains counts by severity and reg_code

#### Scenario: Compliance score
- **WHEN** calculating compliance
- **THEN** `compliance_score` (numeric 0-100) represents the compliance percentage

#### Scenario: Report status
- **WHEN** tracking report generation lifecycle
- **THEN** `status` field tracks 'generating', 'completed', 'failed' states

#### Scenario: Include ruleset info in report
- **WHEN** generating a compliance report
- **THEN** report includes `ruleset_info` object with:
  - `used_default_rules`: boolean
  - `ruleset_name`: string (e.g., "MED-THERM-2026" or extracted filename)
  - `custom_rules_count`: number (if applicable)
