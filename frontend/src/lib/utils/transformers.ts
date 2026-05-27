import type {
  Finding,
  DetectedViolation,
  Evidence,
  RegCategory,
  ValidationResult,
  DataSource,
} from '@/lib/api'
import type { TemperatureDataPoint, TemperatureDataSource } from '@/components/TemperatureChart'

export type { TemperatureDataPoint, TemperatureDataSource }

const OLD_TO_NEW_CATEGORY: Record<string, string> = {
  "thermal": "TEMP",
  "sensor": "SENS",
  "alarm": "ALARM",
  "cooling": "COOL",
  "insulation": "INS",
  "operational": "OPS",
  "data": "DATA",
  "power": "POWER",
}

export function convertCategory(category: string): string {
  if (OLD_TO_NEW_CATEGORY[category]) {
    return OLD_TO_NEW_CATEGORY[category]
  }
  return category
}

export function normalizeFindings(findings: Finding[]): Finding[] {
  return findings.map((finding) => ({
    ...finding,
    category: convertCategory(finding.category) as RegCategory,
  }))
}

export interface SeverityCounts {
  critical: number
  high: number
  medium: number
  low: number
  info: number
}

export function createEmptySeverityCounts(): SeverityCounts {
  return {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    info: 0,
  }
}

export interface CategoryViolationData {
  category: RegCategory
  severityCounts: SeverityCounts
}

export function findingsToDetectedViolations(findings: Finding[]): DetectedViolation[] {
  return findings.map((finding, index) => {
    const status: 'open' | 'acknowledged' | 'resolved' = finding.passed
      ? 'resolved'
      : 'open'

    return {
      id: `finding-${index}-${finding.rule_id}`,
      reg_code: finding.rule_id,
      severity: finding.severity,
      status,
      description: finding.message,
      evidence: finding.evidence as Evidence[],
      detected_at: finding.timestamp || new Date().toISOString(),
      created_at: new Date().toISOString(),
      data_source: finding.data_source,
      confidence: finding.confidence,
    }
  })
}

export function groupViolationsByCategory(
  findings: Finding[]
): Record<RegCategory, SeverityCounts> {
  const result: Record<RegCategory, SeverityCounts> = {
    TEMP: createEmptySeverityCounts(),
    SENS: createEmptySeverityCounts(),
    ALARM: createEmptySeverityCounts(),
    DATA: createEmptySeverityCounts(),
    POWER: createEmptySeverityCounts(),
    COOL: createEmptySeverityCounts(),
    INS: createEmptySeverityCounts(),
    OPS: createEmptySeverityCounts(),
  }

   for (const finding of findings) {
     if (finding.passed) continue

     const rawCategory = finding.category
     const category = convertCategory(rawCategory) as RegCategory
     if (!result[category]) continue

     const severity = finding.severity as keyof SeverityCounts
     if (severity in result[category]) {
       result[category][severity]++
     }
   }

  return result
}

export function calculateComplianceScore(
  passedCount: number,
  totalRules: number
): number {
  if (totalRules === 0) return 100
  return Math.round((passedCount / totalRules) * 100)
}

export function calculateComplianceScoreFromCounts(
  passedCount: number,
  failedCount: number
): number {
  return calculateComplianceScore(passedCount, passedCount + failedCount)
}

export function calculateComplianceScoreFromSeverityCounts(
  passedCount: number,
  failedBySeverity: Pick<SeverityCounts, 'critical' | 'high' | 'medium' | 'low' | 'info'>
): number {
  const failedCount =
    failedBySeverity.critical +
    failedBySeverity.high +
    failedBySeverity.medium +
    failedBySeverity.low +
    failedBySeverity.info

  const totalRules = passedCount + failedCount
  if (totalRules === 0) return 100

  // Weight penalties: critical reduces the score most.
  const weights = {
    critical: 1,
    high: 0.7,
    medium: 0.4,
    low: 0.2,
    info: 0.1,
  } as const

  const weightedPenalty =
    failedBySeverity.critical * weights.critical +
    failedBySeverity.high * weights.high +
    failedBySeverity.medium * weights.medium +
    failedBySeverity.low * weights.low +
    failedBySeverity.info * weights.info

  const rawScore = 100 - (weightedPenalty / totalRules) * 100
  return Math.max(0, Math.min(100, Math.round(rawScore)))
}

const TEMP_READING_PATTERN = /^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+TEMP_READING\s+([\d.]+)C?$/i

