## ADDED Requirements

### Requirement: Dual rule source support
The `RegulatoryEngine` SHALL support validation from both: (1) hardcoded rules, (2) dynamically extracted rules.

#### Scenario: Custom rules provided
- **WHEN** an analysis session has `extracted_rules` in config
- **THEN** validation runs against the custom extracted rules

#### Scenario: Fallback to default rules
- **WHEN** no custom rules are provided
- **THEN** validation uses the built-in hardcoded rules (MED-THERM-2026)

#### Scenario: Merge both rule sets (optional)
- **WHEN** user explicitly requests "default + custom" mode
- **THEN** both rule sets run and findings are merged with source attribution

### Requirement: Executable dynamic rules
Extracted rules with `confidence = 1.0` SHALL be executable against log data for supported rule types.

#### Scenario: Execute threshold range rule
- **WHEN** rule type is `threshold_range` with `field = "temperature"`
- **AND** logs contain `TEMP_READING` entries
- **THEN** system validates each reading against `min`/`max` thresholds
- **AND** creates findings for violations

#### Scenario: Execute frequency limit rule
- **WHEN** rule type is `frequency_limit` with `event_type = "door"`
- **AND** logs contain `DOOR_OPEN` entries
- **THEN** system counts events within sliding time windows
- **AND** creates warning if count exceeds `max_count`

### Requirement: Non-executable rule handling
Rules that cannot be validated from logs alone SHALL be clearly indicated.

#### Scenario: Inspection-only rules
- **WHEN** rule has `data_source = "inspection"`
- **THEN** system creates an info finding
- **AND** sets `needs_visual_verification = true`
- **AND** includes the `inspection_hint` text

#### Scenario: Low confidence rules
- **WHEN** rule has `confidence < 0.7`
- **THEN** system does NOT execute it automatically
- **AND** displays it in UI with "Needs review" indicator
