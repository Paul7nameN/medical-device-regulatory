import { useState, useMemo, useCallback, useEffect } from 'react'
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
  Brush,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle, Button, Badge } from '@/components/ui'
import { Thermometer, RefreshCw, Minus, Plus, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useTheme } from '@/lib/context/ThemeContext'

export type TemperatureDataSource = 'log_file' | 'chart_image'

export interface TemperatureDataPoint {
  timestamp: string
  time: string
  sensorA: number
  sensorB?: number
  source?: TemperatureDataSource
}

interface ChartDataPoint extends TemperatureDataPoint {
  safeMin: number
  safeMax: number
  safeRangeBand: number
  excursionA?: number
  excursionB?: number
  discrepancy?: number
  hasDiscrepancy: boolean
}

interface TemperatureChartProps {
  data: TemperatureDataPoint[]
  title?: string
  safeRange?: { min: number; max: number }
  showControls?: boolean
  className?: string
}

const DEFAULT_SAFE_RANGE = { min: 2, max: 8 }
const DISCREPANCY_THRESHOLD = 0.5

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: Array<{
    value: number
    color: string
    name: string
    dataKey?: string
    payload?: ChartDataPoint
  }>
  label?: string
}) {
  if (active && payload && payload.length) {
    const pointData = payload[0]?.payload

    return (
      <div className="bg-white dark:bg-card border border-border rounded-lg shadow-lg p-3 min-w-[180px]">
        <p className="text-sm font-medium text-foreground mb-2">{label}</p>
         {payload.map((entry, index) => {
           const dataKey = entry.dataKey
           if (
             !dataKey ||
             dataKey === 'safeMin' ||
             dataKey === 'safeRangeBand' ||
             dataKey === 'excursionA' ||
             dataKey === 'excursionB' ||
             dataKey === 'discrepancy'
           ) {
             return null
           }
           return (
             <p key={index} className="text-sm" style={{ color: entry.color }}>
               <span className="font-medium">{entry.name}:</span> {entry.value}°C
             </p>
           )
         })}
        {pointData?.hasDiscrepancy && (
          <div className="mt-2 pt-2 border-t border-border">
            <div className="flex items-center gap-1 text-amber-700 dark:text-amber-400">
              <AlertTriangle className="h-3.5 w-3.5" />
              <span className="text-xs font-medium">
                Discrepancy: {pointData.discrepancy?.toFixed(2)}°C
              </span>
            </div>
            <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
              Exceeds {DISCREPANCY_THRESHOLD}°C threshold (REG-SENS-3)
            </p>
          </div>
        )}
      </div>
    )
  }
  return null
}

