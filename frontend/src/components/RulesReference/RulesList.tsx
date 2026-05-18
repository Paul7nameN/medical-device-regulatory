import { useMemo, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import { RuleCard } from './RuleCard'
import { RulesFilter } from './RulesFilter'
import type { RegulatoryRule, RuleCategory, ValidationType } from '@/lib/constants/regulatoryRules'
import {
  getAllRules,
  getRulesByCategory,
  getRulesByValidationType,
} from '@/lib/constants/regulatoryRules'
import { AlertTriangle, BookOpen } from 'lucide-react'

interface RulesListProps {
  className?: string
}

export function RulesList({ className }: RulesListProps) {
  const [selectedCategory, setSelectedCategory] = useState<RuleCategory | null>(null)
  const [selectedValidationType, setSelectedValidationType] = useState<ValidationType | null>(null)

  const allRules = useMemo(() => getAllRules(), [])

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

  return (
    <div className={className}>
      <Card>
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-3">
              <BookOpen className="h-5 w-5 text-primary" />
              <CardTitle className="text-base font-medium">MED-THERM-2026 Regulatory Rules</CardTitle>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs">
              {criticalRules.length > 0 && (
                <div className="flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3 text-red-500" />
                  <span className="text-red-600 font-medium">{criticalRules.length} CRITICAL rules</span>
                </div>
              )}
              {inspectionRules.length > 0 && (
                <div className="flex items-center gap-1">
                  <span className="text-slate-500">{inspectionRules.length} require inspection</span>
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
