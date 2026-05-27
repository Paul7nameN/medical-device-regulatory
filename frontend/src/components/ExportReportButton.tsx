import { useCallback, useMemo, useRef, useState } from 'react'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
import { Button, Badge } from '@/components/ui'
import { Download, Loader2 } from 'lucide-react'
import type { LatestAnalysis } from '@/lib/context/AnalysisContext'
import type { TelemetryDataPoint, TelemetryMetricId } from '@/lib/telemetry/metrics'
import { TELEMETRY_METRIC_BY_ID, TELEMETRY_METRICS } from '@/lib/telemetry/metrics'
import { TemperatureChart } from '@/components/TemperatureChart'
import type { TemperatureDataPoint } from '@/components/TemperatureChart'
import { TelemetryLineChart } from '@/components/TelemetryLineChart'
import { REGULATORY_CONSTANTS } from '@/lib/constants'

interface ExportReportButtonProps {
  analysis: LatestAnalysis
  complianceScore: number
  severityCounts?: { critical: number; high: number; medium: number; low: number; info?: number }
  telemetrySeries: Partial<Record<TelemetryMetricId, TelemetryDataPoint[]>>
  className?: string
}

function telemetryToTemperaturePoints(points: TelemetryDataPoint[]): TemperatureDataPoint[] {
  return points.map((point) => ({
    timestamp: point.timestamp,
    time: point.time,
    sensorA: point.value,
    sensorB: point.sensorB,
    source: point.source,
  }))
}

function formatDateTime(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString()
}

export function ExportReportButton({
  analysis,
  complianceScore,
  severityCounts,
  telemetrySeries,
  className,
}: ExportReportButtonProps) {
  const [isExporting, setIsExporting] = useState(false)
  const reportRef = useRef<HTMLDivElement | null>(null)

  const chartsToInclude = useMemo(() => {
    const available = TELEMETRY_METRICS.filter((m) => (telemetrySeries[m.id]?.length ?? 0) > 0).map((m) => m.id)
    const availableSet = new Set<TelemetryMetricId>(available)

    // Mandatory charts:
    // - temperature if available
    // - fan_speed if available
    // Then add one more available metric (up to 3 charts total).
    const result: TelemetryMetricId[] = []
    if (availableSet.has('temperature')) result.push('temperature')
    if (availableSet.has('fan_speed')) result.push('fan_speed')

    for (const m of TELEMETRY_METRICS) {
      if (result.length >= 3) break
      if (result.includes(m.id)) continue
      if (availableSet.has(m.id)) result.push(m.id)
    }

    return result
  }, [telemetrySeries])

  const exportPdf = useCallback(async () => {
    const node = reportRef.current
    if (!node || isExporting) return

    setIsExporting(true)
    try {
      const canvas = await html2canvas(node, {
        backgroundColor: '#ffffff',
        scale: 2,
        useCORS: true,
      })

      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF({ orientation: 'p', unit: 'pt', format: 'a4' })

      const pageWidth = pdf.internal.pageSize.getWidth()
      const pageHeight = pdf.internal.pageSize.getHeight()

      const imgWidth = pageWidth
      const imgHeight = (canvas.height * imgWidth) / canvas.width

      let y = 0
      pdf.addImage(imgData, 'PNG', 0, y, imgWidth, imgHeight)

      while (imgHeight + y > pageHeight) {
        y -= pageHeight
        pdf.addPage()
        pdf.addImage(imgData, 'PNG', 0, y, imgWidth, imgHeight)
      }

      const filename = `med-therm-report_${analysis.deviceId || 'device'}_${analysis.analyzedAt.slice(0, 10)}.pdf`
      pdf.save(filename)
    } finally {
      setIsExporting(false)
    }
  }, [analysis.analyzedAt, analysis.deviceId, isExporting])

  return (
    <>
      <Button
        onClick={exportPdf}
        disabled={isExporting}
        variant="outline"
        size="sm"
        className={className}
      >
        {isExporting ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Exporting…
          </>
        ) : (
          <>
            <Download className="h-4 w-4 mr-2" />
            Export PDF
          </>
        )}
      </Button>

      {/* Offscreen printable layout */}
      <div className="fixed left-[-10000px] top-0">
        <div
          ref={reportRef}
          style={{ width: 794 }}
          className="bg-white text-black p-8 space-y-6"
        >
          <div className="flex items-start justify-between gap-6">
            <div>
              <h1 className="text-2xl font-bold">MED-THERM Compliance Report</h1>
              <p className="text-sm text-slate-600">
                Device: <span className="font-medium">{analysis.deviceId || 'Unknown'}</span>
              </p>
              <p className="text-sm text-slate-600">
                Analyzed: <span className="font-medium">{formatDateTime(analysis.analyzedAt)}</span>
              </p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold">{complianceScore}%</div>
              <div className="text-xs text-slate-600">Compliance score (weighted)</div>
            </div>
          </div>

          {severityCounts && (
            <div className="grid grid-cols-4 gap-3">
              {(
                [
                  ['Critical', severityCounts.critical, 'bg-red-50 text-red-700 border-red-100'],
                  ['High', severityCounts.high, 'bg-orange-50 text-orange-700 border-orange-100'],
                  ['Medium', severityCounts.medium, 'bg-yellow-50 text-yellow-700 border-yellow-100'],
                  ['Low', severityCounts.low, 'bg-green-50 text-green-700 border-green-100'],
                ] as const
              ).map(([label, value, cls]) => (
                <div key={label} className={`border rounded p-3 ${cls}`}>
                  <div className="text-2xl font-bold">{value}</div>
                  <div className="text-xs">{label} violations</div>
                </div>
              ))}
            </div>
          )}

          {analysis.aiAnalysis?.natural_language_summary ? (
            <div className="border border-slate-200 rounded-lg bg-white px-4 py-3">
              <div className="text-sm font-medium text-black mb-2">AI Summary</div>
              <p
                className="text-sm text-black whitespace-pre-line"
                style={{ lineHeight: 1.35, wordBreak: 'break-word' }}
              >
                {analysis.aiAnalysis.natural_language_summary}
              </p>
            </div>
          ) : null}

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Key charts</h2>
              <div className="flex flex-wrap gap-2">
                {chartsToInclude.map((id) => (
                  <Badge key={id} variant="secondary">
                    {TELEMETRY_METRIC_BY_ID[id].label}
                  </Badge>
                ))}
              </div>
            </div>

            {chartsToInclude.map((metricId) => {
              const points = telemetrySeries[metricId] ?? []
              if (points.length === 0) return null

              if (metricId === 'temperature') {
                return (
                  <div key={metricId} className="border rounded p-3">
                    <div className="text-sm font-medium mb-2">Temperature</div>
                    <TemperatureChart
                      data={telemetryToTemperaturePoints(points)}
                      safeRange={REGULATORY_CONSTANTS.safeTemperatureRange}
                      title="Temperature timeline"
                      showControls={false}
                    />
                  </div>
                )
              }

              const config = TELEMETRY_METRIC_BY_ID[metricId]
              return (
                <div key={metricId} className="border rounded p-3">
                  <div className="text-sm font-medium mb-2">{config.label}</div>
                  <TelemetryLineChart data={points} metric={config} />
                </div>
              )
            })}
          </div>

          <div className="pt-2 border-t text-xs text-slate-500">
            Note: This report is generated automatically from uploaded data. The compliance score is indicative and may
            not reflect all real-world conditions; always validate with raw evidence and regulatory procedures.
          </div>
        </div>
      </div>
    </>
  )
}

