# Dashboard Graphs section

## Requirement: Multi-metric graph selector

The dashboard SHALL expose a **Graphs** tab (replacing the Temperature-only tab) where users can select among available telemetry series for the active analysis.

### Metrics

- Temperature (existing chart with regulatory safe range)
- Humidity, voltage, fan speed, battery (from parsed log lines)

### Data sources

- Log file lines: `TEMP_READING`, `HUMIDITY`, `VOLTAGE`, `FAN_SPEED`, `BATTERY_LEVEL`
- Chart image analysis: temperature series merged into temperature metric

### Persistence

Analysis sessions SHALL store `telemetrySeries` in `_latest_analysis_data` when saving log-based analyses.
