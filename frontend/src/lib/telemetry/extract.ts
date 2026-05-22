import type { TemperatureDataPoint } from '@/components/TemperatureChart'
import type {
  TelemetryDataPoint,
  TelemetryMetricId,
  TelemetryDataSource,
} from './metrics'
import { TELEMETRY_METRICS } from './metrics'

const LOG_LINE_PATTERN =
  /^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(\w+)(?:\s+(.*))?$/

function parseNumericValue(logType: string, rawValue: string): number | null {
  const trimmed = rawValue.trim()
  if (!trimmed) return null

  if (logType === 'TEMP_READING') {
    const match = trimmed.match(/(-?[\d.]+)\s*C?/i)
    return match ? parseFloat(match[1]) : null
  }
  if (logType === 'FAN_SPEED') {
    const match = trimmed.match(/(\d+)\s*RPM/i)
    return match ? parseFloat(match[1]) : null
  }
  if (logType === 'VOLTAGE') {
    const match = trimmed.match(/([\d.]+)\s*V/i)
    return match ? parseFloat(match[1]) : null
  }
  if (logType === 'HUMIDITY' || logType === 'BATTERY_LEVEL') {
    const match = trimmed.match(/([\d.]+)\s*%/)
    return match ? parseFloat(match[1]) : null
  }

  return null
}

function toTelemetryPoint(
  timestampStr: string,
  value: number,
  source: TelemetryDataSource = 'log_file'
): TelemetryDataPoint {
  const time = new Date(timestampStr)
  const timeStr = `${time.getHours().toString().padStart(2, '0')}:${time.getMinutes().toString().padStart(2, '0')}`
  return {
    timestamp: time.toISOString(),
    time: timeStr,
    value,
    source,
  }
}

export function extractTelemetrySeriesFromRawLogs(
  rawLogs: string[]
): Partial<Record<TelemetryMetricId, TelemetryDataPoint[]>> {
  const buckets: Partial<Record<TelemetryMetricId, TelemetryDataPoint[]>> = {}

  for (const metric of TELEMETRY_METRICS) {
    buckets[metric.id] = []
  }

  for (const line of rawLogs) {
    const match = line.trim().match(LOG_LINE_PATTERN)
    if (!match) continue

    const [, timestampStr, logType, rawValue = ''] = match
    const metric = TELEMETRY_METRICS.find((item) => item.logType === logType)
    if (!metric) continue

    const value = parseNumericValue(logType, rawValue)
    if (value === null || Number.isNaN(value)) continue

    try {
      buckets[metric.id]!.push(toTelemetryPoint(timestampStr, value, 'log_file'))
    } catch {
      continue
    }
  }

  for (const metric of TELEMETRY_METRICS) {
    const series = buckets[metric.id]
    if (series) {
      buckets[metric.id] = series.sort(
        (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      )
    }
  }

  return buckets
}

export function temperaturePointsToTelemetry(
  points: TemperatureDataPoint[]
): TelemetryDataPoint[] {
  return points.map((point) => ({
    timestamp: point.timestamp,
    time: point.time,
    value: point.sensorA,
    sensorB: point.sensorB,
    source: point.source,
  }))
}

export function buildTelemetrySeries(
  rawLogs: string[],
  chartTemperature?: TemperatureDataPoint[]
): Record<TelemetryMetricId, TelemetryDataPoint[]> {
  const fromLogs = extractTelemetrySeriesFromRawLogs(rawLogs)
  const result = {} as Record<TelemetryMetricId, TelemetryDataPoint[]>

  for (const metric of TELEMETRY_METRICS) {
    result[metric.id] = [...(fromLogs[metric.id] || [])]
  }

  if (chartTemperature && chartTemperature.length > 0) {
    const chartSeries = temperaturePointsToTelemetry(chartTemperature)
    const merged = [...result.temperature, ...chartSeries]
    merged.sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )
    result.temperature = merged
  }

  return result
}

export function getAvailableMetrics(
  series: Partial<Record<TelemetryMetricId, TelemetryDataPoint[]>>
): TelemetryMetricId[] {
  return TELEMETRY_METRICS.filter(
    (metric) => (series[metric.id]?.length ?? 0) > 0
  ).map((metric) => metric.id)
}
