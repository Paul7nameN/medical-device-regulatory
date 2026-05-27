import type { Finding, ValidationResult } from '@/lib/api'
import type { LatestAnalysis } from '@/lib/context/AnalysisContext'
import { buildTelemetrySeries } from '@/lib/telemetry/extract'
import type { LiveAlert } from './types'

function ruleIdToCategory(ruleId: string): string {
  if (ruleId.includes('TEMP')) return 'TEMP'
  if (ruleId.includes('SENS')) return 'SENS'
  if (ruleId.includes('POWER')) return 'POWER'
  if (ruleId.includes('COOL')) return 'COOL'
  if (ruleId.includes('OPS')) return 'OPS'
  if (ruleId.includes('ALARM')) return 'ALARM'
  return 'OPS'
}

function alertsToFindings(alerts: LiveAlert[]): Finding[] {
  const byRule = new Map<string, LiveAlert>()
  const severityRank = { critical: 0, high: 1, medium: 2, low: 3, info: 4 }

  for (const alert of alerts) {
    const existing = byRule.get(alert.ruleId)
    if (
      !existing ||
      severityRank[alert.severity] < severityRank[existing.severity]
    ) {
      byRule.set(alert.ruleId, alert)
    }
  }

  return Array.from(byRule.values()).map((alert) => ({
    rule_id: alert.ruleId,
    rule_description: alert.title,
    category: ruleIdToCategory(alert.ruleId),
    severity: alert.severity,
    passed: false,
    message: alert.message,
    evidence: [],
    timestamp: alert.timestamp,
    remediation_hint: alert.advice,
    needs_visual_verification: false,
    data_source: 'logs' as const,
  }))
}

export function buildLiveTransportAnalysis(
  rawLogs: string[],
  alerts: LiveAlert[],
  deviceId: string
): LatestAnalysis {
  const findings = alertsToFindings(alerts)
  const critical_count = findings.filter((f) => f.severity === 'critical').length
  const failed_count = findings.length
  const passed_count = Math.max(0, 24 - failed_count)

  const validationResult: ValidationResult = {
    device_id: deviceId,
    analyzed_at: new Date().toISOString(),
    total_entries: rawLogs.length,
    summary: {},
    findings,
    passed_count,
    failed_count,
    critical_count,
  }

  const telemetrySeries = buildTelemetrySeries(rawLogs)
  const temperatureData = (telemetrySeries.temperature || []).map((point) => ({
    timestamp: point.timestamp,
    time: point.time,
    sensorA: point.value,
    sensorB: point.sensorB,
    source: point.source,
  }))

  return {
    validationResult,
    rawLogs,
    temperatureData,
    telemetrySeries,
    analyzedAt: validationResult.analyzed_at,
    deviceId,
    isPartial: false,
  }
}
