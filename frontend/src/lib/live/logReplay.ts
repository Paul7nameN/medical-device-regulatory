import type { TelemetryMetricId } from '@/lib/telemetry/metrics'
import type { LiveTelemetryTick } from './types'

const LOG_LINE_PATTERN =
  /^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(\w+)(?:\s+(.*))?$/

const METRIC_LOG_TYPES: Record<string, TelemetryMetricId> = {
  TEMP_READING: 'temperature',
  FAN_SPEED: 'fan_speed',
  HUMIDITY: 'humidity',
  VOLTAGE: 'voltage',
  BATTERY_LEVEL: 'battery',
}

const EVENT_LOG_TYPES = new Set([
  'DOOR_OPEN',
  'DOOR_CLOSE',
  'SENSOR_TIMEOUT',
  'ALARM_TRIGGERED',
  'TEMP_WARNING',
  'COOLING_RECOVERY_START',
  'TELEMETRY_SYNC_FAILED',
  'DEVICE_START',
])

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

function formatTimeFromTimestamp(timestampStr: string): string {
  const d = new Date(timestampStr.replace(' ', 'T'))
  if (Number.isNaN(d.getTime())) return timestampStr.slice(11, 19)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`
}

function lineToTicks(line: string, lastTemp: number): { ticks: LiveTelemetryTick[]; lastTemp: number } {
  const match = line.trim().match(LOG_LINE_PATTERN)
  if (!match) return { ticks: [], lastTemp }

  const [, timestampStr, logType, rawValue = ''] = match
  const timestamp = timestampStr.replace(' ', 'T')
  const iso = new Date(timestamp).toISOString()
  const time = formatTimeFromTimestamp(timestampStr)

  const metricId = METRIC_LOG_TYPES[logType]
  if (metricId) {
    const value = parseNumericValue(logType, rawValue)
    if (value === null || Number.isNaN(value)) return { ticks: [], lastTemp }

    const nextTemp = metricId === 'temperature' ? value : lastTemp
    return {
      ticks: [{ timestamp: iso, time, metric: metricId, value }],
      lastTemp: nextTemp,
    }
  }

  if (EVENT_LOG_TYPES.has(logType)) {
    let event = logType
    if (logType === 'SENSOR_TIMEOUT') event = 'SENSOR_TIMEOUT'

    return {
      ticks: [
        {
          timestamp: iso,
          time,
          metric: 'temperature',
          value: lastTemp,
          event,
        },
      ],
      lastTemp,
    }
  }

  return { ticks: [], lastTemp }
}

/** One batch per log line, in file order. */
export function parseLogLinesToReplayBatches(rawLogs: string[]): LiveTelemetryTick[][] {
  const batches: LiveTelemetryTick[][] = []
  let lastTemp = 5

  for (const line of rawLogs) {
    const { ticks, lastTemp: updated } = lineToTicks(line, lastTemp)
    lastTemp = updated
    if (ticks.length > 0) batches.push(ticks)
  }

  return batches
}

export function readLogFile(file: File): Promise<{ lines: string[]; name: string }> {
  return file.text().then((text) => ({
    lines: text.split(/\r?\n/).filter((l) => l.trim().length > 0),
    name: file.name,
  }))
}
