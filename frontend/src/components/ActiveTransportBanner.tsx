import { Link, useLocation } from 'react-router-dom'
import { Badge, Button } from '@/components/ui'
import { Radio, Play, ChevronRight } from 'lucide-react'
import { useLiveTransport } from '@/lib/context/LiveTransportContext'

export function ActiveTransportBanner() {
  const location = useLocation()
  const {
    isRunning,
    elapsedSec,
    tickIndex,
    totalReplayBatches,
    speed,
    alerts,
    deviceId,
    formatElapsed,
    scenario,
    sourceMode,
    scenarioLabels,
  } = useLiveTransport()

  const isOnLivePage = location.pathname === '/live'

  if (!isRunning || isOnLivePage) {
    return null
  }

  const criticalAlerts = alerts.filter((a) => a.severity === 'critical').length
  const highAlerts = alerts.filter((a) => a.severity === 'high').length
  const hasImportantAlerts = criticalAlerts > 0 || highAlerts > 0

  return (
    <Link
      to="/live"
      className="block no-underline"
    >
      <div className={`
        px-4 py-3 border-b cursor-pointer transition-all duration-200
        ${hasImportantAlerts
          ? 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-900 hover:bg-red-100 dark:hover:bg-red-950/40'
          : 'bg-primary/5 dark:bg-primary/10 border-primary/20 hover:bg-primary/10 dark:hover:bg-primary/15'
        }
      `}>
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <div className="relative flex-shrink-0">
              <Radio className={`h-5 w-5 ${hasImportantAlerts ? 'text-red-600 dark:text-red-400' : 'text-primary'}`} />
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <Badge
                  variant={hasImportantAlerts ? 'critical' : 'secondary'}
                  className="gap-1 animate-pulse"
                >
                  <Play className="h-3 w-3" fill="currentColor" />
                  LIVE
                </Badge>
                <span className="text-sm font-medium text-foreground">
                  {deviceId}
                </span>
                <span className="text-xs text-muted-foreground hidden sm:inline">
                  {sourceMode === 'simulated'
                    ? scenarioLabels[scenario]
                    : 'Log replay'
                  }
                </span>
              </div>
              <div className="flex items-center gap-3 mt-0.5 text-xs text-muted-foreground">
                <span>{formatElapsed(elapsedSec)}</span>
                <span>·</span>
                <span>
                  {tickIndex}{totalReplayBatches > 0 ? ` / ${totalReplayBatches}` : ''} ticks
                </span>
                <span>·</span>
                <span>×{speed}</span>
                {alerts.length > 0 && (
                  <>
                    <span>·</span>
                    <span className={criticalAlerts > 0 ? 'text-red-600 dark:text-red-400 font-medium' : ''}>
                      {alerts.length} alert{alerts.length !== 1 ? 's' : ''}
                      {criticalAlerts > 0 && ` (${criticalAlerts} critical)`}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>

          <Button
            variant="ghost"
            size="sm"
            className="hidden sm:flex touch-target"
          >
            <span className="mr-1">Return</span>
            <ChevronRight className="h-4 w-4" />
          </Button>

          <ChevronRight className="h-4 w-4 text-muted-foreground sm:hidden flex-shrink-0" />
        </div>
      </div>
    </Link>
  )
}
