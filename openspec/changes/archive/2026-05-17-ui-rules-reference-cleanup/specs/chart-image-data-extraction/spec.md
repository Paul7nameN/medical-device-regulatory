## MODIFIED Requirements

### Requirement: Chart violation to rule ID mapping
The system SHALL map chart violation types to the correct regulatory rule IDs as defined in the MED-THERM-2026 standard.

#### Scenario: Excursion violation mapping
- **WHEN** VLLM detects a temperature excursion in a chart image
- **THEN** the violation is mapped to REG-TEMP-1 (unchanged)

#### Scenario: Data gap violation mapping
- **WHEN** VLLM detects a data gap in a chart image
- **THEN** the violation is mapped to REG-DATA-1 (unchanged)

#### Scenario: Slow recovery violation mapping (CORRECTED)
- **WHEN** VLLM detects a slow recovery (temperature takes too long to return to range)
- **THEN** the violation is mapped to **REG-TEMP-3** (was incorrectly REG-TEMP-5)
- **Note**: REG-TEMP-3 is defined as "After any disturbance, system must return to stable range within ≤ 3 minutes"

#### Scenario: Frequent access violation mapping (CORRECTED)
- **WHEN** VLLM detects frequent door access patterns
- **THEN** the violation is mapped to **REG-OPS-2** (was incorrectly REG-OPS-3)
- **Note**: REG-OPS-2 is defined as "Excessive access is defined as > 10 events/hour and must trigger operational warning"

#### Scenario: Unknown violation type fallback
- **WHEN** VLLM returns a violation type not in the mapping dictionary
- **THEN** the violation is mapped to **REG-TEMP-1** as a generic fallback (was incorrectly REG-IMAGES-001 which does not exist)
- **Note**: REG-IMAGES-001 is NOT a valid MED-THERM-2026 rule ID

#### Scenario: Consistency with log file analysis
- **WHEN** both log file analysis and chart image analysis detect the same type of violation
- **THEN** both use the same rule ID (e.g., slow recovery uses REG-TEMP-3 in both)
