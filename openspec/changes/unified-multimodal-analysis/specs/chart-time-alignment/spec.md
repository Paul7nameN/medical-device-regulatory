## ADDED Requirements

### Requirement: Chart time alignment service
The system SHALL map chart image relative time (axis labels, elapsed time) to absolute timestamps using multiple methods with confidence tracking.

#### Scenario: Alignment method priority
- **WHEN** aligning a chart and log data is available
- **THEN** pattern matching is attempted first (highest confidence if matched), followed by LLM extraction

#### Scenario: LLM extraction of time range
- **WHEN** VLLM analyzes chart image and alignment is needed
- **THEN** the prompt explicitly asks: "What date and time range does this chart cover? Extract any visible dates, times, or duration indicators."

#### Scenario: Pattern matching against logs
- **WHEN** both chart data points and log temperature readings are available
- **THEN** system searches for matching temperature curve patterns to determine alignment offset

#### Scenario: Pattern match confidence calculation
- **WHEN** pattern matching finds a candidate alignment
- **THEN** confidence is calculated based on: curve correlation coefficient (>0.9 = high), number of matching inflection points, time range overlap

#### Scenario: Low confidence proceeds with warning
- **WHEN** all alignment methods yield confidence < 0.70
- **THEN** alignment proceeds using LLM result or relative time only, with `alignment.uncertain = true` flag

### Requirement: Chart alignment metadata tracking
The system SHALL track alignment method, confidence, and uncertainty for all chart-derived data points.

#### Scenario: Store alignment metadata
- **WHEN** chart is successfully aligned
- **THEN** `config._sources[].alignment` stores: method (pattern_matched/llm_extracted/manual), confidence score, start_time, end_time, uncertain flag

#### Scenario: Uncertain alignment banner
- **WHEN** `alignment.uncertain = true` or `alignment.confidence < 0.70`
- **THEN** frontend displays warning banner: "Chart time alignment is uncertain. Review correlated findings with caution."

#### Scenario: Relative time fallback
- **WHEN** no absolute time can be extracted
- **THEN** chart uses relative time (seconds from start) and correlation is limited to pattern-only without timestamp matching

### Requirement: Aligned data points mapping
Each chart-derived temperature reading SHALL have an absolute or relative timestamp after alignment.

#### Scenario: Map all data points
- **WHEN** chart alignment completes
- **THEN** every `TemperatureReading` from chart has `timestamp` field populated (absolute if aligned, relative fallback otherwise)

#### Scenario: Data point source tracking
- **WHEN** displaying or storing chart-derived data
- **THEN** `source = "chart_image"` field clearly distinguishes from log-derived readings

#### Scenario: Alignment confidence propagation
- **WHEN** chart has uncertain alignment
- **THEN** all correlated findings based on this chart have reduced base confidence (multiplied by alignment confidence)
