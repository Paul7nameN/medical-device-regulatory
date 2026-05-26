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

export interface ConfidenceBreakdown {
  log?: number
  chart?: number
  alignment?: number
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
  data_source?: DataSource
  confidence?: number
  confidence_breakdown?: ConfidenceBreakdown
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

export const SEVERITY_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
}

export function compareSeverity(a: string, b: string): number {
  const orderA = SEVERITY_ORDER[a] ?? 999
  const orderB = SEVERITY_ORDER[b] ?? 999
  return orderA - orderB
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

export interface AIErrorResponse {
  error_type: string
  message: string
  retry_available: boolean
  retry_after_seconds?: number
}

export interface AIResponse<TResult> {
  success: boolean
  result?: TResult
  error?: AIErrorResponse
}

export type RuleType =
  | 'threshold_range'
  | 'duration_limit'
  | 'frequency_limit'
  | 'presence_check'
  | 'inspection_only'

export const RULE_TYPES: Record<RuleType, string> = {
  threshold_range: 'Threshold Range',
  duration_limit: 'Duration Limit',
  frequency_limit: 'Frequency Limit',
  presence_check: 'Presence Check',
  inspection_only: 'Inspection Only',
}

export interface RuleThresholds {
  field?: string
  min?: number
  max?: number
  unit?: string
  max_duration_seconds?: number
  time_window_seconds?: number
  max_count?: number
  required_state?: string
}

export interface RulesetMeta {
  source: string
  filename?: string
  extracted_at?: string
  model_used?: string
  rule_count: number
  average_confidence?: number
  ruleset_name: string
}

export interface ExtractedRule {
  id: string
  name: string
  category: string
  description: string
  type: RuleType
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  confidence: number
  thresholds?: RuleThresholds
  data_source: DataSource
  inspection_hint?: string
  extraction_notes?: string
}

export interface ExtractRulesRequest {
  document_text: string
  filename?: string
}

export interface ExtractRulesMeta {
  extracted_at: string
  model_used: string
  average_confidence: number
  rule_count: number
}

export interface ExtractRulesResponse {
  success: boolean
  rules: ExtractedRule[]
  meta?: ExtractRulesMeta
  error?: string
}

export const CONFIDENCE_THRESHOLD_AUTO_EXECUTE = 0.7

export function isRuleAutoExecutable(rule: ExtractedRule): boolean {
  return rule.confidence >= CONFIDENCE_THRESHOLD_AUTO_EXECUTE && rule.type !== 'inspection_only'
}

export type RuleCategory = 'TEMP' | 'SENS' | 'ALARM' | 'DATA' | 'POWER' | 'COOL' | 'INS' | 'OPS'

export const CATEGORY_NAMES: Record<string, string> = {
  TEMP: 'Thermal Safety',
  SENS: 'Sensor Redundancy & Accuracy',
  ALARM: 'Alarm System',
  DATA: 'Data Integrity & Logging',
  POWER: 'Power System',
  COOL: 'Cooling System',
  INS: 'Structural & Insulation',
  OPS: 'Operational Behavior',
}

export type ValidationType = 'operational' | 'inspection'

export const VALIDATION_TYPE_NAMES: Record<ValidationType, string> = {
  operational: 'Operational',
  inspection: 'Inspection',
}

function formatThreshold(thresholds?: RuleThresholds, ruleType?: RuleType): string {
  if (!thresholds) return 'See description'

  const parts: string[] = []

  if (thresholds.min !== undefined && thresholds.max !== undefined) {
    const unit = thresholds.unit || ''
    parts.push(`${thresholds.min}${unit} ≤ value ≤ ${thresholds.max}${unit}`)
  } else if (thresholds.min !== undefined) {
    const unit = thresholds.unit || ''
    parts.push(`value ≥ ${thresholds.min}${unit}`)
  } else if (thresholds.max !== undefined) {
    const unit = thresholds.unit || ''
    parts.push(`value ≤ ${thresholds.max}${unit}`)
  }

  if (thresholds.max_duration_seconds !== undefined) {
    const sec = thresholds.max_duration_seconds
    if (sec >= 3600) parts.push(`≤ ${Math.floor(sec / 3600)}h duration`)
    else if (sec >= 60) parts.push(`≤ ${Math.floor(sec / 60)}min duration`)
    else parts.push(`≤ ${sec}s duration`)
  }

  if (thresholds.max_count !== undefined && thresholds.time_window_seconds !== undefined) {
    const count = thresholds.max_count
    const window = thresholds.time_window_seconds
    if (window >= 3600) parts.push(`≤ ${count} events per ${Math.floor(window / 3600)}h`)
    else if (window >= 60) parts.push(`≤ ${count} events per ${Math.floor(window / 60)}min`)
    else parts.push(`≤ ${count} events per ${window}s`)
  }

  if (thresholds.required_state) {
    parts.push(`state = "${thresholds.required_state}"`)
  }

  if (parts.length === 0 && ruleType === 'inspection_only') {
    return 'Inspection required - see description'
  }

  return parts.length > 0 ? parts.join(' | ') : 'See description'
}

function normalizeCategory(category: string): RuleCategory {
  const upper = category.toUpperCase().trim()
  if (['TEMP', 'TEMPERATURE', 'THERMAL'].includes(upper)) return 'TEMP'
  if (['SENS', 'SENSOR', 'SENSORS'].includes(upper)) return 'SENS'
  if (['ALARM', 'ALERTS'].includes(upper)) return 'ALARM'
  if (['DATA', 'LOGGING'].includes(upper)) return 'DATA'
  if (['POWER'].includes(upper)) return 'POWER'
  if (['COOL', 'COOLING'].includes(upper)) return 'COOL'
  if (['INS', 'INSPECTION', 'STRUCTURAL'].includes(upper)) return 'INS'
  if (['OPS', 'OPERATIONAL', 'BEHAVIOR'].includes(upper)) return 'OPS'
  return 'TEMP'
}

function ruleTypeToValidationType(type: RuleType): ValidationType {
  if (type === 'inspection_only') return 'inspection'
  return 'operational'
}

export interface DisplayRule {
  id: string
  category: RuleCategory
  categoryName: string
  title: string
  description: string
  threshold: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  validationType: ValidationType
  source: DataSource
  confidence: number
  inspectionHint?: string
  isCustomRule?: boolean
  extractionNotes?: string
}

export function extractedRuleToDisplayRule(rule: ExtractedRule): DisplayRule {
  const category = normalizeCategory(rule.category)
  return {
    id: rule.id,
    category,
    categoryName: CATEGORY_NAMES[category] || rule.category,
    title: rule.name,
    description: rule.description,
    threshold: formatThreshold(rule.thresholds, rule.type),
    severity: rule.severity,
    validationType: ruleTypeToValidationType(rule.type),
    source: rule.data_source,
    confidence: rule.confidence,
    inspectionHint: rule.inspection_hint,
    isCustomRule: true,
    extractionNotes: rule.extraction_notes,
  }
}

export type SourceFileType = 'log_file' | 'chart_image' | 'constraints_doc'
export type AlignmentMethod = 'pattern_matched' | 'llm_extracted' | 'manual'
export type ConfidenceLevel = 'high' | 'medium' | 'low'
export type ConflictType = 'log_ok_chart_violation' | 'log_violation_chart_ok' | 'value_discrepancy'
export type CorrelationInsightType =
  | 'door_temperature_correlation'
  | 'recovery_pattern'
  | 'anomaly_cluster'
  | 'trend_indicator'

export const SOURCE_FILE_TYPE_LABELS: Record<SourceFileType, string> = {
  log_file: 'Log File',
  chart_image: 'Chart Image',
  constraints_doc: 'Constraints Document',
}

export interface ChartAlignment {
  method: AlignmentMethod
  confidence: number
  start_time?: string
  end_time?: string
  uncertain: boolean
}

export interface SourceFile {
  id: string
  name: string
  type: SourceFileType
  entry_count: number
  time_range_start?: string
  time_range_end?: string
  alignment?: ChartAlignment
}

export interface CorrelatedFinding {
  finding_id: string
  rule_id: string
  timestamp: string
  sources: string[]
  log_confidence?: number
  chart_confidence?: number
  alignment_confidence?: number
  combined_confidence: number
  confidence_level: ConfidenceLevel
  description: string
  evidence: Record<string, unknown>
}

export interface ConflictingFinding {
  finding_id: string
  rule_id: string
  timestamp: string
  conflict_type: ConflictType
  log_value?: string
  log_status?: string
  chart_value?: string
  chart_status?: string
  description: string
  for_human_review: boolean
}

export interface CorrelationSummary {
  total_correlated: number
  total_conflicting: number
  avg_correlation_confidence?: number
  high_confidence_count: number
  medium_confidence_count: number
  low_confidence_count: number
}

export interface CorrelationInsight {
  type: CorrelationInsightType
  title: string
  description: string
  start_time?: string
  end_time?: string
  supporting_evidence: string[]
  confidence: number
}

export interface MultiModalAnalysisResult {
  sources: SourceFile[]
  correlated_findings: CorrelatedFinding[]
  conflicting_findings: ConflictingFinding[]
  correlation_summary: CorrelationSummary
  correlation_insights: CorrelationInsight[]
  overall_alignment_confidence?: number
  alignment_uncertain: boolean
}

export interface AggregatedComplianceReport {
  device_id: string
  generated_at: string
  time_range_start?: string
  time_range_end?: string
  total_entries: number
  total_rules_evaluated: number
  summary: Record<string, number>
  violations_by_rule: Record<string, ViolationSummary>
  violations_by_severity: Record<string, Finding[]>
  temporal_analysis: TemporalAnalysis
  ai_enhancements?: AIEnhancements
  recommendations: Recommendation[]
  executive_summary: string
  raw_regulatory_report?: Record<string, unknown>
  data_sources: SourceFile[]
  multi_modal_confidence?: number
  correlation_insights: CorrelationInsight[]
  conflicting_findings: ConflictingFinding[]
  correlation_summary?: CorrelationSummary
  alignment_uncertain: boolean
}

export interface ViolationSummary {
  rule_id: string
  rule_description: string
  category: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  count: number
  first_occurrence?: string
  last_occurrence?: string
  sample_findings: Finding[]
}

export interface TimelineEvent {
  timestamp: string
  event_type: string
  rule_id?: string
  severity?: 'critical' | 'high' | 'medium' | 'low' | 'info'
  description: string
  details: Record<string, unknown>
}

export interface TemporalAnalysis {
  event_timeline: TimelineEvent[]
  critical_periods: CriticalPeriod[]
  recovery_intervals: RecoveryInterval[]
  gaps_detected: GapAnalysis[]
  time_range_start?: string
  time_range_end?: string
}

export interface CriticalPeriod {
  period_start: string
  period_end: string
  duration_seconds: number
  violations_count: number
  critical_count: number
  high_count: number
  triggering_rule?: string
  description: string
}

export interface RecoveryInterval {
  disturbance_start: string
  recovery_complete: string
  recovery_duration_seconds: number
  successful: boolean
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  rule_id?: string
}

export interface GapAnalysis {
  gap_start: string
  gap_end: string
  gap_duration_seconds: number
  gap_type: string
  preceding_event?: string
  following_event?: string
}

export interface AIEnhancements {
  chart_violations: Record<string, unknown>[]
  log_insights: Record<string, unknown>
  cross_validation_confidence?: number
  generated_report_summary?: string
}

export interface Recommendation {
  priority: 'critical' | 'high' | 'medium' | 'low' | 'info'
  rule_id: string
  rule_description: string
  title: string
  description: string
  remediation_hint?: string
  temporal_context?: string
  evidence_count: number
  first_occurrence?: string
}

export interface MultiModalAnalyzeRequest {
  log_files?: File[]
  chart_images?: File[]
  constraints_docs?: File[]
  options?: {
    merge_logs?: boolean
    extract_rules?: boolean
    align_charts?: boolean
    correlate_findings?: boolean
  }
}

export interface MultiModalAnalyzeResponse {
  success: boolean
  session_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  message?: string
  estimated_time_seconds?: number
}

export interface MultiModalStatusResponse {
  success: boolean
  session_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress?: number
  current_step?: string
  steps_total?: number
  message?: string
}

export interface MultiModalResultsResponse {
  success: boolean
  session_id: string
  report?: AggregatedComplianceReport
  multi_modal_result?: MultiModalAnalysisResult
  error?: string
}
