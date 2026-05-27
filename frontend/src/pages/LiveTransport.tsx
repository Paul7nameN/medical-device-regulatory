import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui'
import { Play, Square, Radio, Thermometer, Upload, FileText, X, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { reportsApi } from '@/lib/api'
import { useAnalysis } from '@/lib/context/AnalysisContext'
import { TemperatureChart } from '@/components/TemperatureChart'
import type { TemperatureDataPoint } from '@/components/TemperatureChart'
import { TelemetryLineChart } from '@/components/TelemetryLineChart'
import { TELEMETRY_METRIC_BY_ID } from '@/lib/telemetry/metrics'
import { REGULATORY_CONSTANTS } from '@/lib/constants'
import { LiveAlertFeed } from '@/components/LiveTransport/LiveAlertFeed'
import {
  appendPoint,
  createLiveTick,
  LIVE_MAX_POINTS,
  LIVE_TICK_INTERVAL_MS,
  metricSeriesFromTicks,
} from '@/lib/live/simulator'
import { parseLogLinesToReplayBatches, readLogFile } from '@/lib/live/logReplay'
import { buildLiveTransportAnalysis } from '@/lib/live/buildReport'
import { createMonitorState, evaluateLiveTick } from '@/lib/live/monitor'
import type {
  LiveAlert,
  LiveScenario,
  LiveSourceMode,
  LiveSpeedMultiplier,
  LiveTelemetryTick,
} from '@/lib/live/types'
import { LIVE_SPEED_OPTIONS } from '@/lib/live/types'
import type { TelemetryDataPoint } from '@/lib/telemetry/metrics'

const SCENARIO_LABELS: Record<LiveScenario, string> = {
  stable: 'Stable transport (demo)',
  excursion: 'Door + temperature excursion',
  stress: 'Sensor + power stress',
}

export function LiveTransportPage() {
  const navigate = useNavigate()
  const { addAnalysis, refreshHistory, switchAnalysis, setIsAnalyzing } = useAnalysis()

  const [isRunning, setIsRunning] = useState(false)
  const [isFinalizingReport, setIsFinalizingReport] = useState(false)
  const [scenario, setScenario] = useState<LiveScenario>('excursion')
  const [sourceMode, setSourceMode] = useState<LiveSourceMode>('simulated')
  const [speed, setSpeed] = useState<LiveSpeedMultiplier>(1)
  const [deviceId, setDeviceId] = useState('MED-UNIT-DEMO-01')
  const [logFileName, setLogFileName] = useState<string | null>(null)
  const [logLineCount, setLogLineCount] = useState(0)
  const [ticks, setTicks] = useState<LiveTelemetryTick[]>([])
  const [alerts, setAlerts] = useState<LiveAlert[]>([])
  const [tickIndex, setTickIndex] = useState(0)
  const [startedAt, setStartedAt] = useState<number | null>(null)
  const [elapsedSec, setElapsedSec] = useState(0)

  const monitorRef = useRef(createMonitorState())
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const elapsedRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const simIndexRef = useRef(0)
  const logIndexRef = useRef(0)
  const logBatchesRef = useRef<LiveTelemetryTick[][]>([])
  const logLinesRef = useRef<string[]>([])
  const alertsRef = useRef<LiveAlert[]>([])
  const scenarioRef = useRef(scenario)
  const sourceModeRef = useRef(sourceMode)
  const speedRef = useRef(speed)
  const sessionStartRef = useRef(0)
  const fileInputRef = useRef<HTMLInputElement>(null)

  scenarioRef.current = scenario
  sourceModeRef.current = sourceMode
  speedRef.current = speed

  useEffect(() => {
    alertsRef.current = alerts
  }, [alerts])

  const finalizeLogTransport = useCallback(async () => {
    const lines = logLinesRef.current
    if (lines.length === 0 || isFinalizingReport) return

    setIsFinalizingReport(true)
    setIsAnalyzing(true)

    if (elapsedRef.current) {
      clearInterval(elapsedRef.current)
      elapsedRef.current = null
    }

    try {
      await reportsApi.generateFromLogs({
        raw_logs: lines,
        device_id: deviceId,
      })
      await refreshHistory()
      switchAnalysis(0)
    } catch (error) {
      console.warn('Live transport: backend report failed, using local summary', error)
      addAnalysis(buildLiveTransportAnalysis(lines, alertsRef.current, deviceId))
    } finally {
      setIsAnalyzing(false)
      setIsFinalizingReport(false)
      navigate('/')
    }
  }, [
    addAnalysis,
    deviceId,
    isFinalizingReport,
    navigate,
    refreshHistory,
    setIsAnalyzing,
    switchAnalysis,
  ])

  const finalizeLogTransportRef = useRef(finalizeLogTransport)
  finalizeLogTransportRef.current = finalizeLogTransport

  const temperatureData: TemperatureDataPoint[] = useMemo(() => {
    return metricSeriesFromTicks(ticks, 'temperature').map((p) => ({
      timestamp: p.timestamp,
      time: p.time,
      sensorA: p.value,
      source: 'log_file' as const,
    }))
  }, [ticks])

  const fanData: TelemetryDataPoint[] = useMemo(
    () => metricSeriesFromTicks(ticks, 'fan_speed'),
    [ticks]
  )
  const humidityData: TelemetryDataPoint[] = useMemo(
    () => metricSeriesFromTicks(ticks, 'humidity'),
    [ticks]
  )

  const processBatch = useCallback((batch: LiveTelemetryTick[]) => {
    const now = Date.now()
    const newAlerts: LiveAlert[] = []

    setTicks((prev) => {
      let combined = prev
      for (const tick of batch) {
        combined = appendPoint(combined, tick, LIVE_MAX_POINTS * 4)
        newAlerts.push(...evaluateLiveTick(tick, monitorRef.current, now))
      }
      return combined
    })

    if (newAlerts.length > 0) {
      setAlerts((prev) => [...newAlerts, ...prev].slice(0, 50))
    }
  }, [])

  const runOneTick = useCallback(() => {
    if (sourceModeRef.current === 'log_file') {
      const batches = logBatchesRef.current
      const idx = logIndexRef.current
      if (idx >= batches.length) {
        return false
      }
      processBatch(batches[idx])
      logIndexRef.current = idx + 1
      setTickIndex(logIndexRef.current)
      return logIndexRef.current < batches.length
    }

    const index = simIndexRef.current
    const batch = createLiveTick(
      scenarioRef.current,
      index,
      sessionStartRef.current,
      1000 + index
    )
    processBatch(batch)
    simIndexRef.current = index + 1
    setTickIndex(simIndexRef.current)
    return true
  }, [processBatch])

  const clearTickInterval = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  const scheduleTickLoop = useCallback(() => {
    clearTickInterval()
    const ms = LIVE_TICK_INTERVAL_MS / speedRef.current
    intervalRef.current = setInterval(() => {
      const hasMore = runOneTick()
      if (sourceModeRef.current === 'log_file' && !hasMore) {
        clearTickInterval()
        setIsRunning(false)
        void finalizeLogTransportRef.current()
      }
    }, ms)
  }, [clearTickInterval, runOneTick])

  const stopTransport = useCallback(() => {
    setIsRunning(false)
    clearTickInterval()
    if (elapsedRef.current) {
      clearInterval(elapsedRef.current)
      elapsedRef.current = null
    }
  }, [clearTickInterval])

  const startTransport = useCallback(() => {
    stopTransport()
    setTicks([])
    setAlerts([])
    setTickIndex(0)
    setElapsedSec(0)
    simIndexRef.current = 0
    logIndexRef.current = 0
    monitorRef.current = createMonitorState()

    if (sourceMode === 'log_file' && logBatchesRef.current.length === 0) {
      return
    }

    const start = Date.now()
    sessionStartRef.current = start
    setStartedAt(start)
    setIsRunning(true)

    elapsedRef.current = setInterval(() => {
      setElapsedSec(Math.floor((Date.now() - start) / 1000))
    }, 1000)

    runOneTick()
  }, [sourceMode, stopTransport, runOneTick])

  useEffect(() => {
    if (!isRunning) return
    scheduleTickLoop()
  }, [speed, isRunning, scheduleTickLoop])

  useEffect(() => {
    return () => stopTransport()
  }, [stopTransport])

  const handleLogUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    try {
      const { lines, name } = await readLogFile(file)
      logLinesRef.current = lines
      logBatchesRef.current = parseLogLinesToReplayBatches(lines)
      setLogFileName(name)
      setLogLineCount(lines.length)
      setSourceMode('log_file')
      setTicks([])
      setAlerts([])
      setTickIndex(0)
    } catch {
      setLogFileName(null)
      setLogLineCount(0)
      logBatchesRef.current = []
      logLinesRef.current = []
    }

    e.target.value = ''
  }, [])

  const clearLogFile = useCallback(() => {
    if (isRunning) return
    logBatchesRef.current = []
    logLinesRef.current = []
    setLogFileName(null)
    setLogLineCount(0)
    setSourceMode('simulated')
  }, [isRunning])

  const formatElapsed = (sec: number) => {
    const m = Math.floor(sec / 60)
    const s = sec % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  const canStart =
    sourceMode === 'simulated' || (sourceMode === 'log_file' && logBatchesRef.current.length > 0)

  return (
    <div className="space-y-6 relative">
      {isFinalizingReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <Card className="w-full max-w-sm mx-4">
            <CardContent className="p-8 text-center">
              <Loader2 className="h-10 w-10 mx-auto mb-4 text-primary animate-spin" />
              <h3 className="text-lg font-semibold mb-2">Transport complete</h3>
              <p className="text-sm text-muted-foreground">
                Generating compliance report and opening Home…
              </p>
            </CardContent>
          </Card>
        </div>
      )}
      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground font-heading flex items-center gap-2">
            <Radio className="h-8 w-8 text-primary" />
            Live Transport
          </h1>
          <p className="text-muted-foreground mt-1">
            Simulated telemetry or replay from a log file. Rule checks run on each tick; adjust speed
            with ×2 / ×5 / ×10 / ×25.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {isRunning && (
            <Badge variant="critical" className="animate-pulse gap-1">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              LIVE · ×{speed}
            </Badge>
          )}
          {startedAt && (
            <Badge variant="outline">
              {formatElapsed(elapsedSec)} · {tickIndex} ticks
            </Badge>
          )}
        </div>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium">Session control</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col sm:flex-row flex-wrap gap-4 items-end">
            <div className="space-y-1 min-w-[200px]">
              <label className="text-xs text-muted-foreground">Device ID</label>
              <input
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={deviceId}
                onChange={(e) => setDeviceId(e.target.value)}
                disabled={isRunning}
                placeholder="MED-UNIT-…"
              />
            </div>

            <div className="space-y-1 min-w-[220px]">
              <label className="text-xs text-muted-foreground">Data source</label>
              <Select
                value={sourceMode}
                onValueChange={(v) => {
                  if (isRunning) return
                  setSourceMode(v as LiveSourceMode)
                }}
                disabled={isRunning}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="simulated">Built-in scenario</SelectItem>
                  <SelectItem value="log_file" disabled={!logFileName}>
                    Log file replay{logFileName ? '' : ' (upload first)'}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {sourceMode === 'simulated' && (
              <div className="space-y-1 min-w-[220px]">
                <label className="text-xs text-muted-foreground">Scenario</label>
                <Select
                  value={scenario}
                  onValueChange={(v) => setScenario(v as LiveScenario)}
                  disabled={isRunning}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(Object.keys(SCENARIO_LABELS) as LiveScenario[]).map((key) => (
                      <SelectItem key={key} value={key}>
                        {SCENARIO_LABELS[key]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Simulation speed</label>
              <div className="flex gap-1">
                {LIVE_SPEED_OPTIONS.map((mult) => (
                  <Button
                    key={mult}
                    type="button"
                    size="sm"
                    variant={speed === mult ? 'default' : 'outline'}
                    className="min-w-[3rem]"
                    onClick={() => setSpeed(mult)}
                  >
                    ×{mult}
                  </Button>
                ))}
              </div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row flex-wrap gap-3 items-center pt-2 border-t border-border">
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.log"
              className="hidden"
              onChange={handleLogUpload}
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={isRunning}
              onClick={() => fileInputRef.current?.click()}
              className="touch-target"
            >
              <Upload className="h-4 w-4 mr-2" />
              Upload log file
            </Button>

            {logFileName && (
              <div className="flex items-center gap-2 text-sm">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium truncate max-w-[200px]">{logFileName}</span>
                <Badge variant="secondary">{logLineCount} lines</Badge>
                {!isRunning && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={clearLogFile}
                    aria-label="Remove log file"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            )}

            <div className="flex gap-2 sm:ml-auto">
              {!isRunning ? (
                <Button onClick={startTransport} disabled={!canStart} className="touch-target">
                  <Play className="h-4 w-4 mr-2" />
                  Start transport
                </Button>
              ) : (
                <Button onClick={stopTransport} variant="destructive" className="touch-target">
                  <Square className="h-4 w-4 mr-2" />
                  Stop
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {!isRunning && ticks.length === 0 ? (
        <Card className="border-dashed border-border/80 bg-muted/20">
          <CardContent className="p-12 text-center">
            <Thermometer className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
            <h3 className="text-lg font-semibold mb-2">Ready to monitor</h3>
            <p className="text-sm text-muted-foreground max-w-md mx-auto">
              Pick a <strong>scenario</strong> or <strong>upload a .txt log</strong>, set speed, then press{' '}
              <strong>Start transport</strong>. Charts update in real time; violations show with advice.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2 space-y-6">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span
                className={cn(
                  'px-2 py-0.5 rounded',
                  sourceMode === 'log_file' ? 'bg-blue-100 dark:bg-blue-950/40' : 'bg-muted'
                )}
              >
                {sourceMode === 'log_file' ? `Replay: ${logFileName ?? 'log'}` : `Scenario: ${SCENARIO_LABELS[scenario]}`}
              </span>
            </div>
            <TemperatureChart
              data={temperatureData}
              safeRange={REGULATORY_CONSTANTS.safeTemperatureRange}
              title={`Live temperature · ${deviceId}`}
              showControls={false}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {fanData.length > 0 && (
                <TelemetryLineChart data={fanData} metric={TELEMETRY_METRIC_BY_ID.fan_speed} />
              )}
              {humidityData.length > 0 && (
                <TelemetryLineChart data={humidityData} metric={TELEMETRY_METRIC_BY_ID.humidity} />
              )}
            </div>
          </div>
          <LiveAlertFeed alerts={alerts} />
        </div>
      )}
    </div>
  )
}

export default LiveTransportPage