export function extractTemperatureFromRawLogs(
  rawLogs: string[]
): TemperatureDataPoint[] {
  const result: TemperatureDataPoint[] = []

  for (const line of rawLogs) {
    const match = line.match(TEMP_READING_PATTERN)
    if (!match) continue

    const [, timestampStr, valueStr] = match
    const value = parseFloat(valueStr)

    if (isNaN(value)) continue

    try {
      const time = new Date(timestampStr)
      const timeStr = `${time.getHours().toString().padStart(2, '0')}:${time.getMinutes().toString().padStart(2, '0')}`

       result.push({
         timestamp: time.toISOString(),
         time: timeStr,
         sensorA: value,
         source: 'log_file',
       })
    } catch {
      continue
    }
  }

  return result.sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  )
}

export interface AnalysisTemperatureData {
  validationResult: ValidationResult
  rawLogs: string[]
  temperatureData: TemperatureDataPoint[]
  analyzedAt: string
  deviceId: string
}

export function createAnalysisData(
  validationResult: ValidationResult,
  rawLogs: string[] = []
): AnalysisTemperatureData {
  const temperatureData = extractTemperatureFromRawLogs(rawLogs)
  return {
    validationResult,
    rawLogs,
    temperatureData,
    analyzedAt: new Date().toISOString(),
    deviceId: validationResult.device_id,
  }
}

interface ChartViolationMapping {
  rule_id: string
  category: string
  default_severity: Finding['severity']
}

const CHART_VIOLATION_MAPPINGS: Record<string, ChartViolationMapping> = {
  'excursion': {
    rule_id: 'REG-TEMP-1',
    category: 'TEMP',
    default_severity: 'high',
  },
  'gap': {
    rule_id: 'REG-DATA-1',
    category: 'DATA',
    default_severity: 'medium',
  },
  'slow_recovery': {
    rule_id: 'REG-TEMP-5',
    category: 'TEMP',
    default_severity: 'high',
  },
  'frequent_access': {
    rule_id: 'REG-OPS-3',
    category: 'OPS',
    default_severity: 'info',
  },
}

function confidenceToSeverity(confidence: number): Finding['severity'] {
  if (confidence > 0.8) return 'critical'
  if (confidence > 0.6) return 'high'
  if (confidence > 0.3) return 'medium'
  return 'low'
}

export function chartViolationsToFindings(
  violations: unknown[],
  chartAnalysisResult?: Record<string, unknown>
): Finding[] {
  const results: Finding[] = []

  const parentConfidence = 
    chartAnalysisResult && typeof chartAnalysisResult.confidence === 'number'
      ? chartAnalysisResult.confidence
      : 0.5

  const parentTimestamp = 
    chartAnalysisResult && typeof chartAnalysisResult.analyzed_at === 'string'
      ? chartAnalysisResult.analyzed_at
      : new Date().toISOString()

  for (const v of violations) {
    if (!v || typeof v !== 'object') continue
    const violation = v as Record<string, unknown>

    const violationType = typeof violation.violation_type === 'string' 
      ? violation.violation_type 
      : 'unknown'
    
    const mapping = CHART_VIOLATION_MAPPINGS[violationType] || {
      rule_id: 'REG-IMAGES-001',
      category: 'TEMP',
      default_severity: 'low',
    }

    const violationConfidence = typeof violation.confidence === 'number'
      ? violation.confidence
      : parentConfidence

    const severity = confidenceToSeverity(violationConfidence)

    let timestamp = parentTimestamp
    if (typeof violation.timestamp_start === 'string') {
      timestamp = violation.timestamp_start
    } else if (typeof violation.timestamp_end === 'string') {
      timestamp = violation.timestamp_end
    }

    const description = typeof violation.description === 'string'
      ? violation.description
      : 'Chart analysis violation'

    const extractedValue = typeof violation.extracted_value === 'number'
      ? violation.extracted_value
      : undefined

    const ruleDescription = `[${violationType.toUpperCase()}] ${mapping.category} violation from chart analysis`

    results.push({
      rule_id: mapping.rule_id,
      rule_description: ruleDescription,
      category: mapping.category,
      severity,
      passed: false,
      message: extractedValue !== undefined 
        ? `${description} (Value: ${extractedValue})` 
        : description,
      evidence: [],
      timestamp,
      needs_visual_verification: true,
      data_source: 'images' as DataSource,
      confidence: violationConfidence,
    })
  }

  return results
}

export interface ChartTimeSeriesPoint {
  timestamp?: string
  time?: string
  hour?: number
  minute?: number
  sensor_a?: number
  sensor_b?: number
  value?: number
  temperature?: number
}

