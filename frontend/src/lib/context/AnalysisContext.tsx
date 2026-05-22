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
import type {
  ValidationResult,
  AIAnalysisResult,
  ExtractedRule,
  RulesetMeta,
  MultiModalStatusResponse,
  MultiModalResultsResponse,
} from '@/lib/api'
import {
  validationApi,
  multimodalApi,
  type AnalysisSessionListItem,
} from '@/lib/api'
import type { TemperatureDataPoint } from '@/components/TemperatureChart'
import {
  createEmptySeverityCounts,
  type SeverityCounts,
  extractTemperatureFromRawLogs,
  normalizeFindings,
} from '@/lib/utils/transformers'
import { buildTelemetrySeries } from '@/lib/telemetry/extract'
import type { TelemetryDataPoint, TelemetryMetricId } from '@/lib/telemetry/metrics'

const HISTORY_STORAGE_KEY = 'med-therm-analysis-history'
const ACTIVE_INDEX_STORAGE_KEY = 'med-therm-active-index'

export interface LatestAnalysis {
  validationResult: ValidationResult
  rawLogs: string[]
  temperatureData: TemperatureDataPoint[]
  telemetrySeries: Partial<Record<TelemetryMetricId, TelemetryDataPoint[]>>
  analyzedAt: string
  deviceId: string
  isPartial?: boolean
  analysisSessionId?: string
  aiAnalysis?: AIAnalysisResult
  hasCustomRules?: boolean
  rulesetName?: string
  extractedRules?: ExtractedRule[]
  rulesetMeta?: RulesetMeta
}

function normalizeBackendTemperature(
  points: Array<TemperatureDataPoint & { value?: number }>
): TemperatureDataPoint[] {
  return points.map((point) => ({
    timestamp: point.timestamp,
    time: point.time ?? '',
    sensorA: point.sensorA ?? point.value ?? 0,
    sensorB: point.sensorB,
    source: point.source,
  }))
}

function enrichAnalysis(
  base: Omit<LatestAnalysis, 'telemetrySeries' | 'temperatureData'> & {
    temperatureData?: Array<TemperatureDataPoint & { value?: number }>
    telemetrySeries?: Partial<Record<TelemetryMetricId, TelemetryDataPoint[]>>
  }
): LatestAnalysis {
  const rawLogs = base.rawLogs || []
  const tempFromBackend =
    base.temperatureData && base.temperatureData.length > 0
      ? normalizeBackendTemperature(base.temperatureData)
      : undefined
  const telemetrySeries =
    base.telemetrySeries && Object.keys(base.telemetrySeries).length > 0
      ? (base.telemetrySeries as Record<TelemetryMetricId, TelemetryDataPoint[]>)
      : buildTelemetrySeries(rawLogs, tempFromBackend)

  const temperatureData =
    tempFromBackend && tempFromBackend.length > 0
      ? tempFromBackend
      : (telemetrySeries.temperature || []).map((point) => ({
          timestamp: point.timestamp,
          time: point.time,
          sensorA: point.value,
          sensorB: point.sensorB,
          source: point.source,
        }))

  return {
    ...base,
    temperatureData,
    telemetrySeries,
  }
}

export interface AnalysisContextType {
  latestAnalysis: LatestAnalysis | null
  setLatestAnalysis: (analysis: LatestAnalysis) => void
  clearAnalysis: () => void
  isAnalyzing: boolean
  setIsAnalyzing: (value: boolean) => void
  isLoadingHistory: boolean
  severityCountsByCategory: Record<string, SeverityCounts>
  hasData: boolean
  error: string | null
  setError: (error: string | null) => void
  clearError: () => void
  retryAction: (() => void) | null
  setRetryAction: (action: (() => void) | null) => void
  analysisHistory: LatestAnalysis[]
  activeAnalysisIndex: number
  addAnalysis: (analysis: LatestAnalysis) => void
  switchAnalysis: (index: number) => void
  removeAnalysis: (index: number) => Promise<void>
  clearHistory: () => Promise<void>
  refreshHistory: () => Promise<void>
  batchSessionId: string | null
  batchStatus: MultiModalStatusResponse | null
  startBatchAnalysis: (sessionId: string) => void
  stopBatchAnalysis: () => void
}

