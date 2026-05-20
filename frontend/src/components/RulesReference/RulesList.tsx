import { useMemo, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, Badge } from '@/components/ui'
import { RuleCard } from './RuleCard'
import { RulesFilter } from './RulesFilter'
import type { RegulatoryRule, RuleCategory, ValidationType } from '@/lib/constants/regulatoryRules'
import {
  getAllRules,
  CATEGORY_NAMES,
} from '@/lib/constants/regulatoryRules'
import { AlertTriangle, BookOpen, Sparkles, FileText } from 'lucide-react'
import { useAnalysis } from '@/lib/context/AnalysisContext'
import type { ExtractedRule, RuleThresholds, RuleType } from '@/lib/api'

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

function extractedRuleToRegulatoryRule(rule: ExtractedRule): RegulatoryRule {
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
    source: rule.data_source as 'logs' | 'inspection' | 'combined' | 'images',
    confidence: rule.confidence,
    inspectionHint: rule.inspection_hint,
  }
}

interface RulesListProps {
  className?: string
}

export function RulesList({ className }: RulesListProps) {
  const { latestAnalysis } = useAnalysis()
  const [selectedCategory, setSelectedCategory] = useState<RuleCategory | null>(null)
  const [selectedValidationType, setSelectedValidationType] = useState<ValidationType | null>(null)

  const hasCustomRules = latestAnalysis?.hasCustomRules && latestAnalysis?.extractedRules && latestAnalysis.extractedRules.length > 0
  
  const rulesetName = latestAnalysis?.rulesetName || 'Custom Rules'
  const rulesetMeta = latestAnalysis?.rulesetMeta

  const allRules = useMemo(() => {
    if (hasCustomRules && latestAnalysis?.extractedRules) {
      return latestAnalysis.extractedRules.map(extractedRuleToRegulatoryRule)
    }
    return getAllRules()
  }, [hasCustomRules, latestAnalysis?.extractedRules])

  const filteredRules = useMemo(() => {
    let rules: RegulatoryRule[] = allRules

    if (selectedCategory) {
      rules = rules.filter((r) => r.category === selectedCategory)
    }

    if (selectedValidationType) {
      rules = rules.filter((r) => r.validationType === selectedValidationType)
    }

    return rules
  }, [allRules, selectedCategory, selectedValidationType])

  const criticalRules = useMemo(() => filteredRules.filter((r) => r.severity === 'critical'), [filteredRules])
  const inspectionRules = useMemo(() => filteredRules.filter((r) => r.validationType === 'inspection'), [filteredRules])
  
  const lowConfidenceRules = useMemo(() => {
    if (hasCustomRules && latestAnalysis?.extractedRules) {
      return latestAnalysis.extractedRules.filter((r) => r.confidence < 0.7).length
    }
    return 0
  }, [hasCustomRules, latestAnalysis?.extractedRules])

  return (
    <div className={className}>
      <Card>
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-3">
              {hasCustomRules ? (
                <Sparkles className="h-5 w-5 text-purple-600" />
              ) : (
                <BookOpen className="h-5 w-5 text-primary" />
              )}
              <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                <CardTitle className="text-base font-medium">
                  {hasCustomRules ? rulesetName : 'MED-THERM-2026 Regulatory Rules'}
                </CardTitle>
                 {hasCustomRules ? (
                   <Badge variant="outline" className="flex items-center gap-1 bg-purple-50 text-purple-700 border-purple-200 w-fit">
                     <FileText className="h-3 w-3" />
                     <span>
                       From {rulesetMeta?.filename || rulesetMeta?.source || 'Document'}
                     </span>
                   </Badge>
                 ) : (
                  <Badge variant="outline" className="flex items-center gap-1 w-fit">
                    <BookOpen className="h-3 w-3" />
                    <span>Default Ruleset</span>
                  </Badge>
                )}
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs">
              {criticalRules.length > 0 && (
                <div className="flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3 text-red-500" />
                  <span className="text-red-600 font-medium">{criticalRules.length} CRITICAL rules</span>
                </div>
              )}
              {lowConfidenceRules > 0 && (
                <div className="flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3 text-yellow-500" />
                  <span className="text-yellow-600 font-medium">{lowConfidenceRules} low confidence (skipped)</span>
                </div>
              )}
              {inspectionRules.length > 0 && (
                <div className="flex items-center gap-1">
                  <span className="text-slate-500">{inspectionRules.length} require inspection</span>
                </div>
              )}
              {rulesetMeta?.average_confidence !== undefined && (
                <div className="flex items-center gap-1">
                  <span className="text-slate-500">
                    Avg confidence: {(rulesetMeta.average_confidence * 100).toFixed(0)}%
                  </span>
                </div>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <RulesFilter
            selectedCategory={selectedCategory}
            selectedValidationType={selectedValidationType}
            onCategoryChange={setSelectedCategory}
            onValidationTypeChange={setSelectedValidationType}
            totalRules={allRules.length}
            filteredCount={filteredRules.length}
          />

           {filteredRules.length === 0 ? (
             <div className="text-center py-8">
               <p className="text-sm text-slate-500">No rules match the selected filters.</p>
             </div>
           ) : (
             <div className="space-y-4">
               {filteredRules.map((rule) => (
                 <RuleCard key={rule.id} rule={rule} />
               ))}
             </div>
           )}
        </CardContent>
      </Card>
    </div>
  )
}