export function TemperatureChart({
  data,
  title = 'Temperature Timeline',
  safeRange = DEFAULT_SAFE_RANGE,
  showControls = true,
  className,
}: TemperatureChartProps) {
  const [showLegend, setShowLegend] = useState(true)
  const [visibleSensors] = useState({ sensorA: true, sensorB: true })
  const [chartKey, setChartKey] = useState(0)
  const [isMobile, setIsMobile] = useState(false)
  const { theme } = useTheme()

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 640)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const hasSensorB = data.some((d) => d.sensorB !== undefined)

  const xAxisConfig = useMemo(() => {
    const pointCount = data.length
    
    if (pointCount <= 8) {
      return {
        interval: 0,
        angle: 0,
        textAnchor: 'middle' as const,
        fontSize: isMobile ? 10 : 12,
        bottomMargin: 0,
      }
    }

    const maxTicks = isMobile ? 5 : 10
    const interval = Math.ceil(pointCount / maxTicks)
    const shouldRotate = pointCount > 12

    return {
      interval: isMobile ? 'preserveStartEnd' as const : interval,
      angle: shouldRotate ? -45 : 0,
      textAnchor: shouldRotate ? 'end' as const : 'middle' as const,
      fontSize: isMobile ? 9 : (shouldRotate ? 10 : 12),
      bottomMargin: shouldRotate ? 30 : 0,
    }
  }, [data.length, isMobile])


  const handleResetZoom = useCallback(() => {
    setChartKey((prev) => prev + 1)
  }, [])

  const chartData: ChartDataPoint[] = useMemo(() => {
    return data.map((d) => {
      const discrepancy =
        d.sensorB !== undefined ? Math.abs(d.sensorA - d.sensorB) : undefined
      const hasDiscrepancy = discrepancy !== undefined && discrepancy > DISCREPANCY_THRESHOLD

      return {
        ...d,
        safeMin: safeRange.min,
        safeMax: safeRange.max,
        safeRangeBand: safeRange.max - safeRange.min,
        excursionA:
          visibleSensors.sensorA && d.sensorA > safeRange.max
            ? d.sensorA
            : visibleSensors.sensorA && d.sensorA < safeRange.min
              ? d.sensorA
              : undefined,
        excursionB:
          visibleSensors.sensorB &&
          d.sensorB !== undefined &&
          d.sensorB > safeRange.max
            ? d.sensorB
            : visibleSensors.sensorB &&
                d.sensorB !== undefined &&
                d.sensorB < safeRange.min
              ? d.sensorB
              : undefined,
        discrepancy,
        hasDiscrepancy,
      }
    })
  }, [data, safeRange, visibleSensors])

  const yDomain = useMemo(() => {
    const allValues = data
      .flatMap((d) => [d.sensorA, d.sensorB])
      .filter((v): v is number => v !== undefined)

    const min = Math.min(...allValues, safeRange.min) - 1
    const max = Math.max(...allValues, safeRange.max) + 1

    return [Math.floor(min), Math.ceil(max)]
  }, [data, safeRange])

  const chartColors = useMemo(() => {
    if (theme === 'dark') {
      return {
        grid: '#1e293b',
        tickText: '#94a3b8',
        safeRange: '#22c55e',
        safeRangeFill: '#22c55e',
        sensorA: '#22d3ee',
        sensorB: '#a78bfa',
        excursionA: '#f87171',
        excursionB: '#fb923c',
        discrepancy: '#fbbf24',
        brushStroke: '#22d3ee',
        brushFill: '#0f172a',
      }
    }
    return {
      grid: '#e2e8f0',
      tickText: '#64748b',
      safeRange: '#16a34a',
      safeRangeFill: '#16a34a',
      sensorA: '#0891b2',
      sensorB: '#7c3aed',
      excursionA: '#dc2626',
      excursionB: '#ea580c',
      discrepancy: '#f59e0b',
      brushStroke: '#0891b2',
      brushFill: '#f0fdfa',
    }
  }, [theme])

  const discrepancyPoints = useMemo(() => {
    return chartData.filter((d) => d.hasDiscrepancy).length
  }, [chartData])

  if (data.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <Thermometer className="h-5 w-5 text-primary" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center h-64 text-slate-500">
            <Thermometer className="h-12 w-12 mb-2 opacity-50" />
            <p>No temperature data available</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <Thermometer className="h-5 w-5 text-primary" />
            {title}
            <span className="text-xs font-normal text-slate-500 ml-2">
              Safe range: {safeRange.min}°C - {safeRange.max}°C
            </span>
          </CardTitle>
          {discrepancyPoints > 0 && (
            <Badge variant="high" className="w-fit">
              <AlertTriangle className="h-3 w-3 mr-1" />
              {discrepancyPoints} sensor discrepancy
              {discrepancyPoints !== 1 ? 'ies' : 'y'}
            </Badge>
          )}
        </div>
        {showControls && (
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowLegend(!showLegend)}
              className="h-8 px-2"
            >
              {showLegend ? <Minus className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleResetZoom}
              className="h-8 px-2"
              title="Reset zoom and pan"
            >
              <RefreshCw className="h-4 w-4" />
              <span className="hidden sm:inline ml-1">Reset</span>
            </Button>
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              key={chartKey}
               data={chartData}
               margin={{ top: 20, right: 30, left: 0, bottom: xAxisConfig.bottomMargin }}
             >
               <defs>
                 <linearGradient id="safeRangeGradient" x1="0" y1="0" x2="0" y2="1">
                   <stop offset="0%" stopColor={chartColors.safeRangeFill} stopOpacity={0.05} />
                   <stop offset="100%" stopColor={chartColors.safeRangeFill} stopOpacity={0.05} />
                 </linearGradient>
               </defs>
               <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
               <XAxis
                 dataKey="time"
                 tick={{ fontSize: xAxisConfig.fontSize, fill: chartColors.tickText }}
                 tickLine={false}
                 axisLine={{ stroke: chartColors.grid }}
                 interval={xAxisConfig.interval}
                 angle={xAxisConfig.angle}
                 textAnchor={xAxisConfig.textAnchor}
                 height={xAxisConfig.bottomMargin > 0 ? 50 : 30}
               />
              <YAxis
                domain={yDomain}
                tick={{ fontSize: isMobile ? 10 : 12, fill: chartColors.tickText }}
                tickLine={false}
                axisLine={{ stroke: chartColors.grid }}
                label={{
                  value: 'Temperature (°C)',
                  angle: -90,
                  position: 'insideLeft',
                  style: { textAnchor: 'middle', fill: chartColors.tickText, fontSize: isMobile ? 10 : 12 },
                }}
               />

               <Area
                 type="monotone"
                 dataKey="safeMin"
                 stackId="safeRange"
                 stroke="none"
                 fill="transparent"
                 isAnimationActive={false}
                 legendType="none"
               />
               <Area
                 type="monotone"
                 dataKey="safeRangeBand"
                 stackId="safeRange"
                 stroke="none"
                 fill="url(#safeRangeGradient)"
                 isAnimationActive={false}
                 legendType="none"
               />

               <ReferenceLine
                 y={safeRange.min}
                 stroke={chartColors.safeRange}
                 strokeDasharray="5 5"
                 strokeOpacity={0.6}
               />
               <ReferenceLine
                 y={safeRange.max}
                 stroke={chartColors.safeRange}
                 strokeDasharray="5 5"
                 strokeOpacity={0.6}
               />

                {visibleSensors.sensorA && (
                  <Line
                    type="monotone"
                    dataKey="sensorA"
                    name="Primary Temperature"
                    stroke={chartColors.sensorA}
                    strokeWidth={2}
                    dot={{ fill: chartColors.sensorA, r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                )}

                {visibleSensors.sensorB && hasSensorB && (
                  <Line
                    type="monotone"
                    dataKey="sensorB"
                    name="Secondary Temperature"
                    stroke={chartColors.sensorB}
                    strokeWidth={2}
                    dot={{ fill: chartColors.sensorB, r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                )}

                {visibleSensors.sensorA && (
                  <Line
                    type="monotone"
                    dataKey="excursionA"
                    stroke={chartColors.excursionA}
                    strokeWidth={3}
                    dot={{ fill: chartColors.excursionA, r: 4 }}
                    legendType="none"
                  />
                )}

                {visibleSensors.sensorB && hasSensorB && (
                  <Line
                    type="monotone"
                    dataKey="excursionB"
                    stroke={chartColors.excursionB}
                    strokeWidth={3}
                    dot={{ fill: chartColors.excursionB, r: 4 }}
                    legendType="none"
                  />
                )}

               {hasSensorB && (
                 <Line
                   type="monotone"
                   dataKey="discrepancy"
                   stroke="none"
                   strokeWidth={0}
                   legendType="none"
                   dot={(props) => {
                     const { cx, cy, payload } = props
                     if (!payload?.hasDiscrepancy) return <circle cx={cx} cy={cy} r={0} />
                     return (
                       <circle
                         cx={cx}
                         cy={cy}
                         r={15}
                         fill="none"
                         stroke={chartColors.discrepancy}
                         strokeWidth={2}
                         strokeDasharray="3 3"
                       />
                     )
                   }}
                />
              )}

               <Tooltip content={<CustomTooltip />} />

                <Brush
                 dataKey="time"
                 height={30}
                 stroke={chartColors.brushStroke}
                 fill={chartColors.brushFill}
                 travellerWidth={10}
               />
             </ComposedChart>
           </ResponsiveContainer>
         </div>

         {showLegend && (
           <div className="mt-4 flex flex-wrap items-center justify-center gap-6 text-sm">
             <div className="flex items-center gap-2">
               <div
                 className="w-4 h-1 rounded-full"
                 style={{ backgroundColor: chartColors.sensorA }}
               />
               <span className="text-muted-foreground">Primary Temperature</span>
             </div>
             {hasSensorB && (
               <div className="flex items-center gap-2">
                 <div
                   className="w-4 h-1 rounded-full"
                   style={{ backgroundColor: chartColors.sensorB }}
                 />
                 <span className="text-muted-foreground">Secondary Temperature</span>
               </div>
             )}
             <div className="flex items-center gap-2">
               <div
                 className="w-3 h-3 rounded-full"
                 style={{ backgroundColor: chartColors.excursionA }}
               />
               <span className="text-muted-foreground">Out of Safe Range</span>
             </div>
           </div>
         )}

           <div className="mt-4 p-3 bg-muted/40 rounded-lg text-sm text-muted-foreground">
               <p className="flex flex-wrap items-center gap-2">
                 <span className="text-xs bg-border px-2 py-0.5 rounded">Info</span>
                 <span>
                   Values outside safe range ({safeRange.min}°C - {safeRange.max}°C) are highlighted in red.
                 </span>
                 {hasSensorB && (
                   <span className="text-amber-700 dark:text-amber-400">
                      Amber circles indicate sensor discrepancies ({'>'} {DISCREPANCY_THRESHOLD}°C).
                   </span>
                 )}
               </p>
            </div>
       </CardContent>
     </Card>
   )
 }

export function TemperatureChartSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="h-5 w-48 bg-border rounded animate-pulse" />
      </CardHeader>
      <CardContent>
        <div className="h-80 bg-muted rounded-lg animate-pulse" />
      </CardContent>
    </Card>
  )
}

export function generateSampleTemperatureData(): TemperatureDataPoint[] {
  const data: TemperatureDataPoint[] = []
  const now = new Date()

  for (let i = 24; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 60 * 60 * 1000)
    const hour = time.getHours()

    let tempA = 5
    let tempB = 5.1

    if (hour >= 10 && hour < 12) {
      tempA = 9.5 + Math.random() * 2
      tempB = 9.3 + Math.random() * 2
    } else if (hour >= 3 && hour < 5) {
      tempA = 0.5 + Math.random() * 1
      tempB = 0.3 + Math.random() * 1
    } else {
      tempA = 4.5 + Math.random() * 2
      tempB = 4.4 + Math.random() * 2.2
    }

    if (hour === 14) {
      tempB = tempA + 0.7
    }

    data.push({
      timestamp: time.toISOString(),
      time: `${hour.toString().padStart(2, '0')}:00`,
      sensorA: Math.round(tempA * 10) / 10,
      sensorB: Math.round(tempB * 10) / 10,
    })
  }

  return data
}
