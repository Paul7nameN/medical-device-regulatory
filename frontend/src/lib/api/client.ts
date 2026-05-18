import type {
  ApiError,
  ValidationResult,
  AnalysisSession,
  AIAnalysisResult,
  ChatRequest,
  ChatResponse,
} from './types'

export interface AnalysisSessionListItem {
  id: string
  device_name: string | null
  status: string
  created_at: string
  completed_at: string | null
  result_summary: string | null
  violation_count: number
  latest_analysis_data?: {
    deviceId: string
    analyzedAt: string
    rawLogs: string[]
    validationResult: ValidationResult
    temperatureData?: Array<{ timestamp: string; sensorA: number; sensorB?: number; source?: string }>
  }
  ai_analysis?: AIAnalysisResult
}

export interface AnalysisSessionDetail extends AnalysisSessionListItem {
  logs: LogEntryFromDb[]
  violations: ViolationFromDb[]
  config: Record<string, unknown> | null
}

export interface LogEntryFromDb {
  id: string
  timestamp: string
  log_type: string
  raw_log_type: string | null
  source: string | null
  raw_value: string | null
  parsed_value: unknown
}

export interface ViolationFromDb {
  id: string
  reg_code: string
  severity: string
  status: string
  description: string | null
  rule_description: string | null
  category: string | null
  findings_evidence: unknown
  remediation_hint: string | null
  risk_score: number | null
  detected_at: string | null
}

export interface AnalysisListResponse {
  items: AnalysisSessionListItem[]
  total: number
  limit: number
  offset: number
}

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

export interface FetchConfig extends RequestInit {
  timeout?: number
}

export class ApiClient {
  private baseUrl: string
  private timeout: number

  constructor(baseUrl: string = API_BASE_URL, timeout: number = 120000) {
    this.baseUrl = baseUrl
    this.timeout = timeout
  }

  private async request<T>(endpoint: string, config: FetchConfig = {}): Promise<T> {
    const { timeout = this.timeout, body, headers: userHeaders, ...fetchConfig } = config

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeout)

    const isFormData = body instanceof FormData

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...fetchConfig,
        body,
        signal: controller.signal,
        headers: {
          ...(!isFormData ? { 'Content-Type': 'application/json' } : {}),
          ...userHeaders,
        },
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorData: ApiError = {
          message: response.statusText,
          status_code: response.status,
        }

        try {
          const detail = await response.json()
          errorData.detail = typeof detail === 'string' ? detail : JSON.stringify(detail)
        } catch {
          // No detail available
        }

        throw errorData
      }

      return response.json() as Promise<T>
    } catch (error) {
      clearTimeout(timeoutId)

      if (error instanceof Error && error.name === 'AbortError') {
        throw {
          message: 'Request timed out',
          status_code: 408,
        } as ApiError
      }

      if (error instanceof Error && 'status_code' in error) {
        throw error
      }

      throw {
        message: error instanceof Error ? error.message : 'Network error',
        status_code: 0,
      } as ApiError
    }
  }

  async get<T>(endpoint: string, config?: FetchConfig): Promise<T> {
    return this.request<T>(endpoint, { ...config, method: 'GET' })
  }

  async post<T>(endpoint: string, data?: unknown, config?: FetchConfig): Promise<T> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async postFormData<T>(endpoint: string, formData: FormData, config?: FetchConfig): Promise<T> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'POST',
      body: formData,
    })
  }

  async delete<T>(endpoint: string, config?: FetchConfig): Promise<T> {
    return this.request<T>(endpoint, { ...config, method: 'DELETE' })
  }
}

export const apiClient = new ApiClient()

export const validationApi = {
  validate: async (data: unknown) => {
    return apiClient.post<ValidationResult & { analysis_session_id?: string }>('/api/validate', data)
  },

  getAnalysisList: async (limit?: number, offset?: number, deviceId?: string) => {
    const params = new URLSearchParams()
    if (limit !== undefined) params.set('limit', limit.toString())
    if (offset !== undefined) params.set('offset', offset.toString())
    if (deviceId) params.set('device_id', deviceId)

    const queryString = params.toString()
    const endpoint = queryString ? `/api/analysis?${queryString}` : '/api/analysis'
    return apiClient.get<AnalysisListResponse>(endpoint)
  },

  getAnalysisDetail: async (sessionId: string) => {
    return apiClient.get<AnalysisSessionDetail>(`/api/analysis/${sessionId}`)
  },

  deleteAnalysis: async (sessionId: string) => {
    return apiClient.delete<{ success: boolean; deleted: number; session_id?: string }>(
      `/api/analysis/${sessionId}`
    )
  },

  deleteAllAnalyses: async () => {
    return apiClient.delete<{ success: boolean; deleted: number; session_id?: string }>(
      '/api/analysis/all'
    )
  },
}

