import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from '@/components/ui'
import { ChevronDown, ChevronUp, AlertCircle, Search, CheckCircle, Lightbulb } from 'lucide-react'
import type { Insight } from '@/lib/api'
import { RISK_LEVEL_COLORS } from './'
import { cn } from '@/lib/utils'

interface InsightsListProps {
  insights: Insight[]
  className?: string
}

function InsightItem({ insight }: { insight: Insight }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const riskColors = RISK_LEVEL_COLORS[insight.priority]

  const categoryIcons: Record<string, React.ReactNode> = {
    sensor: <Search className="h-4 w-4" />,
    power: <AlertCircle className="h-4 w-4" />,
    cooling: <CheckCircle className="h-4 w-4" />,
    operational: <Lightbulb className="h-4 w-4" />,
    environmental: <Lightbulb className="h-4 w-4" />,
    thermal: <AlertCircle className="h-4 w-4" />,
    data: <CheckCircle className="h-4 w-4" />,
    alarm: <AlertCircle className="h-4 w-4" />,
  }

  const contributionPercent = Math.round(insight.risk_score_contribution * 100)

  return (
    <Card className={cn('transition-all', riskColors.border)}>
      <CardHeader
        className="pb-2 cursor-pointer hover:bg-muted/40 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <Badge variant={riskColors.badge as any}>
                {insight.priority.toUpperCase()}
              </Badge>
              <Badge variant="outline" className="flex items-center gap-1">
                {categoryIcons[insight.category] || <Lightbulb className="h-3 w-3" />}
                <span className="capitalize">{insight.category}</span>
              </Badge>
              {contributionPercent > 0 && (
                <span className="text-xs text-muted-foreground">
                  {contributionPercent}% of risk
                </span>
              )}
            </div>
            <CardTitle className="text-sm font-medium">{insight.title}</CardTitle>
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8 flex-shrink-0">
            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </Button>
        </div>
      </CardHeader>
      {isExpanded && (
        <CardContent className="space-y-4">
          {insight.evidence.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-foreground mb-2">Evidence</h4>
              <ul className="space-y-1">
                {insight.evidence.map((ev, i) => (
                  <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    {ev}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {insight.why_matters && (
            <div>
              <h4 className="text-sm font-medium text-foreground mb-1">Why This Matters</h4>
              <p className="text-sm text-muted-foreground">{insight.why_matters}</p>
            </div>
          )}
          {insight.risk_factors.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-foreground mb-2">Risk Factors</h4>
              <div className="flex flex-wrap gap-2">
                {insight.risk_factors.map((rf, i) => (
                  <Badge
                    key={i}
                    variant={RISK_LEVEL_COLORS[rf.severity.toLowerCase() as keyof typeof RISK_LEVEL_COLORS]?.badge as any || 'outline'}
                  >
                    {rf.factor}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          {contributionPercent > 0 && (
            <div>
              <h4 className="text-sm font-medium text-foreground mb-2">Risk Contribution</h4>
              <div className="w-full bg-border rounded-full h-2">
                <div
                  className={cn('h-2 rounded-full', RISK_LEVEL_COLORS[insight.priority]?.badge === 'critical' ? 'bg-red-500 dark:bg-red-600' : RISK_LEVEL_COLORS[insight.priority]?.badge === 'high' ? 'bg-orange-500 dark:bg-orange-600' : 'bg-yellow-500 dark:bg-yellow-400')}
                  style={{ width: `${Math.min(contributionPercent, 100)}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                This insight contributes {contributionPercent}% to the overall risk score
              </p>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}

export function InsightsList({ insights, className }: InsightsListProps) {
  if (!insights || insights.length === 0) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-primary" />
            AI Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No insights available for this analysis.</p>
        </CardContent>
      </Card>
    )
  }

  const critical = insights.filter((i) => i.priority === 'critical')
  const high = insights.filter((i) => i.priority === 'high')
  const medium = insights.filter((i) => i.priority === 'medium')
  const low = insights.filter((i) => i.priority === 'low')

  const sortedInsights = [...critical, ...high, ...medium, ...low]

  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-base font-medium flex items-center gap-2">
          <Lightbulb className="h-5 w-5 text-primary" />
          AI Insights ({insights.length})
        </h3>
        <div className="flex items-center gap-2 text-sm">
          {critical.length > 0 && <Badge variant="critical">Critical: {critical.length}</Badge>}
          {high.length > 0 && <Badge variant="high">High: {high.length}</Badge>}
          {medium.length > 0 && <Badge variant="medium">Medium: {medium.length}</Badge>}
        </div>
      </div>
      {sortedInsights.map((insight) => (
        <InsightItem key={insight.id} insight={insight} />
      ))}
    </div>
  )
}
