import { REGULATORY_CONSTANTS } from '@/lib/constants'
import type { LiveAlert, LiveAlertSeverity, LiveTelemetryTick } from './types'

const { min: TEMP_MIN, max: TEMP_MAX } = REGULATORY_CONSTANTS.safeTemperatureRange

export interface MonitorState {
  lastTemp?: number
  outOfRangeSinceMs: number | null
  doorOpen: boolean
  secondarySensorOk: boolean
  lastAlertAt: Record<string, number>
}

export function createMonitorState(): MonitorState {
  return {
    outOfRangeSinceMs: null,
    doorOpen: false,
    secondarySensorOk: true,
    lastAlertAt: {},
  }
}

function makeAlert(
  ruleId: string,
  severity: LiveAlertSeverity,
  title: string,
  message: string,
  advice: string,
  now: number
): LiveAlert {
  return {
    id: `${ruleId}-${now}`,
    ruleId,
    severity,
    title,
    message,
    advice,
    timestamp: new Date(now).toISOString(),
  }
}

function shouldEmit(state: MonitorState, ruleId: string, now: number, cooldownMs = 45000): boolean {
  const last = state.lastAlertAt[ruleId] ?? 0
  if (now - last < cooldownMs) return false
  state.lastAlertAt[ruleId] = now
  return true
}

export function evaluateLiveTick(
  tick: LiveTelemetryTick,
  state: MonitorState,
  now: number
): LiveAlert[] {
  const alerts: LiveAlert[] = []

  if (tick.event === 'DOOR_OPEN') {
    state.doorOpen = true
    if (shouldEmit(state, 'REG-OPS-DOOR', now, 60000)) {
      alerts.push(
        makeAlert(
          'REG-OPS-DOOR',
          'medium',
          'Door opened',
          'Chamber access detected during transport.',
          'Minimize door open time. Verify the door is fully closed to avoid temperature excursions (REG-TEMP).',
          now
        )
      )
    }
  }

  if (tick.event === 'DOOR_CLOSE') {
    state.doorOpen = false
  }

  if (tick.event === 'SENSOR_TIMEOUT') {
    state.secondarySensorOk = false
    if (shouldEmit(state, 'REG-SENS-1', now)) {
      alerts.push(
        makeAlert(
          'REG-SENS-1',
          'critical',
          'Secondary sensor timeout',
          'Redundant temperature sensor is not responding.',
          'Check SECONDARY sensor cable and connector immediately. Do not rely on a single sensor for cold-chain compliance.',
          now
        )
      )
    }
  }

  if (tick.metric === 'temperature') {
    state.lastTemp = tick.value
    const inRange = tick.value >= TEMP_MIN && tick.value <= TEMP_MAX

    if (!inRange) {
      if (state.outOfRangeSinceMs === null) state.outOfRangeSinceMs = now
      const durationSec = (now - state.outOfRangeSinceMs) / 1000

      if (shouldEmit(state, 'REG-TEMP-1', now, 30000)) {
        const severity: LiveAlertSeverity =
          tick.value > TEMP_MAX + 2 || tick.value < TEMP_MIN - 1 ? 'critical' : 'high'
        alerts.push(
          makeAlert(
            'REG-TEMP-1',
            severity,
            'Temperature out of safe range',
            `Current reading ${tick.value.toFixed(1)}°C (allowed ${TEMP_MIN}–${TEMP_MAX}°C).`,
            tick.value > TEMP_MAX
              ? 'Activate cooling recovery, reduce door access, and confirm fan operation. Target return below 8°C within recovery window.'
              : 'Check cooling setpoint and insulation. Verify sensors are not iced or disconnected.',
            now
          )
        )
      }

      if (durationSec >= 90 && shouldEmit(state, 'REG-TEMP-2', now)) {
        alerts.push(
          makeAlert(
            'REG-TEMP-2',
            'critical',
            'Sustained temperature excursion',
            `Out-of-range for ~${Math.round(durationSec)}s.`,
            'Treat as compliance risk: stop unnecessary access, enable recovery mode, and prepare QA documentation if excursion exceeds 5 minutes.',
            now
          )
        )
      }
    } else {
      state.outOfRangeSinceMs = null
    }
  }

  if (tick.metric === 'battery' && tick.value < 85) {
    if (shouldEmit(state, 'REG-POWER-2', now)) {
      alerts.push(
        makeAlert(
          'REG-POWER-2',
          tick.value < 80 ? 'high' : 'medium',
          'Low battery',
          `Battery at ${tick.value.toFixed(1)}%.`,
          'Connect to mains if possible. Monitor voltage and plan replacement before next long transport.',
          now
        )
      )
    }
  }

  if (tick.metric === 'voltage' && tick.value < 11.8) {
    if (shouldEmit(state, 'REG-POWER-1', now)) {
      alerts.push(
        makeAlert(
          'REG-POWER-1',
          'high',
          'Low supply voltage',
          `Voltage ${tick.value.toFixed(2)}V.`,
          'Check power adapter and battery health. Low voltage can reduce cooling capacity during transport.',
          now
        )
      )
    }
  }

  if (tick.metric === 'fan_speed' && tick.value < 1200 && state.lastTemp && state.lastTemp > TEMP_MAX) {
    if (shouldEmit(state, 'REG-COOL-1', now)) {
      alerts.push(
        makeAlert(
          'REG-COOL-1',
          'high',
          'Cooling fan underperforming',
          `Fan ${Math.round(tick.value)} RPM while temperature is elevated.`,
          'Inspect fan obstruction and cooling mode. High fan speed should correlate with recovery after door events.',
          now
        )
      )
    }
  }

  return alerts
}
