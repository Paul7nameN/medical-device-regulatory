import type { TelemetryMetricId } from '@/lib/telemetry/metrics'

export type LiveScenario = 'stable' | 'excursion' | 'stress'

export type LiveSpeedMultiplier = 1 | 2 | 5 | 10 | 25

export type LiveSourceMode = 'simulated' | 'log_file'

export const LIVE_SPEED_OPTIONS: LiveSpeedMultiplier[] = [1, 2, 5, 10, 25]

export interface LiveTelemetryTick {
  timestamp: string
  time: string
  metric: TelemetryMetricId
  value: number
  event?: string
}

export type LiveAlertSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info'

export interface LiveAlert {
  id: string
  ruleId: string
  severity: LiveAlertSeverity
  title: string
  message: string
  advice: string
  timestamp: string
}