export const aiApi = {
  getModels: async () => {
    return apiClient.get<{ models: string[] }>('/api/ai/models')
  },
  analyzeChart: async (formData: FormData) => {
    return apiClient.postFormData<ValidationResult>('/api/ai/analyze-chart', formData)
  },
  analyzeLogs: async (data: { logs: string }) => {
    return apiClient.post<ValidationResult>('/api/ai/analyze-logs', data)
  },
  chat: async (request: ChatRequest) => {
    return apiClient.post<ChatResponse>('/api/ai/chat', request)
  },
}

export interface GenerateReportFromLogsRequest {
  raw_logs: string[]
  device_id?: string
  filter_rules?: string[]
  include_ai_analysis?: boolean
}

export interface ReportListItem {
  id: string
  device_name: string | null
  status: string
  period_start: string | null
  period_end: string | null
  compliance_score: number | null
  generated_at: string | null
  summary: Record<string, unknown> | null
}

export interface ReportListResponse {
  items: ReportListItem[]
  total: number
  limit: number
  offset: number
}

export interface LogListItem {
  id: string
  device_name: string | null
  timestamp: string
  log_type: string
  raw_log_type: string | null
  source: string | null
  raw_value: string | null
}

export interface LogListResponse {
  items: LogListItem[]
  total: number
  limit: number
  offset: number
}

export interface DbHealthResponse {
  status: string
  stats: {
    devices: number
    analysis_sessions: number
    compliance_reports: number
  }
}

export const reportsApi = {
  generate: async (data: { device_id?: string; period_start?: string; period_end?: string }) => {
    return apiClient.post('/api/reports/generate', data)
  },

  generateFromLogs: async (data: GenerateReportFromLogsRequest) => {
    return apiClient.post<{ report: any; generated_at: string; analysis_session_id?: string }>('/api/reports/generate', data)
  },

  getSummary: async (data: GenerateReportFromLogsRequest) => {
    return apiClient.post('/api/reports/summary', data)
  },

  getList: async (limit?: number, offset?: number, deviceId?: string) => {
    const params = new URLSearchParams()
    if (limit !== undefined) params.set('limit', limit.toString())
    if (offset !== undefined) params.set('offset', offset.toString())
    if (deviceId) params.set('device_id', deviceId)

    const queryString = params.toString()
    const endpoint = queryString ? `/api/reports?${queryString}` : '/api/reports'
    return apiClient.get<ReportListResponse>(endpoint)
  },

  getDetail: async (reportId: string) => {
    return apiClient.get<ReportListItem>(`/api/reports/${reportId}`)
  },
}

export const logsApi = {
  ingest: async (formData: FormData) => {
    return apiClient.postFormData<ValidationResult & { saved_to_db?: boolean }>('/api/logs/ingest/file', formData)
  },

  getList: async (
    limit?: number,
    offset?: number,
    deviceId?: string,
    startDate?: string,
    endDate?: string
  ) => {
    const params = new URLSearchParams()
    if (limit !== undefined) params.set('limit', limit.toString())
    if (offset !== undefined) params.set('offset', offset.toString())
    if (deviceId) params.set('device_id', deviceId)
    if (startDate) params.set('start_date', startDate)
    if (endDate) params.set('end_date', endDate)

    const queryString = params.toString()
    const endpoint = queryString ? `/api/logs?${queryString}` : '/api/logs'
    return apiClient.get<LogListResponse>(endpoint)
  },
}

export const healthApi = {
  getHealth: async () => {
    return apiClient.get<{
      status: string
      app_name: string
      app_version: string
      rules_loaded: number
      debug: boolean
    }>('/api/health')
  },

  getDbHealth: async () => {
    return apiClient.get<DbHealthResponse>('/api/health/db')
  },
}
