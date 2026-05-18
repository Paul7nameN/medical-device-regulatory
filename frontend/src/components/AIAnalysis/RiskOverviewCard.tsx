import { Card, CardContent, CardHeader, CardTitle, Badge } from '@/components/ui'
import { Minus, TrendingUp, TrendingDown, Brain, AlertTriangle } from 'lucide-react'
import type { RiskOverview } from '@/lib/api'
import { RISK_LEVEL_COLORS, TREND_INDICATOR_INFO, getRiskScoreColor, getRiskScoreBg } from './'
import { cn } from '@/lib/utils'

interface RiskOverviewCardProps {
  riskOverview: RiskOverview
  className?: string
}

export function RiskOverviewCard({ riskOverview, className }: RiskOverviewCardProps) {
  const riskColors = RISK_LEVEL_COLORS[riskOverview.risk_level]
  const trendInfo = TREND_INDICATOR_INFO[riskOverview.trend_indicator]

  const TrendIcon =
    riskOverview.trend_indicator === 'improving'
      ? TrendingDown
      : riskOverview.trend_indicator === 'deteriorating'
      ? TrendingUp
      : Minus

  const scorePercent = Math.round(riskOverview.overall_risk_score * 100)
  const circumference = 2 * Math.PI * 40
  const offset = circumference - (riskOverview.overall_risk_score * circumference)

  return (
    <Card className={cn(riskColors.border, className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium flex items-center gap-2">
          <Brain className="h-5 w-5 text-primary" />
          AI Risk Overview
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col sm:flex-row items-center gap-6">
           <div className="relative flex items-center justify-center">
             <svg className="w-28 h-28 transform -rotate-90 text-gray-200 dark:text-gray-700" viewBox="0 0 100 100">
               <circle
                 cx="50"
                 cy="50"
                 r="40"
                 fill="none"
                 stroke="currentColor"
                 strokeWidth="8"
               />
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                className={getRiskScoreBg(riskOverview.overall_risk_score)}
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                style={{ transition: 'stroke-dashoffset 0.5s ease-in-out' }}
              />
            </svg>
             <div className="absolute flex flex-col items-center">
               <span className={cn('text-2xl font-bold', getRiskScoreColor(riskOverview.overall_risk_score))}>
                 {scorePercent}%
               </span>
               <span className="text-xs text-muted-foreground">Risk Score</span>
             </div>
           </div>

           <div className="flex flex-col gap-3 w-full sm:w-auto">
             <div className="flex items-center gap-3">
               <Badge variant={riskColors.badge as any} className="text-sm px-3 py-1">
                 {riskOverview.risk_level.toUpperCase()}
               </Badge>
               <span className={cn('flex items-center gap-1 text-sm', trendInfo.color)}>
                 <TrendIcon className="h-4 w-4" />
                 {trendInfo.label}
               </span>
             </div>

             <div className="grid grid-cols-2 gap-3 text-sm">
               <div className={cn('p-3 rounded-lg', riskColors.bg)}>
                 <div className="text-xs text-muted-foreground mb-1">Primary Risk</div>
                 <div className="font-medium capitalize">{riskOverview.primary_risk_category.replace(/_/g, ' ')}</div>
               </div>
               <div className={cn('p-3 rounded-lg', riskOverview.imminent_concerns_count > 0 ? 'bg-red-50 dark:bg-red-950/30' : 'bg-muted/40')}>
                 <div className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                   <AlertTriangle className="h-3 w-3" />
                   Imminent Concerns
                 </div>
                 <div className={cn('font-medium', riskOverview.imminent_concerns_count > 0 ? 'text-red-700 dark:text-red-400' : 'text-slate-700 dark:text-slate-300')}>
                   {riskOverview.imminent_concerns_count}
                 </div>
               </div>
             </div>
           </div>
        </div>
      </CardContent>
    </Card>
  )
}
