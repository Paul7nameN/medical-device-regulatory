## ADDED Requirements

### Requirement: Chart image time-series extraction
The system SHALL extract temperature time-series data from chart images analyzed by VLLM, enabling display in the Temperature page timeline.

#### Scenario: Extract data_points from VLLM response
- **WHEN** VLLM analysis response includes a `data_points` or `time_series` array
- **THEN** each entry is converted to `TemperatureDataPoint` with timestamp and sensor values

#### Scenario: Fallback to violation timestamps
- **WHEN** VLLM response has `violations` but no full time-series
- **THEN** violation timestamp_start/timestamp_end and extracted_value create minimum data points

#### Scenario: Aggregated analysis from multiple sources
- **WHEN** both log files and chart images are uploaded
- **THEN** temperature data from both sources are merged in chronological order

### Requirement: Temperature data source tracking
The system SHALL track the source of temperature data points (log_file vs chart_image).

#### Scenario: Mark image-extracted points
- **WHEN** temperature data originates from image analysis
- **THEN** a source field indicates "chart_image" for traceability

#### Scenario: UI indication of data source
- **WHEN** displaying temperature chart with mixed sources
- **THEN** visual indicators distinguish log-extracted vs image-extracted data
