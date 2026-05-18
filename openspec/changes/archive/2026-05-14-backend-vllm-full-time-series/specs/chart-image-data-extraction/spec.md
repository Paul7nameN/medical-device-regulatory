## MODIFIED Requirements

### Requirement: Chart image time-series extraction
The system SHALL extract temperature time-series data from chart images analyzed by VLLM, enabling display in the Temperature page timeline. The backend VLLM analysis SHALL request and return the complete temperature time-series, not just violation points.

#### Scenario: Extract data_points from VLLM response
- **WHEN** VLLM analysis response includes a `data_points` or `time_series` array
- **THEN** each entry is converted to `TemperatureDataPoint` with timestamp and sensor values

#### Scenario: Fallback to violation timestamps
- **WHEN** VLLM response has `violations` but no full time-series
- **THEN** violation timestamp_start/timestamp_end and extracted_value create minimum data points

#### Scenario: Aggregated analysis from multiple sources
- **WHEN** both log files and chart images are uploaded
- **THEN** temperature data from both sources are merged in chronological order

#### Scenario: Prompt requests full time-series
- **WHEN** backend sends chart image to VLLM for analysis
- **THEN** the prompt explicitly requests extraction of ALL temperature readings, not just violations

#### Scenario: Backend returns data_points in response
- **WHEN** VLLM returns `data_points` array in its JSON response
- **THEN** backend extracts and returns these points in `ChartAnalysisResult.data_points`
