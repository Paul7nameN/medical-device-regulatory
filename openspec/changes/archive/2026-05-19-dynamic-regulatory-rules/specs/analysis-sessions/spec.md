## MODIFIED Requirements

### Requirement: Analysis configuration and results
The `analysis_sessions` table SHALL store VLLM configuration, input document reference, result summary, extracted time-series data when available, AND regulatory ruleset information.

#### Scenario: Store configuration
- **WHEN** starting an analysis with specific VLLM parameters
- **THEN** `config` JSON field stores the VLLM provider, model, and parameters

#### Scenario: Store results reference
- **WHEN** analysis generates output
- **THEN** `result_summary` field stores key findings, and `result_path` points to full output

#### Scenario: Query sessions by device
- **WHEN** retrieving all analyses for a device
- **THEN** the query filters by `device_id` and orders by `started_at` DESC

#### Scenario: Include time-series in results
- **WHEN** chart image analysis returns temperature readings
- **THEN** extracted data points are included alongside violation findings

#### Scenario: API response includes data_points field
- **WHEN** returning `ChartAnalysisResult` from `/api/ai/analyze-chart`
- **THEN** the response includes `result.data_points` array when available

#### Scenario: Store extracted rules in config
- **WHEN** rules are extracted from a constraints document
- **THEN** `config.extracted_rules` JSON array stores the rule set
- **AND** `config.ruleset_metadata` stores: filename, extraction timestamp, model used, extraction confidence

#### Scenario: Rules available when loading historical analysis
- **WHEN** loading an analysis session from history
- **THEN** the extracted rules (if any) are available in the API response
- **AND** UI can display "From custom rules" vs "From MED-THERM-2026 default"
