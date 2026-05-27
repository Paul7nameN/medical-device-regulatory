import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, Tabs, TabsList, TabsTrigger, TabsContent, Badge, Button } from '@/components/ui'
import { ChevronDown, ChevronUp, ClipboardList, AlertTriangle, Clock, Wrench } from 'lucide-react'
import type { ActionPlan, ActionItem } from '@/lib/api'
import { RISK_LEVEL_COLORS } from './'
import { cn } from '@/lib/utils'

interface ActionPlanCardProps {
  actionPlan: ActionPlan
  className?: string
}

function ActionItemCard({ item }: { item: ActionItem }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const riskColors = RISK_LEVEL_COLORS[item.priority]

  return (
    <Card className={cn(riskColors.border, 'overflow-hidden')}>
      <CardHeader
        className="pb-2 cursor-pointer hover:bg-muted/40 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant={riskColors.badge as any}>
                {item.priority.toUpperCase()}
              </Badge>
            </div>
            <CardTitle className="text-sm font-medium">{item.action}</CardTitle>
          </div>
          {(item.steps || item.why_needed || item.rationale) && (
            <Button variant="ghost" size="icon" className="h-8 w-8 flex-shrink-0">
              {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
          )}
        </div>
      </CardHeader>
      {isExpanded && (item.steps || item.why_needed || item.rationale) && (
        <CardContent className="space-y-3 pt-0">
          {item.why_needed && (
            <div>
              <h4 className="text-xs font-medium text-slate-600 mb-1">Why Needed</h4>
              <p className="text-sm text-slate-600">{item.why_needed}</p>
            </div>
          )}
          {item.rationale && (
            <div>
              <h4 className="text-xs font-medium text-slate-600 mb-1">Rationale</h4>
              <p className="text-sm text-slate-600">{item.rationale}</p>
            </div>
          )}
          {item.steps && item.steps.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-slate-600 mb-2">Steps</h4>
              <ol className="space-y-1 list-decimal list-inside">
                {item.steps.map((step, i) => (
                  <li key={i} className="text-sm text-slate-600">{step}</li>
                ))}
              </ol>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}

function ActionSection({ title, items, icon: Icon }: { title: string; items: ActionItem[]; icon: React.ElementType }) {
  if (!items || items.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        <Icon className="h-8 w-8 mx-auto mb-2 text-slate-300" />
        <p className="text-sm">No {title.toLowerCase()} actions</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {items.map((item, i) => (
        <ActionItemCard key={i} item={item} />
      ))}
    </div>
  )
}

export function ActionPlanCard({ actionPlan, className }: ActionPlanCardProps) {
  const hasImmediate = actionPlan.immediate_actions_0_1h && actionPlan.immediate_actions_0_1h.length > 0
  const hasShortTerm = actionPlan.short_term_24h && actionPlan.short_term_24h.length > 0
  const hasLongTerm = actionPlan.long_term_maintenance && actionPlan.long_term_maintenance.length > 0

  const defaultTab = hasImmediate ? 'immediate' : hasShortTerm ? 'short' : hasLongTerm ? 'long' : 'immediate'

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <ClipboardList className="h-5 w-5 text-primary" />
          <CardTitle className="text-base font-medium">Action Plan</CardTitle>
        </div>
        {actionPlan.summary && (
          <p className="text-sm text-slate-600 mt-1">{actionPlan.summary}</p>
        )}
      </CardHeader>
      <CardContent>
        <Tabs defaultValue={defaultTab}>
          <TabsList className="w-full grid grid-cols-3">
            <TabsTrigger value="immediate" disabled={!hasImmediate}>
              <AlertTriangle className="h-4 w-4 mr-1 text-red-500" />
              Immediate
            </TabsTrigger>
            <TabsTrigger value="short" disabled={!hasShortTerm}>
              <Clock className="h-4 w-4 mr-1 text-orange-500" />
              24h
            </TabsTrigger>
            <TabsTrigger value="long" disabled={!hasLongTerm}>
              <Wrench className="h-4 w-4 mr-1 text-blue-500" />
              Long Term
            </TabsTrigger>
          </TabsList>
          <TabsContent value="immediate" className="mt-4">
            <ActionSection
              title="Immediate (0-1h)"
              items={actionPlan.immediate_actions_0_1h}
              icon={AlertTriangle}
            />
          </TabsContent>
          <TabsContent value="short" className="mt-4">
            <ActionSection
              title="Short Term (24h)"
              items={actionPlan.short_term_24h}
              icon={Clock}
            />
          </TabsContent>
          <TabsContent value="long" className="mt-4">
            <ActionSection
              title="Long Term Maintenance"
              items={actionPlan.long_term_maintenance}
              icon={Wrench}
            />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