function isValidAnalysis(data: unknown): data is LatestAnalysis {
  if (!data || typeof data !== 'object') return false
  const obj = data as Record<string, unknown>
  if (!('validationResult' in obj)) return false
  const vr = obj.validationResult
  if (!vr || typeof vr !== 'object') return false
  const vrObj = vr as Record<string, unknown>
  if ('findings' in vrObj && !Array.isArray(vrObj.findings)) return false
  return true
}

function isValidHistoryArray(data: unknown): data is LatestAnalysis[] {
  if (!Array.isArray(data)) return false
  return data.every((item) => isValidAnalysis(item))
}

function loadHistoryFromStorage(): LatestAnalysis[] {
  try {
    const stored = localStorage.getItem(HISTORY_STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored) as unknown
      if (isValidHistoryArray(parsed)) {
        return parsed
      }
      localStorage.removeItem(HISTORY_STORAGE_KEY)
    }
  } catch {
    try {
      localStorage.removeItem(HISTORY_STORAGE_KEY)
    } catch {
      // Ignore
    }
  }
  return []
}

function loadActiveIndexFromStorage(): number {
  return -1
}

function saveHistoryToStorage(history: LatestAnalysis[]): void {
  try {
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history))
  } catch {
    // Ignore storage errors
  }
}

function saveActiveIndexToStorage(index: number): void {
  try {
    if (index === -1) {
      localStorage.removeItem(ACTIVE_INDEX_STORAGE_KEY)
    } else {
      localStorage.setItem(ACTIVE_INDEX_STORAGE_KEY, index.toString())
    }
  } catch {
    // Ignore
  }
}

function buildSeverityCounts(
  analysis: LatestAnalysis | null
): Record<string, SeverityCounts> {
  const result: Record<string, SeverityCounts> = {
    TEMP: createEmptySeverityCounts(),
    SENS: createEmptySeverityCounts(),
    ALARM: createEmptySeverityCounts(),
    DATA: createEmptySeverityCounts(),
    POWER: createEmptySeverityCounts(),
    COOL: createEmptySeverityCounts(),
    INS: createEmptySeverityCounts(),
    OPS: createEmptySeverityCounts(),
  }

  if (!analysis?.validationResult?.findings) {
    return result
  }

  const findings = analysis.validationResult.findings
  if (!Array.isArray(findings)) {
    return result
  }

  for (const finding of findings) {
    if (finding.passed) continue

    const category = finding.category
    if (!result[category]) {
      result[category] = createEmptySeverityCounts()
    }

    const severity = finding.severity as keyof SeverityCounts
    if (severity in result[category]) {
      result[category][severity]++
    }
  }

  return result
}

interface BackendLatestAnalysisData {
  deviceId: string
  analyzedAt: string
  rawLogs: string[]
  validationResult: ValidationResult
  temperatureData?: TemperatureDataPoint[]
  telemetrySeries?: Partial<Record<TelemetryMetricId, TelemetryDataPoint[]>>
}

