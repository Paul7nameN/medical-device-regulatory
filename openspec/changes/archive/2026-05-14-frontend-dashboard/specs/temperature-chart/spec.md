## ADDED Requirements

### Requirement: Temperature timeline chart
The temperature chart SHALL visualize telemetry readings over time as a line chart with the 2-8°C safe range clearly indicated.

#### Scenario: Line chart display
- **WHEN** temperature data is loaded
- **THEN** line chart plots temperature readings on Y-axis against time on X-axis

#### Scenario: Safe range indicator
- **WHEN** viewing temperature chart
- **THEN** shaded band or horizontal lines indicate the 2-8°C safe temperature range

#### Scenario: Hover tooltip
- **WHEN** user hovers over a data point
- **THEN** tooltip shows exact timestamp, temperature value, and sensor source

### Requirement: Thermal excursion highlighting
The temperature chart SHALL visually highlight temperature excursions outside the 2-8°C safe range.

#### Scenario: Temperature above safe range
- **WHEN** temperature reading exceeds 8°C
- **THEN** that portion of the line displays in red with visual emphasis

#### Scenario: Temperature below safe range
- **WHEN** temperature reading is below 2°C
- **THEN** that portion of the line displays in blue with visual emphasis

#### Scenario: Excursion duration display
- **WHEN** user hovers over an excursion
- **THEN** tooltip indicates how long the excursion lasted

### Requirement: Multiple sensor support
The temperature chart SHALL support displaying data from multiple sensors simultaneously.

#### Scenario: Dual sensor display
- **WHEN** device has dual sensor data (per REG-SENS requirements)
- **THEN** chart shows two lines with different colors and legend

#### Scenario: Toggle sensor visibility
- **WHEN** user clicks sensor name in legend
- **THEN** corresponding line toggles visibility on chart

#### Scenario: Sensor discrepancy indicator
- **WHEN** two sensors differ by more than 0.5°C (REG-SENS-1)
- **THEN** chart highlights discrepancy with marker or annotation

### Requirement: Chart zoom and pan
The temperature chart SHALL support zooming into specific time ranges and panning across the dataset.

#### Scenario: Zoom to time range
- **WHEN** user drags to select a horizontal region
- **THEN** chart zooms to show only that time period in detail

#### Scenario: Pan across data
- **WHEN** zoomed in and user drags horizontally
- **THEN** chart pans left/right to show different time periods

#### Scenario: Reset view
- **WHEN** user clicks "Reset Zoom" button
- **THEN** chart returns to full dataset view

### Requirement: Responsive chart behavior
The temperature chart SHALL adapt to different viewport sizes while maintaining readability.

#### Scenario: Mobile chart view
- **WHEN** viewing on mobile (< 640px)
- **THEN** chart uses simplified X-axis with fewer ticks and larger tap targets

#### Scenario: Y-axis adaptive range
- **WHEN** data varies beyond 2-8°C range
- **THEN** Y-axis automatically adjusts to fit all data while keeping 2-8°C visible
