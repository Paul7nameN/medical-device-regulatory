## ADDED Requirements

### Requirement: User can upload constraints documents
The system SHALL accept regulatory constraints documents alongside log files and images during upload.

#### Scenario: Detect constraints file by pattern
- **WHEN** user uploads a `.txt` or `.md` file
- **AND** filename contains keywords like "constraint", "regulatory", "rule", "standard", "MED-THERM"
- **OR** file content contains `REG-` patterns
- **THEN** system classifies it as a `CONSTRAINTS_DOCUMENT`

#### Scenario: Log file vs constraints differentiation
- **WHEN** uploaded file contains timestamp patterns like `YYYY-MM-DD HH:MM:SS`
- **AND** contains log type keywords like `TEMP_READING`, `DOOR_OPEN`, `ALARM`
- **THEN** system classifies it as a `LOG_FILE`, not constraints

### Requirement: AI extracts structured rules from text
The system SHALL use LLM to extract structured regulatory rules from unstructured constraint documents.

#### Scenario: Successful rule extraction
- **WHEN** a valid constraints document is provided
- **AND** AI is enabled (`MODELARK_API_KEY` configured)
- **THEN** LLM returns a JSON array of rules with: `id`, `name`, `category`, `description`, `type`, `severity`, `thresholds`

#### Scenario: Extraction with partial confidence
- **WHEN** LLM cannot confidently interpret some rules
- **THEN** those rules are marked with `confidence < 1.0`
- **AND** include `extraction_notes` field explaining ambiguity

#### Scenario: AI not configured fallback
- **WHEN** constraints document is uploaded but AI is not enabled
- **THEN** system returns error explaining that `MODELARK_API_KEY` is required for rule extraction

### Requirement: Rule validation schema
Extracted rules SHALL conform to a defined schema that supports multiple rule types.

#### Scenario: Threshold range rule
- **WHEN** rule type is `threshold_range`
- **THEN** schema includes: `field`, `min`, `max`, `unit`

#### Scenario: Duration limit rule
- **WHEN** rule type is `duration_limit`
- **THEN** schema includes: `max_duration_seconds`, `applies_to_out_of_range`

#### Scenario: Frequency/count rule
- **WHEN** rule type is `frequency_limit`
- **THEN** schema includes: `max_count`, `time_window_seconds`, `event_type`

#### Scenario: Inspection-only rule
- **WHEN** rule requires physical/visual inspection (cannot validate from logs)
- **THEN** `data_source = "inspection"` and `inspection_hint` field provides guidance
