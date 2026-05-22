import type { LucideIcon } from 'lucide-react'
import {
  Thermometer,
  Droplets,
  Zap,
  Fan,
  Battery,
} from 'lucide-react'

export type TelemetryMetricId =
  | 'temperature'
  | 'humidity'
  | 'voltage'
  | 'fan_speed'
  | 'battery'

export type TelemetryDataSource = 'log_file' | 'chart_image'

export interface TelemetryDataPoint {
  timestamp: string
  time: string
  value: number
  sensorB?: number
  source?: TelemetryDataSource
}

export interface TelemetryMetricConfig {
  id: TelemetryMetricId
  label: string
  logType: string
  unit: string
  icon: LucideIcon
  color: string
  safeRange?: { min: number; max: number }
  supportsDualSensor?: boolean
  description: string
}

export const TELEMETRY_METRICS: TelemetryMetricConfig[] = [
  {
    id: 'temperature',
    label: 'Temperature',
    logType: 'TEMP_READING',
    unit: '°C',
    icon: Thermometer,
    color: '#f97316',
    safeRange: { min: 2, max: 8 },
    supportsDualSensor: true,
    description: 'Chamber temperature readings (REG-TEMP)',
  },
  {
    id: 'humidity',
    label: 'Humidity',
    logType: 'HUMIDITY',
    unit: '%',
    icon: Droplets,
    color: '#0ea5e9',
    description: 'Ambient humidity from device logs',
  },
  {
    id: 'voltage',
    label: 'Voltage',
    logType: 'VOLTAGE',
    unit: 'V',
    icon: Zap,
    color: '#eab308',
    description: 'Supply voltage readings (REG-POWER)',
  },
  {
    id: 'fan_speed',
    label: 'Fan speed',
    logType: 'FAN_SPEED',
    unit: 'RPM',
    icon: Fan,
    color: '#8b5cf6',
    description: 'Cooling fan speed (REG-COOL)',
  },
  {
    id: 'battery',
    label: 'Battery',
    logType: 'BATTERY_LEVEL',
    unit: '%',
    icon: Battery,
    color: '#22c55e',
    description: 'Battery level telemetry (REG-POWER)',
  },
]

export const TELEMETRY_METRIC_BY_ID = Object.fromEntries(
  TELEMETRY_METRICS.map((metric) => [metric.id, metric])
) as Record<TelemetryMetricId, TelemetryMetricConfig>
