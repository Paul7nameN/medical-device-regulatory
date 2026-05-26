## MODIFIED Requirements

### Requirement: Chart image time-series extraction
The system SHALL extract temperature time-series data from chart images analyzed by VLLM, enabling display in the Temperature page timeline with proper time alignment to log data. The backend VLLM analysis SHALL request and return the complete temperature time-series, not just violation points.

#### Scenario: Extract data_points from VLLM response
- **WHEN** VLLM analysis response includes a `data_points` or `time_series` array
- **THEN** each entry is converted to `TemperatureDataPoint` with timestamp and sensor values

#### Scenario: Fallback to violation timestamps
- **WHEN** VLLM response has `violations` but no full time-series
- **THEN** violation timestamp_start/timestamp_end and extracted_value create minimum data points

#### Scenario: Aggregated analysis from multiple sources with alignment
- **WHEN** both log files and chart images are uploaded in unified batch
- **THEN** temperature data from both sources are aligned to absolute timeline and merged in chronological order, with alignment confidence tracked

#### Scenario: Prompt requests full time-series
- **WHEN** backend sends chart image to VLLM for analysis
- **THEN** the prompt explicitly requests extraction of ALL temperature readings, not just violations

#### Scenario: Backend returns data_points in response
- **WHEN** VLLM returns `data_points` array in its JSON response
- **THEN** backend extracts and returns these points in `ChartAnalysisResult.data_points`

### Requirement: Temperature data source tracking
The system SHALL track the source of temperature data points (log_file vs chart_image) along with alignment confidence for chart-derived points.

#### Scenario: Mark image-extracted points
- **WHEN** temperature data originates from image analysis
- **THEN** a source field indicates "chart_image" for traceability

#### Scenario: UI indication of data source
- **WHEN** displaying temperature chart with mixed sources
- **THEN** visual indicators distinguish log-extracted vs image-extracted data

#### Scenario: Track alignment confidence per chart
- **WHEN** chart is aligned to log timeline
- **THEN** `alignment.confidence` score is stored and propagated to correlation engine

#### Scenario: Uncertain alignment visual indicator
- **WHEN** chart alignment confidence < 0.70
- **THEN** all chart-derived points in timeline show "uncertain" visual treatment

## ADDED Requirements

### Requirement: Chart time alignment prompts
The system SHALL use specialized VLLM prompts to extract time range information from chart images when explicit date/time labels are ambiguous or relative.

#### Scenario: Alignment prompt queries time range
- **WHEN** backend needs chart alignment information
- **THEN** prompt includes: "What date and time range does this chart cover? Look for: axis labels with dates/times, duration indicators, any visible calendar or clock references."

#### Scenario: Alignment prompt queries x-axis type
- **WHEN** backend needs chart alignment information
- **THEN** prompt asks: "Is the x-axis showing absolute time (dates, times) or relative time (minutes since start, elapsed duration)?"

#### Scenario: Extracted alignment metadata
- **WHEN** VLLM returns alignment info
- **THEN** backend extracts: inferred_start_time, inferred_end_time, x_axis_type (absolute/relative), time_unit (minutes/hours), extraction_confidence