function backendItemToLatestAnalysis(
  item: AnalysisSessionListItem
): LatestAnalysis | null {
  const sessionId = item.id
  const data = item.latest_analysis_data as BackendLatestAnalysisData | undefined
  const aiAnalysis = item.ai_analysis
  
  const hasCustomRules = item.has_custom_rules
  const rulesetName = item.ruleset_name
  const extractedRulesRaw = item.extracted_rules
  const rulesetMetaRaw = item.ruleset_meta

  const extractedRules = extractedRulesRaw ? (extractedRulesRaw as unknown as ExtractedRule[]) : undefined
  const rulesetMeta = rulesetMetaRaw ? (rulesetMetaRaw as unknown as RulesetMeta) : undefined

  console.log('🔍 backendItemToLatestAnalysis: item=', item)
  console.log('🔍 ai_analysis found:', aiAnalysis ? 'YES' : 'NO')
  console.log('🔍 hasCustomRules:', hasCustomRules, 'rulesetName:', rulesetName)
  console.log('🔍 extractedRules count:', extractedRules?.length || 0)

  if (data) {
    console.log('✅ Converting analysis from backend (full):', data)
    
    let tempData: TemperatureDataPoint[]
    if (data.temperatureData && data.temperatureData.length > 0) {
      tempData = data.temperatureData
      console.log('📊 Using temperatureData from backend (chart image):', tempData.length, 'points')
    } else {
      tempData = extractTemperatureFromRawLogs(data.rawLogs || [])
    }

    return enrichAnalysis({
      deviceId: data.deviceId,
      analyzedAt: data.analyzedAt,
      rawLogs: data.rawLogs || [],
      validationResult: {
        ...data.validationResult,
        findings: normalizeFindings(data.validationResult.findings || []),
      },
      temperatureData: tempData,
      telemetrySeries: data.telemetrySeries,
      analysisSessionId: sessionId,
      aiAnalysis: aiAnalysis,
      hasCustomRules,
      rulesetName,
      extractedRules,
      rulesetMeta,
    })
  }

  console.log('⚠️ backendItemToLatestAnalysis: missing latest_analysis_data, creating partial analysis, item=', item)
  
  const deviceId = item.device_name || 'unknown-device'
  const analyzedAt = item.created_at || new Date().toISOString()
  const violationCount = item.violation_count || 0

  const partialValidationResult: ValidationResult = {
    device_id: deviceId,
    analyzed_at: analyzedAt,
    total_entries: 0,
    summary: {},
    findings: [],
    passed_count: 0,
    failed_count: violationCount,
    critical_count: 0,
  }

  return enrichAnalysis({
    deviceId,
    analyzedAt,
    rawLogs: [],
    validationResult: partialValidationResult,
    temperatureData: [],
    isPartial: true,
    analysisSessionId: sessionId,
    aiAnalysis: aiAnalysis,
    hasCustomRules,
    rulesetName,
    extractedRules,
    rulesetMeta,
  })
}

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined)

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [analysisHistory, setAnalysisHistory] = useState<LatestAnalysis[]>(loadHistoryFromStorage)
  const [activeAnalysisIndex, setActiveAnalysisIndex] = useState<number>(loadActiveIndexFromStorage)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [retryAction, setRetryAction] = useState<(() => void) | null>(null)

  const [batchSessionId, setBatchSessionId] = useState<string | null>(null)
  const [batchStatus, setBatchStatus] = useState<MultiModalStatusResponse | null>(null)
  const batchPollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const batchSessionIdRef = useRef<string | null>(null)

  const refreshHistory = useCallback(async () => {
    console.log('🔄 refreshHistory: loading from database (single source of truth)...')
    setIsLoadingHistory(true)
    setRetryAction(null)

    try {
      const response = await validationApi.getAnalysisList(100, 0)
      console.log('📥 GET /api/analysis response:', response)

      const loadedFromBackend: LatestAnalysis[] = []
      for (const item of response.items) {
        const converted = backendItemToLatestAnalysis(item)
        if (converted) {
          loadedFromBackend.push(converted)
        }
      }

      const sortedHistory = loadedFromBackend.sort(
        (a, b) => new Date(b.analyzedAt).getTime() - new Date(a.analyzedAt).getTime()
      )

      console.log('✅ Loaded from DB:', sortedHistory.length, 'items')

      setAnalysisHistory(sortedHistory)
      saveHistoryToStorage(sortedHistory)
      setError(null)
      
    } catch (e) {
      console.warn('⚠️ Failed to load from DB, trying localStorage fallback:', e)

      const localHistory = loadHistoryFromStorage().map((item) => enrichAnalysis(item))
      if (localHistory.length > 0) {
        console.log('📦 Using localStorage fallback:', localHistory.length, 'items')
        setAnalysisHistory(localHistory)
        setError('Mod offline. Datele sunt din cache.')
        
      } else {
        console.log('❌ No data available (DB failed + localStorage empty)')
        setAnalysisHistory([])
        setError('Nu se poate conecta la server. Verifică conexiunea.')
      }

      setRetryAction(() => refreshHistory)
    } finally {
      setIsLoadingHistory(false)
    }
  }, [])

  const stopBatchAnalysis = useCallback(() => {
    console.log('🛑 [batch] Stopping batch analysis polling')
    if (batchPollingRef.current) {
      clearInterval(batchPollingRef.current)
      batchPollingRef.current = null
    }
    batchSessionIdRef.current = null
    setBatchSessionId(null)
    setBatchStatus(null)
    setIsAnalyzing(false)
  }, [])

  const startBatchAnalysis = useCallback((sessionId: string) => {
    console.log('🚀 [batch] Starting batch analysis polling for session:', sessionId)

    stopBatchAnalysis()

    batchSessionIdRef.current = sessionId
    setBatchSessionId(sessionId)
    setIsAnalyzing(true)
    setError(null)

    const pollStatus = async () => {
      const currentSessionId = batchSessionIdRef.current
      if (!currentSessionId) return

      try {
        console.log('📊 [batch poll] Checking status for:', currentSessionId)
        const status = await multimodalApi.getStatus(currentSessionId)
        setBatchStatus(status)

        console.log('📊 [batch poll] Status:', status.status, 'Progress:', status.progress)

        if (status.status === 'completed' || status.status === 'failed') {
          stopBatchAnalysis()

          if (status.status === 'completed') {
            try {
              const results = await multimodalApi.getResults(currentSessionId)

              if (results.success && results.report) {
                console.log('✅ [batch poll] Analysis complete!')
                await refreshHistory()
                setActiveAnalysisIndex(0)
              } else {
                setError(results.error || 'Analysis completed but no results available')
              }
            } catch (resultError) {
              console.error('❌ [batch poll] Failed to get results:', resultError)
              const errorMessage =
                resultError instanceof Error
                  ? resultError.message
                  : 'Failed to retrieve results'
              setError(errorMessage)
            }
          } else if (status.status === 'failed') {
            setError(status.message || 'Batch analysis failed')
          }
        }
      } catch (pollError: unknown) {
        console.error('❌ [batch poll] Status check failed:', pollError)
        const errorMessage =
          pollError instanceof Error
            ? pollError.message
            : typeof pollError === 'object' && pollError !== null && 'message' in pollError
              ? String((pollError as { message: string }).message)
              : 'Status check failed'
        setError(errorMessage)
        stopBatchAnalysis()
      }
    }

    pollStatus()
    batchPollingRef.current = setInterval(pollStatus, 2000)
  }, [stopBatchAnalysis, refreshHistory])

  useEffect(() => {
    return () => {
      if (batchPollingRef.current) {
        clearInterval(batchPollingRef.current)
      }
    }
  }, [])

  const clampedIndex = useMemo(() => {
    if (activeAnalysisIndex === -1) return -1
    
    if (analysisHistory.length === 0) return -1
    
    if (activeAnalysisIndex >= analysisHistory.length) return analysisHistory.length - 1
    if (activeAnalysisIndex < 0) return 0
    return activeAnalysisIndex
  }, [analysisHistory.length, activeAnalysisIndex])

  const latestAnalysis = useMemo(() => {
    return clampedIndex >= 0 && clampedIndex < analysisHistory.length
      ? analysisHistory[clampedIndex]
      : null
  }, [analysisHistory, clampedIndex])

  const severityCountsByCategory = useMemo(() => {
    return buildSeverityCounts(latestAnalysis)
  }, [latestAnalysis])

  const hasData = analysisHistory.length > 0 && latestAnalysis !== null

  useEffect(() => {
    refreshHistory()
  }, [refreshHistory])

  useEffect(() => {
    saveActiveIndexToStorage(clampedIndex)
  }, [clampedIndex])

  const setLatestAnalysis = useCallback((analysis: LatestAnalysis) => {
    setAnalysisHistory((prev) => {
      if (prev.length === 0) {
        setActiveAnalysisIndex(0)
        return [analysis]
      }
      const newHistory = [...prev]
      newHistory[clampedIndex] = analysis
      return newHistory
    })
    setError(null)
    setRetryAction(null)
  }, [clampedIndex])

  const clearAnalysis = useCallback(() => {
    setActiveAnalysisIndex(-1)
    setError(null)
    setRetryAction(null)
  }, [])

  const addAnalysis = useCallback((analysis: LatestAnalysis) => {
    setAnalysisHistory((prev) => {
      const newIndex = prev.length
      setActiveAnalysisIndex(newIndex)
      return [...prev, analysis]
    })
    setError(null)
    setRetryAction(null)
  }, [])

  const switchAnalysis = useCallback((index: number) => {
    setActiveAnalysisIndex(index)
  }, [])

  const removeAnalysis = useCallback(async (index: number) => {
    const item = analysisHistory[index]
    if (!item) {
      return
    }

    if (item.analysisSessionId) {
      try {
        console.log('🗑️ Deleting analysis session:', item.analysisSessionId)
        await validationApi.deleteAnalysis(item.analysisSessionId)
        console.log('✅ Deleted successfully')
      } catch (e: unknown) {
        const errorMsg = e instanceof Error ? e.message : String(e)
        console.error('❌ Failed to delete analysis:', e)
        setError(`Eroare la ștergere: ${errorMsg}`)
        return
      }
    }

    await refreshHistory()
  }, [analysisHistory, refreshHistory, setError])

  const clearHistory = useCallback(async () => {
    const hasItemsWithIds = analysisHistory.some((item) => !!item.analysisSessionId)

    if (hasItemsWithIds) {
      try {
        console.log('🗑️ Deleting ALL analysis sessions...')
        await validationApi.deleteAllAnalyses()
        console.log('✅ Deleted all successfully')
      } catch (e: unknown) {
        const errorMsg = e instanceof Error ? e.message : String(e)
        console.error('❌ Failed to delete all analyses:', e)
        setError(`Eroare la ștergere: ${errorMsg}`)
        return
      }
    }

    await refreshHistory()
  }, [analysisHistory, refreshHistory, setError])

  const clearError = useCallback(() => {
    setError(null)
    setRetryAction(null)
  }, [])

  return (
    <AnalysisContext.Provider
      value={{
        latestAnalysis,
        setLatestAnalysis,
        clearAnalysis,
        isAnalyzing,
        setIsAnalyzing,
        isLoadingHistory,
        severityCountsByCategory,
        hasData,
        error,
        setError,
        clearError,
        retryAction,
        setRetryAction,
        analysisHistory,
        activeAnalysisIndex: clampedIndex,
        addAnalysis,
        switchAnalysis,
        removeAnalysis,
        clearHistory,
        refreshHistory,
        batchSessionId,
        batchStatus,
        startBatchAnalysis,
        stopBatchAnalysis,
      }}
    >
      {children}
    </AnalysisContext.Provider>
  )
}

export function useAnalysis(): AnalysisContextType {
  const context = useContext(AnalysisContext)
  if (context === undefined) {
    throw new Error('useAnalysis must be used within an AnalysisProvider')
  }
  return context
}
