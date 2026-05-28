import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  useRef,
  type ReactNode,
} from 'react'
import { useNavigate } from 'react-router-dom'
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
import { reportsApi } from '@/lib/api'
import type { TemperatureDataPoint } from '@/components/TemperatureChart'
import type { TelemetryDataPoint } from '@/lib/telemetry/metrics'
import { useAnalysis } from './AnalysisContext'

const SCENARIO_LABELS: Record<LiveScenario, string> = {
  stable: 'Stable transport (demo)',
  excursion: 'Door + temperature excursion',
  stress: 'Sensor + power stress',
}

export interface LiveTransportContextType {
  isRunning: boolean
  scenario: LiveScenario
  sourceMode: LiveSourceMode
  speed: LiveSpeedMultiplier
  deviceId: string
  logFileName: string | null
  logLineCount: number
  totalReplayBatches: number
  ticks: LiveTelemetryTick[]
  alerts: LiveAlert[]
  tickIndex: number
  startedAt: number | null
  elapsedSec: number
  isFinalizingReport: boolean
  canStart: boolean
  canResumeLog: boolean
  scenarioLabels: Record<LiveScenario, string>
  temperatureData: TemperatureDataPoint[]
  fanData: TelemetryDataPoint[]
  humidityData: TelemetryDataPoint[]
  setScenario: (s: LiveScenario) => void
  setSourceMode: (s: LiveSourceMode) => void
  setSpeed: (s: LiveSpeedMultiplier) => void
  setDeviceId: (id: string) => void
  startTransport: (forceRestart?: boolean) => void
  stopTransport: () => void
  handleLogUpload: (file: File) => Promise<void>
  clearLogFile: () => void
  formatElapsed: (sec: number) => string
}

const LiveTransportContext = createContext<LiveTransportContextType | undefined>(undefined)

export function LiveTransportProvider({ children }: { children: ReactNode }) {
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
  const [totalReplayBatches, setTotalReplayBatches] = useState(0)
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

  const startTransport = useCallback(
    (forceRestart = false) => {
      stopTransport()

      const isLogResume =
        !forceRestart &&
        sourceMode === 'log_file' &&
        logIndexRef.current > 0 &&
        logIndexRef.current < logBatchesRef.current.length

      if (!isLogResume) {
        setTicks([])
        setAlerts([])
        setTickIndex(0)
        setElapsedSec(0)
        simIndexRef.current = 0
        logIndexRef.current = 0
        monitorRef.current = createMonitorState()
      } else {
        setTickIndex(logIndexRef.current)
      }

      if (sourceMode === 'log_file' && logBatchesRef.current.length === 0) {
        return
      }

      const sessionElapsedBase = isLogResume ? elapsedSec : 0
      const start = Date.now()
      sessionStartRef.current = start
      setStartedAt(start)
      setIsRunning(true)

      elapsedRef.current = setInterval(() => {
        setElapsedSec(sessionElapsedBase + Math.floor((Date.now() - start) / 1000))
      }, 1000)

      if (!isLogResume) {
        runOneTick()
      }
    },
    [elapsedSec, sourceMode, stopTransport, runOneTick]
  )

  const handleLogUpload = useCallback(async (file: File) => {
    try {
      const { lines, name } = await readLogFile(file)
      logLinesRef.current = lines
      logBatchesRef.current = parseLogLinesToReplayBatches(lines)
      setTotalReplayBatches(logBatchesRef.current.length)
      setLogFileName(name)
      setLogLineCount(lines.length)
      setSourceMode('log_file')
      setTicks([])
      setAlerts([])
      setTickIndex(0)
      logIndexRef.current = 0
      monitorRef.current = createMonitorState()
    } catch {
      setLogFileName(null)
      setLogLineCount(0)
      logBatchesRef.current = []
      logLinesRef.current = []
      setTotalReplayBatches(0)
    }
  }, [])

  const clearLogFile = useCallback(() => {
    if (isRunning) return
    logBatchesRef.current = []
    logLinesRef.current = []
    setTotalReplayBatches(0)
    setTicks([])
    setAlerts([])
    setTickIndex(0)
    logIndexRef.current = 0
    monitorRef.current = createMonitorState()
    setLogFileName(null)
    setLogLineCount(0)
    setSourceMode('simulated')
  }, [isRunning])

  const formatElapsed = useCallback((sec: number) => {
    const m = Math.floor(sec / 60)
    const s = sec % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }, [])

  const canStart = useMemo(
    () => sourceMode === 'simulated' || (sourceMode === 'log_file' && logBatchesRef.current.length > 0),
    [sourceMode]
  )

  const canResumeLog = useMemo(
    () =>
      !isRunning &&
      sourceMode === 'log_file' &&
      tickIndex > 0 &&
      totalReplayBatches > 0 &&
      tickIndex < totalReplayBatches,
    [isRunning, sourceMode, tickIndex, totalReplayBatches]
  )

  useEffect(() => {
    if (!isRunning) return
    scheduleTickLoop()
  }, [speed, isRunning, scheduleTickLoop])

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
      if (elapsedRef.current) {
        clearInterval(elapsedRef.current)
      }
    }
  }, [])

  const setSourceModeSafe = useCallback((s: LiveSourceMode) => {
    if (isRunning) return
    setSourceMode(s)
  }, [isRunning])

  const setScenarioSafe = useCallback((s: LiveScenario) => {
    if (isRunning) return
    setScenario(s)
  }, [isRunning])

  return (
    <LiveTransportContext.Provider
      value={{
        isRunning,
        scenario,
        sourceMode,
        speed,
        deviceId,
        logFileName,
        logLineCount,
        totalReplayBatches,
        ticks,
        alerts,
        tickIndex,
        startedAt,
        elapsedSec,
        isFinalizingReport,
        canStart,
        canResumeLog,
        scenarioLabels: SCENARIO_LABELS,
        temperatureData,
        fanData,
        humidityData,
        setScenario: setScenarioSafe,
        setSourceMode: setSourceModeSafe,
        setSpeed,
        setDeviceId,
        startTransport,
        stopTransport,
        handleLogUpload,
        clearLogFile,
        formatElapsed,
      }}
    >
      {children}
    </LiveTransportContext.Provider>
  )
}

export function useLiveTransport(): LiveTransportContextType {
  const context = useContext(LiveTransportContext)
  if (context === undefined) {
    throw new Error('useLiveTransport must be used within a LiveTransportProvider')
  }
  return context
}
