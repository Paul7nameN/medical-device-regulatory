import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, Badge, SeverityBadge, Button } from '@/components/ui'
import { ChevronDown, ChevronUp, Info, Thermometer, AlertTriangle, Database, Zap, Fan, Shield, Settings } from 'lucide-react'
import type { RegulatoryRule, RuleSeverity, ValidationType, RuleCategory } from '@/lib/constants/regulatoryRules'
import { cn } from '@/lib/utils'

interface RuleCardProps {
  rule: RegulatoryRule
  className?: string
}

const CATEGORY_ICONS: Record<RuleCategory, React.ReactNode> = {
  TEMP: <Thermometer className="h-4 w-4" />,
  SENS: <AlertTriangle className="h-4 w-4" />,
  ALARM: <AlertTriangle className="h-4 w-4" />,
  DATA: <Database className="h-4 w-4" />,
  POWER: <Zap className="h-4 w-4" />,
  COOL: <Fan className="h-4 w-4" />,
  INS: <Shield className="h-4 w-4" />,
  OPS: <Settings className="h-4 w-4" />,
}

const SEVERITY_BORDER_COLORS: Record<RuleSeverity, string> = {
  critical: 'border-red-200',
  high: 'border-orange-200',
  medium: 'border-yellow-200',
  low: 'border-green-200',
  info: 'border-blue-200',
}

const VALIDATION_TYPE_INFO: Record<ValidationType, { label: string; variant: 'info' | 'outline' }> = {
  operational: { label: 'Operational', variant: 'info' },
  inspection: { label: 'Inspection', variant: 'outline' },
}

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const percentage = Math.round(confidence * 100)
  let color = 'text-green-600'
  if (percentage < 50) color = 'text-red-600'
  else if (percentage < 80) color = 'text-yellow-600'

  return (
    <span className={cn('text-xs font-medium', color)}>
      {percentage}%
    </span>
  )
}

export function RuleCard({ rule, className }: RuleCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const validationTypeInfo = VALIDATION_TYPE_INFO[rule.validationType]
  const borderColor = SEVERITY_BORDER_COLORS[rule.severity] || 'border-slate-200'

  const toggleExpand = () => {
    setIsExpanded(!isExpanded)
  }

  return (
    <Card className={cn('transition-all hover:shadow-md', borderColor, className)}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-4">
          <div
            className="flex-1 cursor-pointer"
            onClick={toggleExpand}
          >
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <Badge variant="default" className="font-mono text-xs">
                {rule.id}
              </Badge>
              <Badge variant="outline" className="flex items-center gap-1">
                {CATEGORY_ICONS[rule.category]}
                <span className="capitalize text-xs">{rule.categoryName}</span>
              </Badge>
              <SeverityBadge severity={rule.severity as any} />
              <Badge variant={validationTypeInfo.variant} className="text-xs">
                {validationTypeInfo.label}
              </Badge>
            </div>
            <CardTitle className="text-sm font-medium">{rule.title}</CardTitle>
            <p className="text-xs text-primary font-medium mt-1">
              {rule.threshold}
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            {rule.confidence < 1.0 && (
              <div className="flex items-center gap-1">
                <span className="text-xs text-slate-500">Confidence:</span>
                <ConfidenceBadge confidence={rule.confidence} />
              </div>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 flex-shrink-0"
              onClick={toggleExpand}
            >
              {isExpanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
        {!isExpanded && (
          <p className="text-xs text-slate-500 mt-2">
            {rule.description.length > 120
              ? rule.description.slice(0, 117) + '...'
              : rule.description}
          </p>
        )}
      </CardHeader>

      {isExpanded && (
        <CardContent className="space-y-4 pt-2 border-t border-slate-100">
          <div>
            <h4 className="text-sm font-medium text-slate-700 mb-2">Description</h4>
            <p className="text-sm text-slate-600 leading-relaxed">{rule.description}</p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-muted/40 rounded-lg p-3">
              <h4 className="text-xs font-medium text-slate-500 mb-1">Threshold</h4>
              <p className="text-sm font-mono text-primary font-medium">{rule.threshold}</p>
            </div>
            <div className="bg-muted/40 rounded-lg p-3">
              <h4 className="text-xs font-medium text-slate-500 mb-1">Severity</h4>
              <SeverityBadge severity={rule.severity as any} />
            </div>
            <div className="bg-muted/40 rounded-lg p-3">
              <h4 className="text-xs font-medium text-slate-500 mb-1">Validation Type</h4>
              <Badge variant={validationTypeInfo.variant}>{validationTypeInfo.label}</Badge>
            </div>
            <div className="bg-muted/40 rounded-lg p-3">
              <h4 className="text-xs font-medium text-slate-500 mb-1">Confidence</h4>
              <p className="text-sm font-medium">
                {Math.round(rule.confidence * 100)}%
              </p>
            </div>
          </div>

          {rule.inspectionHint && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-blue-100 rounded-lg flex-shrink-0">
                  <Info className="h-4 w-4 text-blue-600" />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-blue-800 mb-1">Inspection Required</h4>
                  <p className="text-sm text-blue-700">{rule.inspectionHint}</p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}
