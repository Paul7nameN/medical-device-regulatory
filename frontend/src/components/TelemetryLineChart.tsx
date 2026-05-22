import { useMemo, useState, useCallback, useEffect } from 'react'
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea,
  ComposedChart,
  Brush,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle, Button } from '@/components/ui'
import { RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useTheme } from '@/lib/context/ThemeContext'
import type { TelemetryDataPoint, TelemetryMetricConfig } from '@/lib/telemetry/metrics'

interface TelemetryLineChartProps {
  data: TelemetryDataPoint[]
  metric: TelemetryMetricConfig
  className?: string
}

export function TelemetryLineChart({ data, metric, className }: TelemetryLineChartProps) {
  const [chartKey, setChartKey] = useState(0)
  const [isMobile, setIsMobile] = useState(false)
  const { theme } = useTheme()
  const Icon = metric.icon

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 640)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const xAxisConfig = useMemo(() => {
    const pointCount = data.length
    if (pointCount <= 8) {
      return { interval: 0, angle: 0, textAnchor: 'middle' as const, fontSize: isMobile ? 10 : 12, bottomMargin: 0 }
    }
    const maxTicks = isMobile ? 5 : 10
    const interval = Math.ceil(pointCount / maxTicks)
    const shouldRotate = pointCount > 12
    return {
      interval: isMobile ? ('preserveStartEnd' as const) : interval,
      angle: shouldRotate ? -45 : 0,
      textAnchor: shouldRotate ? ('end' as const) : ('middle' as const),
      fontSize: isMobile ? 9 : shouldRotate ? 10 : 12,
      bottomMargin: shouldRotate ? 30 : 0,
    }
  }, [data.length, isMobile])

  const yDomain = useMemo(() => {
    const values = data.map((d) => d.value)
    const min = Math.min(...values)
    const max = Math.max(...values)
    const padding = (max - min) * 0.1 || 1
    return [Math.floor(min - padding), Math.ceil(max + padding)]
  }, [data])

  const chartColors = useMemo(() => {
    if (theme === 'dark') {
      return { grid: '#1e293b', tickText: '#94a3b8', line: metric.color, brushStroke: metric.color, brushFill: '#0f172a' }
    }
    return { grid: '#e2e8f0', tickText: '#64748b', line: metric.color, brushStroke: metric.color, brushFill: '#f0f9ff' }
  }, [theme, metric.color])

  const handleResetZoom = useCallback(() => setChartKey((k) => k + 1), [])

  if (data.length === 0) {
    return null
  }

  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-base font-medium flex items-center gap-2">
          <Icon className="h-5 w-5" style={{ color: metric.color }} />
          {metric.label} timeline
          {metric.safeRange && (
            <span className="text-xs font-normal text-muted-foreground ml-2">
              Safe: {metric.safeRange.min}
              {metric.unit} – {metric.safeRange.max}
              {metric.unit}
            </span>
          )}
        </CardTitle>
        <Button variant="ghost" size="sm" onClick={handleResetZoom} className="h-8 px-2" title="Reset zoom">
          <RefreshCw className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              key={chartKey}
              data={data}
              margin={{ top: 20, right: 30, left: 0, bottom: xAxisConfig.bottomMargin }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
              <XAxis
                dataKey="time"
                tick={{ fontSize: xAxisConfig.fontSize, fill: chartColors.tickText }}
                tickLine={false}
                axisLine={{ stroke: chartColors.grid }}
                interval={xAxisConfig.interval}
                angle={xAxisConfig.angle}
                textAnchor={xAxisConfig.textAnchor}
              />
              <YAxis
                tick={{ fontSize: 12, fill: chartColors.tickText }}
                tickLine={false}
                axisLine={{ stroke: chartColors.grid }}
                domain={yDomain}
                tickFormatter={(v) => `${v}${metric.unit}`}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (!active || !payload?.length) return null
                  const point = payload[0].payload as TelemetryDataPoint
                  return (
                    <div className="bg-card border border-border rounded-lg shadow-lg p-3 text-sm">
                      <p className="font-medium mb-1">{label}</p>
                      <p style={{ color: metric.color }}>
                        {metric.label}: {point.value}
                        {metric.unit}
                      </p>
                      {point.source && (
                        <p className="text-xs text-muted-foreground mt-1">Source: {point.source}</p>
                      )}
                    </div>
                  )
                }}
              />
              {metric.safeRange && (
                <ReferenceArea
                  y1={metric.safeRange.min}
                  y2={metric.safeRange.max}
                  fill="#22c55e"
                  fillOpacity={0.08}
                  stroke="#22c55e"
                  strokeOpacity={0.3}
                />
              )}
              <Line
                type="monotone"
                dataKey="value"
                stroke={chartColors.line}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
              <Brush
                dataKey="time"
                height={24}
                stroke={chartColors.brushStroke}
                fill={chartColors.brushFill}
                travellerWidth={8}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

export function TelemetryLineChartSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="h-5 w-48 bg-border rounded animate-pulse" />
      </CardHeader>
      <CardContent>
        <div className="h-80 bg-border/50 rounded animate-pulse" />
      </CardContent>
    </Card>
  )
}
