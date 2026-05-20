import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, Badge, Button, SeverityBadge, ConfidenceBadge } from '@/components/ui'
import { 
  ChevronDown, ChevronUp, 
  Lightbulb, Search,
  Activity, TrendingUp, Clock, GitMerge, AlertTriangle, Eye, FileText, Image,
  Info
} from 'lucide-react'
import type { CorrelationInsight, CorrelationInsightType, ConflictingFinding, ConflictType } from '@/lib/api'
import { cn } from '@/lib/utils'

interface CorrelationInsightsProps {
  insights: CorrelationInsight[]
  className?: string
}

const CORRELATION_TYPE_INFO: Record<CorrelationInsightType, { 
  icon: React.ReactNode 
  label: string 
  color: string
}> = {
  door_temperature_correlation: {
    icon: <Search className="h-4 w-4" />,
    label: 'Door-Temp Correlation',
    color: 'text-orange-600 dark:text-orange-400',
  },
  recovery_pattern: {
    icon: <TrendingUp className="h-4 w-4" />,
    label: 'Recovery Pattern',
    color: 'text-blue-600 dark:text-blue-400',
  },
  anomaly_cluster: {
    icon: <Activity className="h-4 w-4" />,
    label: 'Anomaly Cluster',
    color: 'text-red-600 dark:text-red-400',
  },
  trend_indicator: {
    icon: <TrendingUp className="h-4 w-4" />,
    label: 'Trend Indicator',
    color: 'text-purple-600 dark:text-purple-400',
  },
}

