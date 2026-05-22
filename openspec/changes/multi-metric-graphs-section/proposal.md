# Multi-metric Graphs section

Replace the single Temperature tab with a **Graphs** section that lets users switch between telemetry series extracted from analysis data.

## Scope

- Temperature (existing chart + safe range)
- Humidity, voltage, fan speed, battery (from log lines)
- Chart image temperature merged into temperature series

## UI

- Tab renamed: Temperature → Graphs
- Metric selector buttons with point counts
- Generic line chart for non-temperature metrics

## Data

- `telemetrySeries` on analysis session (`_latest_analysis_data`)
- Backend extracts all numeric log types on save