export function parseChartTimePoint(point: unknown): TemperatureDataPoint | null {
  if (!point || typeof point !== 'object') return null

  const obj = point as Record<string, unknown>
  
  let sensorA: number | undefined
  let sensorB: number | undefined

  if (typeof obj.sensor_a === 'number') sensorA = obj.sensor_a
  else if (typeof obj.sensorA === 'number') sensorA = obj.sensorA
  else if (typeof obj.temperature === 'number') sensorA = obj.temperature
  else if (typeof obj.value === 'number') sensorA = obj.value

  if (typeof obj.sensor_b === 'number') sensorB = obj.sensor_b
  else if (typeof obj.sensorB === 'number') sensorB = obj.sensorB

  if (sensorA === undefined) return null

  let timestamp: string
  let time: string

  const now = new Date()

  if (typeof obj.timestamp === 'string') {
    timestamp = obj.timestamp
    try {
      const d = new Date(timestamp)
      time = `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
    } catch {
      time = typeof obj.time === 'string' ? obj.time : '00:00'
    }
  } else if (typeof obj.time === 'string') {
    time = obj.time
    const [hours, minutes] = time.split(':').map(Number)
    const d = new Date(now)
    d.setHours(isNaN(hours) ? 0 : hours, isNaN(minutes) ? 0 : minutes, 0, 0)
    timestamp = d.toISOString()
  } else if (typeof obj.hour === 'number') {
    const hour = obj.hour
    const minute = typeof obj.minute === 'number' ? obj.minute : 0
    time = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`
    const d = new Date(now)
    d.setHours(hour, minute, 0, 0)
    timestamp = d.toISOString()
  } else {
    return null
  }

  return {
    timestamp,
    time,
    sensorA,
    sensorB,
    source: 'chart_image',
  }
}

export function extractTemperatureFromChartResult(
  chartResult: Record<string, unknown>
): TemperatureDataPoint[] {
  const result: TemperatureDataPoint[] = []

  let dataArray: unknown[] | undefined

  if ('data_points' in chartResult && Array.isArray(chartResult.data_points)) {
    dataArray = chartResult.data_points
  } else if ('time_series' in chartResult && Array.isArray(chartResult.time_series)) {
    dataArray = chartResult.time_series
  } else if ('readings' in chartResult && Array.isArray(chartResult.readings)) {
    dataArray = chartResult.readings
  } else if ('temperature_data' in chartResult && Array.isArray(chartResult.temperature_data)) {
    dataArray = chartResult.temperature_data
  }

  if (dataArray) {
    for (const item of dataArray) {
      const parsed = parseChartTimePoint(item)
      if (parsed) {
        result.push(parsed)
      }
    }
  }

  if (result.length === 0) {
    return extractTemperatureFromViolations(chartResult)
  }

  return result.sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  )
}

function extractTemperatureFromViolations(
  chartResult: Record<string, unknown>
): TemperatureDataPoint[] {
  const result: TemperatureDataPoint[] = []
  const seenTimes = new Set<string>()

  let violations: unknown[] | undefined

  if ('violations' in chartResult && Array.isArray(chartResult.violations)) {
    violations = chartResult.violations
  }

  if (!violations) return result

  for (const v of violations) {
    if (!v || typeof v !== 'object') continue
    const violation = v as Record<string, unknown>

    let timestamp: string | undefined
    let time: string | undefined
    let value: number | undefined

    if (typeof violation.extracted_value === 'number') {
      value = violation.extracted_value
    } else if (typeof violation.value === 'number') {
      value = violation.value
    }

    if (typeof violation.timestamp_start === 'string') {
      timestamp = violation.timestamp_start
    } else if (typeof violation.timestamp_end === 'string') {
      timestamp = violation.timestamp_end
    } else if (typeof violation.timestamp === 'string') {
      timestamp = violation.timestamp
    }

    if (timestamp) {
      try {
        const d = new Date(timestamp)
        time = `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
      } catch {
        time = '00:00'
      }
    }

    if (time && value !== undefined && !seenTimes.has(time)) {
      seenTimes.add(time)
      result.push({
        timestamp: timestamp || new Date().toISOString(),
        time,
        sensorA: value,
        source: 'chart_image',
      })
    }
  }

  return result.sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  )
}

export function mergeTemperatureData(
  logData: TemperatureDataPoint[],
  chartData: TemperatureDataPoint[]
): TemperatureDataPoint[] {
  const merged = [...logData, ...chartData]
  
  return merged.sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  )
}