function CorrelationInsightItem({ insight }: { insight: CorrelationInsight }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const typeInfo = CORRELATION_TYPE_INFO[insight.type] || {
    icon: <Lightbulb className="h-4 w-4" />,
    label: 'Correlation',
    color: 'text-primary',
  }

  const confidencePercent = Math.round(insight.confidence * 100)
  const isHighConfidence = confidencePercent >= 85
  const isMediumConfidence = confidencePercent >= 70

  return (
    <Card className={cn(
      'transition-all border-l-4',
      isHighConfidence ? 'border-l-green-500' : 
      isMediumConfidence ? 'border-l-yellow-500' : 'border-l-orange-500'
    )}>
      <CardHeader
        className="pb-2 cursor-pointer hover:bg-muted/40 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <Badge variant="outline" className={cn('flex items-center gap-1', typeInfo.color)}>
                {typeInfo.icon}
                <span className="capitalize text-xs">{typeInfo.label}</span>
              </Badge>
              <ConfidenceBadge confidence={insight.confidence} />
              {(insight.start_time || insight.end_time) && (
                <Badge variant="outline" className="flex items-center gap-1 text-xs">
                  <Clock className="h-3 w-3" />
                  {insight.start_time && new Date(insight.start_time).toLocaleTimeString()}
                  {insight.start_time && insight.end_time && ' → '}
                  {insight.end_time && new Date(insight.end_time).toLocaleTimeString()}
                </Badge>
              )}
            </div>
            <CardTitle className="text-sm font-medium">{insight.title}</CardTitle>
            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
              {insight.description}
            </p>
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8 flex-shrink-0">
            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </Button>
        </div>
      </CardHeader>
      {isExpanded && (
        <CardContent className="space-y-4 pt-2 border-t border-border">
          <div>
            <h4 className="text-sm font-medium text-foreground mb-1">Description</h4>
            <p className="text-sm text-muted-foreground">{insight.description}</p>
          </div>
          {insight.supporting_evidence && insight.supporting_evidence.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-foreground mb-2 flex items-center gap-1.5">
                <GitMerge className="h-4 w-4 text-primary" />
                Supporting Evidence
              </h4>
              <ul className="space-y-1.5">
                {insight.supporting_evidence.map((ev, i) => (
                  <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                    <span className="text-primary mt-0.5">•</span>
                    {ev}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-muted/40 rounded-lg p-3">
              <h4 className="text-xs font-medium text-muted-foreground mb-1">Confidence</h4>
              <div className="flex items-center gap-2">
                <ConfidenceBadge confidence={insight.confidence} />
              </div>
            </div>
            <div className="bg-muted/40 rounded-lg p-3">
              <h4 className="text-xs font-medium text-muted-foreground mb-1">Type</h4>
              <span className="text-sm font-medium">{typeInfo.label}</span>
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  )
}

export function CorrelationInsights({ insights, className }: CorrelationInsightsProps) {
  if (!insights || insights.length === 0) {
    return null
  }

  const high = insights.filter((i) => i.confidence >= 0.85)
  const medium = insights.filter((i) => i.confidence >= 0.70 && i.confidence < 0.85)
  const low = insights.filter((i) => i.confidence < 0.70)

  const sortedInsights = [...high, ...medium, ...low]

  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-base font-medium flex items-center gap-2">
          <GitMerge className="h-5 w-5 text-primary" />
          Multi-Modal Correlation Insights ({insights.length})
        </h3>
        <div className="flex items-center gap-2 text-sm">
          {high.length > 0 && <Badge variant="low">High: {high.length}</Badge>}
          {medium.length > 0 && <Badge variant="medium">Medium: {medium.length}</Badge>}
          {low.length > 0 && <Badge variant="high">Low: {low.length}</Badge>}
        </div>
      </div>
      <p className="text-xs text-muted-foreground">
        These insights were discovered by correlating data from multiple sources (logs and chart images).
      </p>
      {sortedInsights.map((insight, idx) => (
        <CorrelationInsightItem key={`${insight.type}-${idx}`} insight={insight} />
      ))}
    </div>
  )
}

interface ConflictsSectionProps {
  findings: ConflictingFinding[]
  className?: string
}

const CONFLICT_TYPE_INFO: Record<ConflictType, {
  label: string
  description: string
  icon: React.ReactNode
  severity: 'critical' | 'high' | 'medium'
}> = {
  log_ok_chart_violation: {
    label: 'Logs OK, Chart Shows Violation',
    description: 'System logs passed validation, but chart image shows a potential violation',
    icon: <FileText className="h-4 w-4" />,
    severity: 'high',
  },
  log_violation_chart_ok: {
    label: 'Logs Violation, Chart OK',
    description: 'System logs detected a violation, but chart appears normal',
    icon: <Image className="h-4 w-4" />,
    severity: 'medium',
  },
  value_discrepancy: {
    label: 'Value Discrepancy',
    description: 'Log values and chart values show different readings at the same time',
    icon: <AlertTriangle className="h-4 w-4" />,
    severity: 'high',
  },
}

function ConflictItem({ conflict }: { conflict: ConflictingFinding }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const typeInfo = CONFLICT_TYPE_INFO[conflict.conflict_type] || {
    label: 'Unknown Conflict',
    description: 'Data mismatch detected',
    icon: <AlertTriangle className="h-4 w-4" />,
    severity: 'medium' as const,
  }

  return (
    <Card className="border-l-4 border-l-amber-500 bg-amber-50/50 dark:bg-amber-950/10">
      <CardHeader
        className="pb-2 cursor-pointer hover:bg-muted/40 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <SeverityBadge severity={typeInfo.severity} />
              <Badge variant="outline" className="flex items-center gap-1 text-amber-700 dark:text-amber-400 border-amber-300 dark:border-amber-700">
                {typeInfo.icon}
                <span className="text-xs">{typeInfo.label}</span>
              </Badge>
              {conflict.for_human_review && (
                <Badge variant="outline" className="flex items-center gap-1 text-xs bg-amber-100 dark:bg-amber-900/50">
                  <Eye className="h-3 w-3" />
                  For Review
                </Badge>
              )}
            </div>
            <CardTitle className="text-sm font-medium">{conflict.description}</CardTitle>
            <p className="text-xs text-muted-foreground mt-1">
              {conflict.rule_id} • Detected {new Date(conflict.timestamp).toLocaleString()}
            </p>
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8 flex-shrink-0">
            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </Button>
        </div>
      </CardHeader>
      {isExpanded && (
        <CardContent className="space-y-4 pt-2 border-t border-amber-200 dark:border-amber-900">
          <div className="bg-amber-100/50 dark:bg-amber-900/30 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <Info className="h-4 w-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                  {typeInfo.description}
                </p>
                <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                  Logs are considered ground truth. Chart discrepancies require human verification.
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-muted/40 rounded-lg p-3 border border-border">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="h-4 w-4 text-green-600 dark:text-green-400" />
                <h4 className="text-sm font-medium">From Logs</h4>
              </div>
              {conflict.log_status && (
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-muted-foreground">Status:</span>
                  <Badge variant={conflict.log_status === 'passed' ? 'low' : 'critical'}>
                    {conflict.log_status === 'passed' ? 'PASSED' : 'VIOLATION'}
                  </Badge>
                </div>
              )}
              {conflict.log_value && (
                <p className="text-sm font-mono text-foreground">
                  Value: {conflict.log_value}
                </p>
              )}
              {!conflict.log_status && !conflict.log_value && (
                <p className="text-xs text-muted-foreground italic">No specific value available</p>
              )}
            </div>

            <div className="bg-muted/40 rounded-lg p-3 border border-border">
              <div className="flex items-center gap-2 mb-2">
                <Image className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                <h4 className="text-sm font-medium">From Chart</h4>
              </div>
              {conflict.chart_status && (
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-muted-foreground">Status:</span>
                  <Badge variant={conflict.chart_status === 'passed' ? 'low' : 'critical'}>
                    {conflict.chart_status === 'passed' ? 'PASSED' : 'VIOLATION'}
                  </Badge>
                </div>
              )}
              {conflict.chart_value && (
                <p className="text-sm font-mono text-foreground">
                  Value: {conflict.chart_value}
                </p>
              )}
              {!conflict.chart_status && !conflict.chart_value && (
                <p className="text-xs text-muted-foreground italic">No specific value available</p>
              )}
            </div>
          </div>

          <div className="border-t border-border pt-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-1">Rule</h4>
                <p className="text-sm font-mono text-primary">{conflict.rule_id}</p>
              </div>
              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-1">Detected</h4>
                <p className="text-sm">{new Date(conflict.timestamp).toLocaleString()}</p>
              </div>
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  )
}

export function ConflictsSection({ findings, className }: ConflictsSectionProps) {
  if (!findings || findings.length === 0) {
    return null
  }

  const forReview = findings.filter((f) => f.for_human_review)

  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-base font-medium flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400" />
          Conflicts Requiring Review ({findings.length})
        </h3>
        {forReview.length > 0 && (
          <Badge variant="high" className="flex items-center gap-1">
            <Eye className="h-3 w-3" />
            {forReview.length} for review
          </Badge>
        )}
      </div>
      <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900 rounded-lg p-3">
        <div className="flex items-start gap-2">
          <Info className="h-4 w-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
              Source Data Conflicts Detected
            </p>
            <p className="text-xs text-amber-700 dark:text-amber-300 mt-0.5">
              These findings show discrepancies between log data (ground truth) and chart image analysis.
              Log data takes precedence, but chart anomalies may indicate real issues requiring visual verification.
            </p>
          </div>
        </div>
      </div>
      {findings.map((conflict) => (
        <ConflictItem key={conflict.finding_id} conflict={conflict} />
      ))}
    </div>
  )
}

export function CorrelationSummaryCard({
  total_correlated,
  total_conflicting,
  avg_correlation_confidence,
}: {
  total_correlated?: number
  total_conflicting?: number
  avg_correlation_confidence?: number
}) {
  if (total_correlated === undefined && total_conflicting === undefined) {
    return null
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <GitMerge className="h-4 w-4 text-primary" />
          Multi-Modal Analysis Summary
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4">
          {total_correlated !== undefined && (
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                {total_correlated}
              </p>
              <p className="text-xs text-muted-foreground">Correlated</p>
            </div>
          )}
          {total_conflicting !== undefined && (
            <div className="text-center">
              <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                {total_conflicting}
              </p>
              <p className="text-xs text-muted-foreground">Conflicts</p>
            </div>
          )}
          {avg_correlation_confidence !== undefined && (
            <div className="text-center">
              <p className="text-2xl font-bold text-primary">
                {Math.round(avg_correlation_confidence * 100)}%
              </p>
              <p className="text-xs text-muted-foreground">Avg Confidence</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export default CorrelationInsights
