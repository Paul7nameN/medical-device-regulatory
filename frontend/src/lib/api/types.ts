export interface LogEntry {
  id: string
  device_id: string
  timestamp: string
  log_type: 'telemetry' | 'event' | 'alert' | 'status'
  source?: string
  payload?: Record<string, unknown>
  created_at: string
}

export interface Device {
  id: string
  name: string
  model?: string
  serial_number?: string
  status: 'online' | 'offline' | 'maintenance' | 'registered'
  last_seen_at?: string
  created_at: string
  updated_at: string
}

export interface AnalysisSession {
  id: string
  device_id?: string
  status: 'pending' | 'completed' | 'failed'
  config?: Record<string, unknown>
  result_summary?: string
  result_path?: string
  started_at: string
  completed_at?: string
  created_at: string
}

export interface DetectedViolation {
  id: string
  device_id?: string
  analysis_session_id?: string
  log_entry_id?: string
  reg_code: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  status: 'open' | 'acknowledged' | 'resolved'
  description?: string
  evidence?: Evidence[]
  risk_score?: number
  detected_at: string
  resolved_at?: string
  created_at: string
}

export interface Evidence {
  entry_index: number
  timestamp: string
  log_type: string
  raw_value: string
  explanation: string
}

export interface ComplianceReport {
  id: string
  device_id?: string
  status: 'generating' | 'completed' | 'failed'
  period_start: string
  period_end: string
  compliance_score?: number
  summary?: {
    by_category: Record<string, CategorySummary>
    by_severity: Record<string, number>
    total_rules: number
    passed_rules: number
    failed_rules: number
  }
  report_path?: string
  generated_by?: string
  generated_at: string
  created_at: string
}

export interface CategorySummary {
  passed: number
  failed: number
  total: number
}

export interface ValidationResult {
  device_id: string
  analyzed_at: string
  total_entries: number
  time_range_start?: string
  time_range_end?: string
  summary: Record<string, CategorySummary>
  findings: Finding[]
  passed_count: number
  failed_count: number
  critical_count: number
}

export type DataSource = 'logs' | 'inspection' | 'combined' | 'images'

export interface Finding {
  rule_id: string
  rule_description: string
  category: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  passed: boolean
  message: string
  evidence: Evidence[]
  timestamp: string
  remediation_hint?: string
  needs_visual_verification: boolean
  data_source?: DataSource
  confidence?: number
  inspection_hint?: string
}

export interface ApiError {
  message: string
  status_code: number
  detail?: string
}

export interface UploadFileItem {
  id: string
  file: File
  name: string
  size: number
  type: string
  progress: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
  session_id?: string
}

export type RegCategory = 'TEMP' | 'SENS' | 'ALARM' | 'DATA' | 'POWER' | 'COOL' | 'INS' | 'OPS'

export const REG_CATEGORIES: Record<RegCategory, string> = {
  TEMP: 'Thermal Safety',
  SENS: 'Sensor Redundancy',
  ALARM: 'Alarm System',
  DATA: 'Data Integrity',
  POWER: 'Power System',
  COOL: 'Cooling System',
  INS: 'Structural Insulation',
  OPS: 'Operational Behavior',
}

export const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-red-100 text-red-700 border-red-200 dark:bg-red-950/50 dark:text-red-400 dark:border-red-900',
  high: 'bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-950/50 dark:text-orange-400 dark:border-orange-900',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-950/50 dark:text-yellow-400 dark:border-yellow-900',
  low: 'bg-green-100 text-green-700 border-green-200 dark:bg-green-950/50 dark:text-green-400 dark:border-green-900',
  info: 'bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-950/50 dark:text-blue-400 dark:border-blue-900',
}

export const SEVERITY_BG: Record<string, string> = {
  critical: 'bg-severity-critical',
  high: 'bg-severity-high',
  medium: 'bg-severity-medium',
  low: 'bg-severity-low',
  info: 'bg-severity-info',
}

export const DATA_SOURCE_LABELS: Record<DataSource, string> = {
  logs: 'Logs',
  inspection: 'Inspection',
  combined: 'Combined',
  images: 'Images',
}

export const DATA_SOURCE_COLORS: Record<DataSource, { badge: string; text: string }> = {
  logs: {
    badge: 'bg-green-100 text-green-700 border-green-200 dark:bg-green-950/40 dark:text-green-400 dark:border-green-900',
    text: 'text-green-600 dark:text-green-400',
  },
  inspection: {
    badge: 'bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-800/60 dark:text-gray-300 dark:border-gray-700',
    text: 'text-gray-600 dark:text-gray-400',
  },
  combined: {
    badge: 'bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-950/40 dark:text-orange-400 dark:border-orange-900',
    text: 'text-orange-600 dark:text-orange-400',
  },
  images: {
    badge: 'bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-400 dark:border-blue-900',
    text: 'text-blue-600 dark:text-blue-400',
  },
}

export const DATA_SOURCE_DESCRIPTIONS: Record<DataSource, string> = {
  logs: 'Fully validated from system log data',
  inspection: 'Requires physical inspection - not validated from logs',
  combined: 'Partially validated from logs, may require inspection',
  images: 'Validated from image/VLM analysis',
}

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'
export type TrendIndicator = 'stable' | 'improving' | 'deteriorating'
export type InsightCategory = 'sensor' | 'power' | 'cooling' | 'operational' | 'environmental' | 'thermal' | 'data' | 'alarm'

export interface InsightRiskFactor {
  factor: string
  severity: string
}

export interface RiskOverview {
  overall_risk_score: number
  risk_level: RiskLevel
  primary_risk_category: string
  imminent_concerns_count: number
  trend_indicator: TrendIndicator
}

export interface Insight {
  id: string
  priority: RiskLevel
  category: InsightCategory
  title: string
  evidence: string[]
  why_matters: string
  risk_score_contribution: number
  risk_factors: InsightRiskFactor[]
}

export interface Prediction {
  id: string
  scenario: string
  confidence: number
  timeframe: string
  estimated_probability: string
  risk_factors_driving_this: string[]
  mitigation_potential?: string
  why_concerning?: string
}

export interface ActionItem {
  action: string
  priority: RiskLevel
  steps?: string[]
  why_needed?: string
  rationale?: string
}

export interface ActionPlan {
  summary: string
  immediate_actions_0_1h: ActionItem[]
  short_term_24h: ActionItem[]
  long_term_maintenance: ActionItem[]
}

export interface AIAnalysisResult {
  session_risk_overview: RiskOverview
  insights: Insight[]
  predictions: Prediction[]
  action_plan: ActionPlan
  natural_language_summary: string
  generated_at?: string
  model_used?: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatRequest {
  analysis_session_id?: string
  message: string
  chat_history: ChatMessage[]
}

export interface ChatResponse {
  message: string
  sources: Record<string, unknown>[]
  suggested_actions: string[]
}
