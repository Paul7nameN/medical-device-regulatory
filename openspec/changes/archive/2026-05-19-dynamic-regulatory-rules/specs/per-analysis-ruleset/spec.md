## ADDED Requirements

### Requirement: Ruleset stored per analysis
Every analysis session SHALL have its associated ruleset stored alongside the results for audit trail purposes.

#### Scenario: Save extracted rules with session
- **WHEN** rules are successfully extracted from a constraints document
- **THEN** they are stored in `analysis_session.config.extracted_rules` JSON array
- **AND** `config.ruleset_metadata` stores: filename, extraction timestamp, model used, rule count

#### Scenario: Default rules indicator
- **WHEN** analysis uses built-in hardcoded rules
- **THEN** `config.used_default_rules = true`
- **AND** `config.ruleset_metadata.standard_name = "MED-THERM-2026"`

### Requirement: Ruleset available in API responses
All API endpoints returning analysis session data SHALL include the ruleset information.

#### Scenario: List endpoint includes ruleset info
- **WHEN** calling `GET /api/analysis` to list sessions
- **THEN** each item includes `has_custom_rules` boolean
- **AND** `ruleset_name` when applicable

#### Scenario: Detail endpoint returns full ruleset
- **WHEN** calling `GET /api/analysis/{session_id}`
- **THEN** response includes full `extracted_rules` array when present

### Requirement: Rules tab displays context-aware rules
The Rules tab in UI SHALL show rules relevant to the currently selected analysis session.

#### Scenario: Display custom rules from current analysis
- **WHEN** viewing an analysis that has `extracted_rules`
- **THEN** Rules tab shows the custom extracted rules
- **AND** indicates source: "Extracted from: [filename]"

#### Scenario: Show rules source attribution
- **WHEN** displaying findings/violations
- **THEN** each finding includes `from_default_rules` or `from_custom_rules` indicator
