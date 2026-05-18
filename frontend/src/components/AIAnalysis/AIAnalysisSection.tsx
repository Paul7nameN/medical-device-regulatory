import { Brain, Sparkles } from 'lucide-react'
import type { AIAnalysisResult } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import { RiskOverviewCard } from './RiskOverviewCard'
import { InsightsList } from './InsightsList'
import { PredictionsList } from './PredictionsList'
import { ActionPlanCard } from './ActionPlanCard'
import { NaturalLanguageSummary } from './NaturalLanguageSummary'

interface AIAnalysisSectionProps {
  aiAnalysis: AIAnalysisResult | undefined
  className?: string
}

export function AIAnalysisSection({ aiAnalysis, className }: AIAnalysisSectionProps) {
  if (!aiAnalysis) {
    return null
  }

  const hasInsights = aiAnalysis.insights && aiAnalysis.insights.length > 0
  const hasPredictions = aiAnalysis.predictions && aiAnalysis.predictions.length > 0
  const hasActionPlan = aiAnalysis.action_plan && (
    (aiAnalysis.action_plan.immediate_actions_0_1h && aiAnalysis.action_plan.immediate_actions_0_1h.length > 0) ||
    (aiAnalysis.action_plan.short_term_24h && aiAnalysis.action_plan.short_term_24h.length > 0) ||
    (aiAnalysis.action_plan.long_term_maintenance && aiAnalysis.action_plan.long_term_maintenance.length > 0)
  )
  const hasSummary = aiAnalysis.natural_language_summary && aiAnalysis.natural_language_summary.length > 0

  return (
    <div className={className}>
      <div className="flex items-center gap-2 mb-6">
        <div className="p-2 bg-primary/10 rounded-lg">
          <Brain className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-foreground font-heading">AI Insights</h2>
          <p className="text-sm text-muted-foreground">
            Powered by intelligent analysis of your device data
          </p>
        </div>
      </div>

      {hasSummary && (
        <div className="mb-6">
          <NaturalLanguageSummary summary={aiAnalysis.natural_language_summary} />
        </div>
      )}

       <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
         <div className="lg:col-span-2 flex flex-col">
           <RiskOverviewCard riskOverview={aiAnalysis.session_risk_overview} className="h-full" />
         </div>
         <div className="lg:col-span-1 flex flex-col">
           <Card className="h-full">
             <CardHeader className="pb-2">
               <CardTitle className="text-base font-medium flex items-center gap-2">
                 <Sparkles className="h-5 w-5 text-purple-500 dark:text-purple-400" />
                 Analysis Stats
               </CardTitle>
             </CardHeader>
             <CardContent>
               <div className="grid grid-cols-2 gap-3 text-center">
                 <div className="p-3 bg-muted/40 rounded-lg">
                   <div className="text-2xl font-bold text-foreground">
                     {aiAnalysis.insights?.length || 0}
                   </div>
                   <div className="text-xs text-muted-foreground">Insights</div>
                 </div>
                 <div className="p-3 bg-muted/40 rounded-lg">
                   <div className="text-2xl font-bold text-foreground">
                     {aiAnalysis.predictions?.length || 0}
                   </div>
                   <div className="text-xs text-muted-foreground">Predictions</div>
                 </div>
               </div>
             </CardContent>
           </Card>
         </div>
       </div>

      {hasInsights && (
        <div className="mb-6">
          <InsightsList insights={aiAnalysis.insights} />
        </div>
      )}

      {hasPredictions && (
        <div className="mb-6">
          <PredictionsList predictions={aiAnalysis.predictions} />
        </div>
      )}

      {hasActionPlan && (
        <div>
          <ActionPlanCard actionPlan={aiAnalysis.action_plan} />
        </div>
      )}
    </div>
  )
}
