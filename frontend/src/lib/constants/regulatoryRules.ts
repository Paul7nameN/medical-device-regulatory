export type RuleCategory = 'TEMP' | 'SENS' | 'ALARM' | 'DATA' | 'POWER' | 'COOL' | 'INS' | 'OPS'
export type RuleSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info'
export type ValidationType = 'operational' | 'inspection'
export type RuleSource = 'logs' | 'inspection' | 'combined' | 'images'

export interface RegulatoryRule {
  id: string
  category: RuleCategory
  categoryName: string
  title: string
  description: string
  threshold: string
  severity: RuleSeverity
  validationType: ValidationType
  source: RuleSource
  confidence: number
  inspectionHint?: string
}

export const CATEGORY_NAMES: Record<RuleCategory, string> = {
  TEMP: 'Thermal Safety',
  SENS: 'Sensor Redundancy & Accuracy',
  ALARM: 'Alarm System',
  DATA: 'Data Integrity & Logging',
  POWER: 'Power System',
  COOL: 'Cooling System',
  INS: 'Structural & Insulation',
  OPS: 'Operational Behavior',
}

export const REGULATORY_RULES: RegulatoryRule[] = [
  // REG-TEMP - Thermal Safety
  {
    id: 'REG-TEMP-1',
    category: 'TEMP',
    categoryName: 'Thermal Safety',
    title: 'Operating Temperature Range',
    description: 'The device shall maintain internal storage temperature within 2°C to 8°C at all times during active operation. This is the primary thermal safety requirement for medical cold chain devices.',
    threshold: '2°C ≤ T ≤ 8°C',
    severity: 'high',
    validationType: 'operational',
    source: 'logs',
    confidence: 1.0,
  },
  {
    id: 'REG-TEMP-2',
    category: 'TEMP',
    categoryName: 'Thermal Safety',
    title: 'Excursion Limits',
    description: 'Temperature excursions outside the allowed range must comply with: maximum 5 minutes per single event, maximum 10 minutes cumulative per 24 hours. Any exceedance is considered a critical violation.',
    threshold: '≤5min single, ≤10min/24h cumulative',
    severity: 'critical',
    validationType: 'operational',
    source: 'logs',
    confidence: 1.0,
  },
  {
    id: 'REG-TEMP-3',
    category: 'TEMP',
    categoryName: 'Thermal Safety',
    title: 'Recovery After Disturbance',
    description: 'After any disturbance such as door opening, the system must return to stable operating range within 3 minutes. This ensures rapid recovery after access events.',
    threshold: 'Recovery ≤ 3 minutes',
    severity: 'high',
    validationType: 'operational',
    source: 'logs',
    confidence: 1.0,
  },
  {
    id: 'REG-TEMP-4',
    category: 'TEMP',
    categoryName: 'Thermal Safety',
    title: 'Sampling Frequency',
    description: 'Temperature must be recorded at intervals not exceeding 30 seconds. This ensures sufficient data density for accurate excursion detection and recovery verification.',
    threshold: 'Δt ≤ 30 seconds',
    severity: 'medium',
    validationType: 'operational',
    source: 'logs',
    confidence: 1.0,
  },

  // REG-SENS - Sensor Redundancy & Accuracy
  {
    id: 'REG-SENS-1',
    category: 'SENS',
    categoryName: 'Sensor Redundancy & Accuracy',
    title: 'Dual Sensor Redundancy',
    description: 'The system shall include at least one primary sensor and at least one redundant secondary sensor. Failure of redundancy constitutes a critical violation as it eliminates temperature visibility fallback.',
    threshold: 'PRIMARY + SECONDARY required',
    severity: 'critical',
    validationType: 'operational',
    source: 'logs',
    confidence: 1.0,
  },
  {
    id: 'REG-SENS-2',
    category: 'SENS',
    categoryName: 'Sensor Redundancy & Accuracy',
    title: 'Sensor Placement Constraint',
    description: 'Sensors must not be placed within 15 cm from airflow outlet to prevent airflow bias interference. This ensures accurate chamber temperature readings without draft distortion.',
    threshold: 'Placement ≥ 15cm from airflow',
    severity: 'info',
    validationType: 'inspection',
    source: 'inspection',
    confidence: 0.0,
    inspectionHint: 'Verify sensor placement via blueprint analysis or physical measurement. Use calipers or review engineering schematics.',
  },
  {
    id: 'REG-SENS-3',
    category: 'SENS',
    categoryName: 'Sensor Redundancy & Accuracy',
    title: 'Sensor Agreement',
    description: 'Sensor readings must satisfy |T1 - T2| ≤ 0.5°C. Disagreement beyond this threshold indicates sensor drift, calibration issues, or placement problems.',
    threshold: '|T1 - T2| ≤ 0.5°C',
    severity: 'high',
    validationType: 'operational',
    source: 'combined',
    confidence: 0.7,
  },

  // REG-ALARM - Alarm System
  {
    id: 'REG-ALARM-1',
    category: 'ALARM',
    categoryName: 'Alarm System',
    title: 'Alarm Activation Delay',
    description: 'Alarm shall activate if temperature remains outside range for 2 minutes or more. This provides a grace period for minor fluctuations while ensuring timely alerting for actual excursions.',
    threshold: 'Activate after ≥ 2 min out of range',
    severity: 'high',
    validationType: 'operational',
    source: 'logs',
    confidence: 1.0,
  },
  {
    id: 'REG-ALARM-2',
    category: 'ALARM',
    categoryName: 'Alarm System',
    title: 'Notification Latency',
    description: 'System notifications must be delivered within 10 seconds from alarm trigger. This ensures rapid response by personnel during excursion events.',
    threshold: 'Notification ≤ 10 seconds',
    severity: 'medium',
    validationType: 'inspection',
    source: 'inspection',
    confidence: 0.0,
    inspectionHint: 'Requires end-to-end notification timing test. Measure from alarm trigger to mobile push notification delivery. Verify latency across all notification channels.',
  },
  {
    id: 'REG-ALARM-3',
    category: 'ALARM',
    categoryName: 'Alarm System',
    title: 'Multi-Channel Notification',
    description: 'The system must support three notification channels: audible alarm, visual dashboard alert, and remote mobile notification. Failure to support any channel is non-compliant.',
    threshold: '3 channels: audible + visual + mobile',
    severity: 'medium',
    validationType: 'inspection',
    source: 'inspection',
    confidence: 0.0,
    inspectionHint: 'Verify all three notification channels: (1) Test physical speaker/buzzer for audible alarm, (2) Verify HMI/dashboard visual indicators, (3) Test push notification system.',
  },

  // REG-DATA - Data Integrity & Logging
  {
    id: 'REG-DATA-1',
    category: 'DATA',
    categoryName: 'Data Integrity & Logging',
    title: 'Immutable Audit Log',
    description: 'The system must maintain an immutable log of temperature readings, alarms, configuration changes, and sensor status events. This provides an auditable trail for compliance verification.',
    threshold: 'Immutable log of all critical events',
    severity: 'info',
    validationType: 'operational',
    source: 'logs',
    confidence: 1.0,
  },
  {
    id: 'REG-DATA-2',
    category: 'DATA',
    categoryName: 'Data Integrity & Logging',
    title: 'Telemetry Continuity',
    description: 'Data gaps in telemetry must not exceed 90 seconds. This ensures continuous visibility and prevents unobserved excursions during communication interruptions.',
    threshold: 'Gaps ≤ 90 seconds',
    severity: 'medium',
    validationType: 'operational',
    source: 'logs',
    confidence: 1.0,
  },
  {
    id: 'REG-DATA-3',
    category: 'DATA',
    categoryName: 'Data Integrity & Logging',
    title: 'Data Retention',
    description: 'Local data must be retained for at least 72 hours in case of cloud sync failure. This ensures compliance data survives network outages.',
    threshold: 'Retention ≥ 72 hours',
    severity: 'info',
    validationType: 'operational',
    source: 'combined',
    confidence: 0.5,
    inspectionHint: 'Verify device storage capacity and retention policy configuration. Review database purge schedules and storage allocation.',
  },

  // REG-POWER - Power System
  {
    id: 'REG-POWER-1',
    category: 'POWER',
    categoryName: 'Power System',
    title: 'Battery Backup Runtime',
    description: 'Battery backup must support continuous operation for at least 4 hours. This provides sufficient time for intervention during power failures.',
    threshold: 'Runtime ≥ 4 hours',
    severity: 'medium',
    validationType: 'operational',
    source: 'combined',
    confidence: 0.6,
    inspectionHint: 'Verify battery capacity through full discharge test or review device specifications. Calculate runtime based on observed drain rates.',
  },
  {
    id: 'REG-POWER-2',
    category: 'POWER',
    categoryName: 'Power System',
    title: 'Degraded Mode Compliance',
    description: 'Even in battery mode, temperature must remain compliant with REG-TEMP-1 (2-8°C). Cooling systems must continue operating on backup power.',
    threshold: 'Temp compliant during battery mode',
    severity: 'high',
    validationType: 'operational',
    source: 'logs',
    confidence: 0.9,
  },

  // REG-COOL - Cooling System
  {
    id: 'REG-COOL-1',
    category: 'COOL',
    categoryName: 'Cooling System',
    title: 'Redundant Airflow Paths',
    description: 'Cooling system must include at least 2 independent airflow paths. This provides N+1 redundancy for cooling failures.',
    threshold: '≥ 2 airflow paths',
    severity: 'info',
    validationType: 'inspection',
    source: 'inspection',
    confidence: 0.0,
    inspectionHint: 'Verify redundant fans and separate cooling loops via blueprint analysis or physical inspection. Check for independent airflow paths and fan redundancy.',
  },
  {
    id: 'REG-COOL-2',
    category: 'COOL',
    categoryName: 'Cooling System',
    title: 'Failure Tolerance',
    description: 'Single-point failure in cooling airflow shall not result in temperature excursion beyond allowed range for more than 3 minutes. This requires the cooling architecture to maintain thermal stability even during component failures.',
    threshold: '≤ 3min recovery after failure',
    severity: 'high',
    validationType: 'operational',
    source: 'logs',
    confidence: 0.8,
  },

  // REG-INS - Structural & Insulation
  {
    id: 'REG-INS-1',
    category: 'INS',
    categoryName: 'Structural & Insulation',
    title: 'Insulation Thickness',
    description: 'All chamber walls must have insulation thickness of at least 4 cm. Sufficient insulation prevents thermal drift, reduces energy consumption, and improves recovery times.',
    threshold: 'Thickness ≥ 4 cm',
    severity: 'info',
    validationType: 'inspection',
    source: 'inspection',
    confidence: 0.0,
    inspectionHint: 'Measure insulation thickness on all chamber walls using calipers or review engineering specifications. Verify minimum 4cm on ALL wall surfaces.',
  },
  {
    id: 'REG-INS-2',
    category: 'INS',
    categoryName: 'Structural & Insulation',
    title: 'Battery Compartment Isolation',
    description: 'Battery compartment must be physically and thermally isolated from storage chamber. This prevents battery heat from warming plasma and contains thermal runaway risk.',
    threshold: 'Physical + thermal barrier required',
    severity: 'info',
    validationType: 'inspection',
    source: 'inspection',
    confidence: 0.0,
    inspectionHint: 'Verify physical barrier between battery compartment and storage chamber via CAD analysis or physical inspection. Check for thermal isolation features and review thermal simulation data.',
  },

  // REG-OPS - Operational Behavior
  {
    id: 'REG-OPS-1',
    category: 'OPS',
    categoryName: 'Operational Behavior',
    title: 'Door Recovery Requirement',
    description: 'After a door opening event, the system must stabilize within 3 minutes and not exceed 8°C during the recovery window. This ensures door access does not compromise stored materials.',
    threshold: 'Recovery ≤ 3min, ≤ 8°C during recovery',
    severity: 'high',
    validationType: 'operational',
    source: 'logs',
    confidence: 1.0,
  },
  {
    id: 'REG-OPS-2',
    category: 'OPS',
    categoryName: 'Operational Behavior',
    title: 'Access Frequency Threshold',
    description: 'Excessive access is defined as more than 10 door events per hour and must trigger operational warning. Frequent access correlates with temperature instability and cooling system stress.',
    threshold: '≤ 10 door events/hour',
    severity: 'low',
    validationType: 'operational',
    source: 'logs',
    confidence: 1.0,
  },
]

export function getAllRules(): RegulatoryRule[] {
  return REGULATORY_RULES
}

export function getRulesByCategory(category: RuleCategory): RegulatoryRule[] {
  return REGULATORY_RULES.filter((r) => r.category === category)
}

export function getRulesByValidationType(type: ValidationType): RegulatoryRule[] {
  return REGULATORY_RULES.filter((r) => r.validationType === type)
}

export function getRuleById(id: string): RegulatoryRule | undefined {
  return REGULATORY_RULES.find((r) => r.id === id)
}

export function getCategories(): RuleCategory[] {
  return ['TEMP', 'SENS', 'ALARM', 'DATA', 'POWER', 'COOL', 'INS', 'OPS']
}

export function getValidationTypes(): ValidationType[] {
  return ['operational', 'inspection']
}
