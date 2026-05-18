import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  type ReactNode,
} from 'react'
import type { ValidationResult, AIAnalysisResult } from '@/lib/api'
import { validationApi, type AnalysisSessionListItem } from '@/lib/api'
import type { TemperatureDataPoint } from '@/components/TemperatureChart'
import {
  createEmptySeverityCounts,
  type SeverityCounts,
  extractTemperatureFromRawLogs,
} from '@/lib/utils/transformers'

const HISTORY_STORAGE_KEY = 'med-therm-analysis-history'
const ACTIVE_INDEX_STORAGE_KEY = 'med-therm-active-index'

export interface LatestAnalysis {
  validationResult: ValidationResult
  rawLogs: string[]
  temperatureData: TemperatureDataPoint[]
  analyzedAt: string
  deviceId: string
  isPartial?: boolean
  analysisSessionId?: string
  aiAnalysis?: AIAnalysisResult
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
  // VARIANTA 2: "Intotdeauna curat" la pornirea aplicatiei
  // Nu restauram indexul din localStorage intre sesiuni
  // Utilizatorul intra intotdeauna cu upload zone vizibil, gata pentru analiza noua
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
      // Nu salvam valoarea -1 ("Clear" trebuie sa nu persiste intre sesiuni)
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
}

function backendItemToLatestAnalysis(
  item: AnalysisSessionListItem
): LatestAnalysis | null {
  const itemRecord = item as Record<string, unknown>
  const sessionId = (itemRecord.id as string) || undefined
  const data = itemRecord.latest_analysis_data as
    | BackendLatestAnalysisData
    | undefined
  const aiAnalysis = itemRecord.ai_analysis as AIAnalysisResult | undefined

  console.log('🔍 backendItemToLatestAnalysis: item=', item)
  console.log('🔍 ai_analysis found:', aiAnalysis ? 'YES' : 'NO')
  if (aiAnalysis) {
    console.log('🔍 ai_analysis details:', {
      hasRiskOverview: !!aiAnalysis.session_risk_overview,
      insightsCount: aiAnalysis.insights?.length || 0,
      predictionsCount: aiAnalysis.predictions?.length || 0,
      hasActionPlan: !!aiAnalysis.action_plan,
      hasSummary: !!aiAnalysis.natural_language_summary,
    })
  }

  if (data) {
    console.log('✅ Converting analysis from backend (full):', data)
    
    let tempData: TemperatureDataPoint[]
    if (data.temperatureData && data.temperatureData.length > 0) {
      tempData = data.temperatureData
      console.log('📊 Using temperatureData from backend (chart image):', tempData.length, 'points')
    } else {
      tempData = extractTemperatureFromRawLogs(data.rawLogs || [])
    }
    
    return {
      deviceId: data.deviceId,
      analyzedAt: data.analyzedAt,
      rawLogs: data.rawLogs || [],
      validationResult: data.validationResult,
      temperatureData: tempData,
      analysisSessionId: sessionId,
      aiAnalysis: aiAnalysis,
    }
  }

  console.log('⚠️ backendItemToLatestAnalysis: missing latest_analysis_data, creating partial analysis, item=', item)
  
  const deviceId = (itemRecord.device_name as string) || 'unknown-device'
  const analyzedAt = (itemRecord.created_at as string) || new Date().toISOString()
  const violationCount = (itemRecord.violation_count as number) || 0

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

  return {
    deviceId,
    analyzedAt,
    rawLogs: [],
    validationResult: partialValidationResult,
    temperatureData: [],
    isPartial: true,
    analysisSessionId: sessionId,
    aiAnalysis: aiAnalysis,
  }
}

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined)

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [analysisHistory, setAnalysisHistory] = useState<LatestAnalysis[]>(loadHistoryFromStorage)
  const [activeAnalysisIndex, setActiveAnalysisIndex] = useState<number>(loadActiveIndexFromStorage)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [retryAction, setRetryAction] = useState<(() => void) | null>(null)

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
       
       // NOTA: Nu mai facem auto-select aici (varianta 2: "intotdeauna curat" la pornire)
       // Daca vrem sa selectam dupa un nou upload, o vom face explicit in FileUploadZone
     } catch (e) {
      console.warn('⚠️ Failed to load from DB, trying localStorage fallback:', e)

       const localHistory = loadHistoryFromStorage()
       if (localHistory.length > 0) {
         console.log('📦 Using localStorage fallback:', localHistory.length, 'items')
         setAnalysisHistory(localHistory)
         setError('Mod offline. Datele sunt din cache.')
         
         // NOTA: Nu mai facem auto-select nici aici
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

  const clampedIndex = useMemo(() => {
    // -1 înseamnă "nicio analiză activă" - valoare specială setată de butonul "Clear"
    if (activeAnalysisIndex === -1) return -1
    
    // Dacă nu există analize, întoarce -1
    if (analysisHistory.length === 0) return -1
    
    // Altfel, clamp la un index valid în istoric
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
    // Salveaza indexul (dar nu salveaza -1, vezi functia saveActiveIndexToStorage)
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
    // Setăm activeAnalysisIndex la -1 pentru a indica "nicio analiză activă"
    // NU mai ștergem analysisHistory - rămâne încărcat din baza de date
    // Dacă utilizatorul vrea să șteargă toate analizele, poate folosi "Clear All" din tabul History
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
