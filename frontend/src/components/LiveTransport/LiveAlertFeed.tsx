import { Card, CardContent, CardHeader, CardTitle, Badge } from '@/components/ui'
import { AlertTriangle, Info, ShieldAlert } from 'lucide-react'
import type { LiveAlert } from '@/lib/live/types'
import { cn } from '@/lib/utils'

interface LiveAlertFeedProps {
  alerts: LiveAlert[]
  className?: string
}

const severityVariant: Record<LiveAlert['severity'], string> = {
  critical: 'border-red-300 dark:border-red-900 bg-red-50 dark:bg-red-950/40',
  high: 'border-orange-300 dark:border-orange-900 bg-orange-50 dark:bg-orange-950/30',
  medium: 'border-yellow-300 dark:border-yellow-900 bg-yellow-50 dark:bg-yellow-950/30',
  low: 'border-green-300 dark:border-green-900 bg-green-50 dark:bg-green-950/20',
  info: 'border-border bg-muted/40',
}

export function LiveAlertFeed({ alerts, className }: LiveAlertFeedProps) {
  return (
    <Card className={cn('h-full flex flex-col', className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-primary" />
          Live alerts
          {alerts.length > 0 && (
            <Badge variant="critical" className="ml-1">
              {alerts.length}
            </Badge>
          )}
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          Rule checks run on each telemetry tick. Advice is indicative for operators.
        </p>
      </CardHeader>
      <CardContent className="flex-1 overflow-y-auto max-h-[520px] space-y-3">
        {alerts.length === 0 ? (
          <div className="text-center py-10 text-muted-foreground">
            <Info className="h-10 w-10 mx-auto mb-3 opacity-50" />
            <p className="text-sm">No violations yet. Monitoring in progress…</p>
          </div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={cn('rounded-lg border p-3', severityVariant[alert.severity])}
            >
              <div className="flex items-start gap-2">
                <AlertTriangle
                  className={cn(
                    'h-4 w-4 mt-0.5 flex-shrink-0',
                    alert.severity === 'critical' || alert.severity === 'high'
                      ? 'text-red-600 dark:text-red-400'
                      : 'text-yellow-600 dark:text-yellow-400'
                  )}
                />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-foreground">{alert.title}</span>
                    <Badge variant="outline" className="text-xs">
                      {alert.ruleId}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{alert.message}</p>
                  <p className="text-sm mt-2 font-medium text-foreground">
                    Recommended: {alert.advice}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  )
}
