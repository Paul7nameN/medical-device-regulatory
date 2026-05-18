## ADDED Requirements

### Requirement: Summary cards
The dashboard SHALL display summary cards showing violation counts grouped by REG category (REG-TEMP, REG-SENS, REG-ALARM, REG-DATA, etc.).

#### Scenario: Card display
- **WHEN** viewing dashboard
- **THEN** each REG category has a card showing total violations for that category

#### Scenario: Severity breakdown
- **WHEN** viewing a category card
- **THEN** card displays counts by severity: Critical, High, Medium, Low

#### Scenario: Click to filter
- **WHEN** user clicks on a category card
- **THEN** violations table filters to show only violations from that category

### Requirement: Compliance score display
The dashboard SHALL display an overall compliance score (0-100) based on passed vs. failed rules.

#### Scenario: Score calculation
- **WHEN** compliance data loads
- **THEN** score calculates as: (passed_rules / total_rules) * 100

#### Scenario: Visual score indicator
- **WHEN** displaying compliance score
- **THEN** score shows with color coding: green (≥90), yellow (70-89), orange (50-69), red (<50)

#### Scenario: Progress ring or gauge
- **WHEN** visualizing the score
- **THEN** circular progress indicator or gauge shows the compliance percentage visually

### Requirement: Pass/Fail summary
The dashboard SHALL provide a quick summary of passed and failed validation rules for each analysis session.

#### Scenario: Pass/fail counts
- **WHEN** viewing analysis results
- **THEN** display shows: X rules passed, Y rules failed

#### Scenario: Per-category breakdown
- **WHEN** expanding pass/fail section
- **THEN** breakdown shows pass/fail counts per REG category

#### Scenario: Rule list link
- **WHEN** user clicks on a rule count
- **THEN** navigates to detailed view showing which specific rules passed/failed

### Requirement: Report visualization
The dashboard SHALL provide visualizations of compliance reports including trend over time and comparisons.

#### Scenario: Time period selection
- **WHEN** viewing reports
- **THEN** user can select time range: Last 24h, Last 7d, Last 30d, Custom

#### Scenario: Trend chart
- **WHEN** report includes historical data
- **THEN** line chart shows compliance score trend over selected time period

#### Scenario: Severity distribution
- **WHEN** viewing report summary
- **THEN** pie or bar chart shows distribution of violations by severity level

#### Scenario: Category comparison
- **WHEN** viewing category breakdown
- **THEN** bar chart compares violation counts across all REG categories
