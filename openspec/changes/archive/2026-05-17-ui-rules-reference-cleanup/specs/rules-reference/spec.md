## ADDED Requirements

### Requirement: Rules Reference tab in Dashboard
The system SHALL provide a dedicated Rules Reference tab in the Dashboard that displays all MED-THERM-2026 regulatory rules in a user-friendly format.

#### Scenario: Tab is visible in navigation
- **WHEN** user navigates to Dashboard
- **THEN** the "Rules" tab appears alongside Overview, Temperature, Violations, and History tabs

#### Scenario: All 21 rules displayed
- **WHEN** user clicks the "Rules" tab
- **THEN** all 21 regulatory rules are displayed (4 TEMP, 3 SENS, 3 ALARM, 3 DATA, 2 POWER, 2 COOL, 2 INS, 2 OPS)

---

### Requirement: Rule card structure
Each rule card SHALL display the following information: rule ID, category name, human-readable title, threshold value, severity, validation type, and detailed description.

#### Scenario: Operational rule card
- **WHEN** displaying a rule with data_source="LOGS"
- **THEN** card shows "Operational" badge and indicates it can be validated from device logs

#### Scenario: Inspection rule card
- **WHEN** displaying a rule with data_source="INSPECTION"
- **THEN** card shows "Inspection" badge and indicates it requires physical inspection or blueprint analysis

#### Scenario: Rule severity indicator
- **WHEN** displaying any rule
- **THEN** severity is indicated (CRITICAL, HIGH, MEDIUM, LOW, INFO) with appropriate visual styling

---

### Requirement: Rules filtering
The system SHALL allow filtering rules by category and by validation type.

#### Scenario: Filter by category
- **WHEN** user selects "TEMP" from the category filter dropdown
- **THEN** only REG-TEMP-1 through REG-TEMP-4 are displayed

#### Scenario: Filter by validation type - Operational
- **WHEN** user selects "Operational" from the type filter
- **THEN** only rules that can be validated from logs are displayed

#### Scenario: Filter by validation type - Inspection
- **WHEN** user selects "Inspection" from the type filter
- **THEN** only rules requiring physical inspection are displayed

#### Scenario: Combined filters
- **WHEN** user selects category="SENS" AND type="Operational"
- **THEN** only REG-SENS-1 and REG-SENS-3 are displayed (REG-SENS-2 requires inspection)

---

### Requirement: Rules data source
Rules data SHALL be stored as constants in the frontend codebase, synchronized with the official MED-THERM-2026 specification.

#### Scenario: Rules constants file exists
- **WHEN** the application builds
- **THEN** a TypeScript file contains all rule definitions

#### Scenario: Rule data structure
- **WHEN** accessing a rule object
- **THEN** it contains: id, category, categoryName, title, description, threshold, severity, validationType, source, confidence

---

### Requirement: UI History cleanup
The redundant "View History" button SHALL be removed from the Dashboard, keeping only the History tab.

#### Scenario: Button removed when multiple analyses exist
- **WHEN** user has multiple analyses loaded (analysisHistory.length > 1)
- **THEN** no "View History" button appears above the tabs

#### Scenario: History tab remains functional
- **WHEN** user clicks the "History" tab
- **THEN** the analysis history table is displayed

#### Scenario: Single analysis state
- **WHEN** user has only one analysis loaded
- **THEN** UI behavior is unchanged (no button was displayed anyway)
