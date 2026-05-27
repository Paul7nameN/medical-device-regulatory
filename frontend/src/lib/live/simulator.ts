import type { LiveScenario, LiveTelemetryTick } from './types'
import type { TelemetryMetricId } from '@/lib/telemetry/metrics'

function mulberry32(seed: number) {
  return function () {
    let t = (seed += 0x6d2b79f5)
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function formatTime(d: Date): string {
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`
}

function tempForScenario(scenario: LiveScenario, tickIndex: number, rng: () => number): number {
  if (scenario === 'stable') {
    return 4.5 + Math.sin(tickIndex / 18) * 1.2 + (rng() - 0.5) * 0.6
  }
  if (scenario === 'excursion') {
    if (tickIndex < 25) return 5 + rng() * 1.5
    if (tickIndex < 55) return 7.5 + (tickIndex - 25) * 0.12 + rng() * 0.8
    return 9 + Math.min(3, (tickIndex - 55) * 0.08) + rng() * 0.5
  }
  // stress: drift high + noise
  return 6.5 + tickIndex * 0.05 + rng() * 1.2
}

export function createLiveTick(
  scenario: LiveScenario,
  tickIndex: number,
  startedAt: number,
  seed: number
): LiveTelemetryTick[] {
  const rng = mulberry32(seed + tickIndex)
  const now = Date.now()
  const ts = new Date(now).toISOString()
  const time = formatTime(new Date(now))
  const ticks: LiveTelemetryTick[] = []

  const temp = Math.round(tempForScenario(scenario, tickIndex, rng) * 10) / 10
  ticks.push({ timestamp: ts, time, metric: 'temperature', value: temp })

  const fan = Math.max(900, Math.min(3200, Math.round(1500 + (temp - 5) * 200 + (rng() - 0.5) * 150)))
  ticks.push({ timestamp: ts, time, metric: 'fan_speed', value: fan })

  if (tickIndex % 3 === 0) {
    ticks.push({
      timestamp: ts,
      time,
      metric: 'humidity',
      value: Math.round(40 + rng() * 35),
    })
  }

  if (tickIndex % 4 === 0) {
    const batt = 99 - tickIndex * 0.15 - (scenario === 'stress' ? tickIndex * 0.08 : 0)
    ticks.push({
      timestamp: ts,
      time,
      metric: 'battery',
      value: Math.max(75, Math.round(batt * 10) / 10),
    })
  }

  if (tickIndex % 4 === 2) {
    const v = 12.4 - tickIndex * 0.008 - (scenario === 'stress' ? 0.02 : 0)
    ticks.push({
      timestamp: ts,
      time,
      metric: 'voltage',
      value: Math.round(v * 100) / 100,
    })
  }

  // Scenario events
  if (scenario === 'excursion' && tickIndex > 0 && tickIndex % 22 === 0) {
    ticks.push({ timestamp: ts, time, metric: 'temperature', value: temp, event: 'DOOR_OPEN' })
  }
  if (scenario === 'excursion' && tickIndex > 0 && tickIndex % 22 === 3) {
    ticks.push({ timestamp: ts, time, metric: 'temperature', value: temp, event: 'DOOR_CLOSE' })
  }

  if (scenario === 'stress' && tickIndex === 35) {
    ticks.push({ timestamp: ts, time, metric: 'temperature', value: temp, event: 'SENSOR_TIMEOUT' })
  }

  if (scenario === 'stable' && tickIndex > 0 && tickIndex % 40 === 0) {
    ticks.push({ timestamp: ts, time, metric: 'temperature', value: temp, event: 'DOOR_OPEN' })
    ticks.push({ timestamp: ts, time, metric: 'temperature', value: temp, event: 'DOOR_CLOSE' })
  }

  void startedAt
  return ticks
}

export const LIVE_TICK_INTERVAL_MS = 2000
export const LIVE_MAX_POINTS = 120

export function appendPoint<T>(arr: T[], point: T, max: number): T[] {
  const next = [...arr, point]
  if (next.length <= max) return next
  return next.slice(next.length - max)
}

export function metricSeriesFromTicks(
  ticks: LiveTelemetryTick[],
  metric: TelemetryMetricId
) {
  return ticks
    .filter((t) => t.metric === metric && !t.event)
    .map((t) => ({
      timestamp: t.timestamp,
      time: t.time,
      value: t.value,
      source: 'log_file' as const,
    }))
}
