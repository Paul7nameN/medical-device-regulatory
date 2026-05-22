import { useMemo, useState } from 'react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Button,
} from '@/components/ui'
import { LineChart, Info } from 'lucide-react'
import {
  TELEMETRY_METRICS,
  TELEMETRY_METRIC_BY_ID,
  type TelemetryMetricId,
  type TelemetryDataPoint,
} from '@/lib/telemetry/metrics'
import { getAvailableMetrics } from '@/lib/telemetry/extract'
import { TemperatureChart, TemperatureChartSkeleton } from '@/components/TemperatureChart'
import type { TemperatureDataPoint } from '@/components/TemperatureChart'
import { TelemetryLineChart, TelemetryLineChartSkeleton } from '@/components/TelemetryLineChart'
import { REGULATORY_CONSTANTS } from '@/lib/constants'

interface GraphSectionProps {
  telemetrySeries: Partial<Record<TelemetryMetricId, TelemetryDataPoint[]>>
  isLoading?: boolean
}

function telemetryToTemperaturePoints(
  points: TelemetryDataPoint[]
): TemperatureDataPoint[] {
  return points.map((point) => ({
    timestamp: point.timestamp,
    time: point.time,
    sensorA: point.value,
    sensorB: point.sensorB,
    source: point.source,
  }))
}

export function GraphSection({ telemetrySeries, isLoading }: GraphSectionProps) {
  const available = useMemo(
    () => getAvailableMetrics(telemetrySeries),
    [telemetrySeries]
  )

  const [selectedMetric, setSelectedMetric] = useState<TelemetryMetricId | null>(null)

  const activeMetric = selectedMetric && available.includes(selectedMetric)
    ? selectedMetric
    : available[0] ?? null

  const config = activeMetric ? TELEMETRY_METRIC_BY_ID[activeMetric] : null
  const activeData = activeMetric ? telemetrySeries[activeMetric] ?? [] : []

  const stats = useMemo(() => {
    if (!activeData.length) return null
    const values = activeData.map((d) => d.value)
    const avg = values.reduce((a, b) => a + b, 0) / values.length
    const min = Math.min(...values)
    const max = Math.max(...values)
    const logCount = activeData.filter((d) => d.source === 'log_file').length
    const chartCount = activeData.filter((d) => d.source === 'chart_image').length
    return { avg, min, max, logCount, chartCount, count: activeData.length }
  }, [activeData])

  if (available.length === 0) {
    return (
      <Card className="border-dashed border-border/80 bg-muted/20">
        <CardContent className="p-8 text-center">
          <LineChart className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
          <h3 className="text-lg font-semibold text-foreground mb-2">No graph data available</h3>
          <p className="text-sm text-muted-foreground max-w-md mx-auto">
            Upload a device log file (.txt) to see temperature, humidity, voltage, fan speed, and
            battery charts. Chart images (.png) add temperature series from visual analysis.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3">
        <p className="text-sm text-muted-foreground">
          Select a telemetry series extracted from your analysis. Data comes from log lines and, for
          temperature, from chart images when uploaded.
        </p>
        <div className="flex flex-wrap gap-2">
          {TELEMETRY_METRICS.filter((m) => available.includes(m.id)).map((metric) => {
            const Icon = metric.icon
            const count = telemetrySeries[metric.id]?.length ?? 0
            const isActive = activeMetric === metric.id
            return (
              <Button
                key={metric.id}
                variant={isActive ? 'default' : 'outline'}
                size="sm"
                className="touch-target gap-2"
                onClick={() => setSelectedMetric(metric.id)}
              >
                <Icon className="h-4 w-4" />
                {metric.label}
                <Badge variant="secondary" className="ml-1 text-xs">
                  {count}
                </Badge>
              </Button>
            )
          })}
        </div>
      </div>

      {config && stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Average</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold" style={{ color: config.color }}>
                {stats.avg.toFixed(1)}
                {config.unit}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Min / Max</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-lg font-semibold text-foreground">
                {stats.min.toFixed(1)} – {stats.max.toFixed(1)}
                {config.unit}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Readings</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-foreground">{stats.count}</p>
              <p className="text-xs text-muted-foreground">data points</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Sources</CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground space-y-1">
              {stats.logCount > 0 && <p>Log file: {stats.logCount}</p>}
              {stats.chartCount > 0 && <p>Chart image: {stats.chartCount}</p>}
              {stats.logCount === 0 && stats.chartCount === 0 && <p>—</p>}
            </CardContent>
          </Card>
        </div>
      )}

      {isLoading ? (
        activeMetric === 'temperature' ? (
          <TemperatureChartSkeleton />
        ) : (
          <TelemetryLineChartSkeleton />
        )
      ) : activeMetric === 'temperature' ? (
        <TemperatureChart
          data={telemetryToTemperaturePoints(activeData)}
          safeRange={REGULATORY_CONSTANTS.safeTemperatureRange}
          title="Temperature timeline"
        />
      ) : config ? (
        <TelemetryLineChart data={activeData} metric={config} />
      ) : null}

      {config && (
        <Card className="border-border bg-muted/40">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Info className="h-4 w-4 text-muted-foreground" />
              About {config.label}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{config.description}</p>
            <p className="text-xs text-muted-foreground mt-2">
              Parsed from log type <code className="bg-muted px-1 rounded">{config.logType}</code>
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
