import { writeFileSync, mkdirSync } from 'fs'
import { dirname, join } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const repoRoot = join(__dirname, '..')

function fmtTs(dt) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}:${pad(dt.getSeconds())}`
}

function mulberry32(seed) {
  return function () {
    let t = (seed += 0x6d2b79f5)
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function generateSession(startMs, lineCount, intervalSec, tempFn, weights, seed) {
  const rng = mulberry32(seed)
  const events = Object.keys(weights)
  const probs = events.map((e) => weights[e])
  const sum = probs.reduce((a, b) => a + b, 0)
  const lines = []
  let dt = new Date(startMs)

  const pick = () => {
    let r = rng() * sum
    for (let i = 0; i < events.length; i++) {
      r -= probs[i]
      if (r <= 0) return events[i]
    }
    return events[events.length - 1]
  }

  for (let i = 0; i < lineCount; i++) {
    const t = tempFn(i, lineCount, seed + i)
    let kind
    if (i % 6 === 1) kind = 'TEMP_READING'
    else if (i % 6 === 2) kind = 'FAN_SPEED'
    else if (i % 6 === 3) kind = 'HUMIDITY'
    else if (i % 6 === 4) kind = 'VOLTAGE'
    else if (i % 6 === 5) kind = 'BATTERY_LEVEL'
    else kind = pick()

    let event
    if (kind === 'TEMP_READING') event = `TEMP_READING ${t.toFixed(1)}C`
    else if (kind === 'FAN_SPEED') {
      const rpm = Math.max(900, Math.min(3200, Math.round(1400 + (t - 4) * 180 + (rng() * 240 - 120))))
      event = `FAN_SPEED ${rpm}RPM`
    } else if (kind === 'HUMIDITY') event = `HUMIDITY ${Math.round(35 + rng() * 45)}%`
    else if (kind === 'VOLTAGE') {
      const v = 12.4 - (i / lineCount) * 0.6 + (rng() * 0.16 - 0.08)
      event = `VOLTAGE ${v.toFixed(2)}V`
    } else if (kind === 'BATTERY_LEVEL') {
      const b = 99.5 - (i / lineCount) * 18 + (rng() * 0.6 - 0.3)
      event = `BATTERY_LEVEL ${b.toFixed(1)}%`
    } else if (kind === 'SENSOR_TIMEOUT') event = 'SENSOR_TIMEOUT SECONDARY_SENSOR'
    else event = kind

    lines.push(`${fmtTs(dt)} ${event}\n`)
    dt = new Date(dt.getTime() + intervalSec * 1000)
  }
  return lines.join('')
}

function tempStable(i, n, seed) {
  const r = mulberry32(seed + i)
  const base = 4.2 + (i / n) * 2.8
  return Math.max(2.5, Math.min(7.8, base + (r() * 0.8 - 0.4)))
}

function tempExcursion(i, n, seed) {
  const r = mulberry32(seed + i)
  const third = Math.floor(n / 3)
  if (i < third) return 4.5 + r() * 1.5
  if (i < 2 * third) return 7.5 + r() * 2.5
  return 9.5 + r() * 2.5
}

const weightsStable = {
  DOOR_OPEN: 0.08,
  DOOR_CLOSE: 0.08,
  ALARM_TRIGGERED: 0.04,
  TEMP_WARNING: 0.03,
  COOLING_RECOVERY_START: 0.05,
  DEVICE_START: 0.04,
  TELEMETRY_SYNC_FAILED: 0.03,
  SENSOR_TIMEOUT: 0.02,
  TEMP_READING: 0.25,
  FAN_SPEED: 0.12,
  HUMIDITY: 0.1,
  VOLTAGE: 0.08,
  BATTERY_LEVEL: 0.08,
}

const weightsCritical = {
  DOOR_OPEN: 0.12,
  DOOR_CLOSE: 0.1,
  ALARM_TRIGGERED: 0.09,
  TEMP_WARNING: 0.1,
  COOLING_RECOVERY_START: 0.08,
  DEVICE_START: 0.04,
  TELEMETRY_SYNC_FAILED: 0.06,
  SENSOR_TIMEOUT: 0.08,
  TEMP_READING: 0.15,
  FAN_SPEED: 0.08,
  HUMIDITY: 0.06,
  VOLTAGE: 0.07,
  BATTERY_LEVEL: 0.07,
}

const sessions = [
  {
    name: 'medical_device_logs_1000_setB_stable.txt',
    start: new Date('2026-05-20T08:00:00').getTime(),
    tempFn: tempStable,
    weights: weightsStable,
    seed: 42,
  },
  {
    name: 'medical_device_logs_1000_setC_excursion.txt',
    start: new Date('2026-05-22T10:00:00').getTime(),
    tempFn: tempExcursion,
    weights: weightsCritical,
    seed: 77,
  },
]

const outDirs = [
  join(repoRoot, 'docs', 'user-guide', 'examples'),
  String.raw`C:\Users\Daniel-NicolaeVisa\Downloads\OneDrive_1_5-18-2026`,
]

for (const s of sessions) {
  const content = generateSession(s.start, 1000, 9, s.tempFn, s.weights, s.seed)
  for (const dir of outDirs) {
    try {
      mkdirSync(dir, { recursive: true })
      const path = join(dir, s.name)
      writeFileSync(path, content, 'utf8')
      console.log('Wrote', path)
    } catch (e) {
      console.warn('Skip', dir, e.message)
    }
  }
}
