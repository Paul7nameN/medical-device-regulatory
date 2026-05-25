import { useState, useMemo, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle, Badge, Button, SeverityBadge, Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui'
import { 
  ChevronDown, ChevronUp, Clock, Filter, X,
  Activity, AlertTriangle, CheckCircle, Database, Image, GitMerge,
  ChevronLeft, ChevronRight, AlertCircle
} from 'lucide-react'
import type { TimelineEvent, DataSource } from '@/lib/api'
import { compareSeverity } from '@/lib/api/types'
import { cn } from '@/lib/utils'

interface UnifiedTimelineProps {
  events: TimelineEvent[]
  title?: string
  className?: string
  maxInitialEvents?: number
}

type EventFilter = 'all' | 'critical' | 'high' | 'medium' | 'low' | 'info'
type SourceFilter = 'all' | DataSource | 'correlated'

function getEventIcon(eventType: string): React.ReactNode {
  const lower = eventType.toLowerCase()
  if (lower.includes('violation') || lower.includes('excursion')) return <AlertTriangle className="h-4 w-4" />
  if (lower.includes('recovery') || lower.includes('resolved')) return <CheckCircle className="h-4 w-4" />
  if (lower.includes('anomaly') || lower.includes('alert')) return <Activity className="h-4 w-4" />
  if (lower.includes('correlated')) return <GitMerge className="h-4 w-4" />
  return <Clock className="h-4 w-4" />
}

function extractSourceFromEvent(event: TimelineEvent): { source: DataSource | 'correlated' | null; label: string } {
  const details = event.details || {}
  
  if (details.source === 'correlated' || details.is_correlated) {
    return { source: 'correlated', label: 'Correlated' }
  }
  
  if (details.source === 'logs' || event.event_type.toLowerCase().includes('log')) {
    return { source: 'logs', label: 'Logs' }
  }
  
  if (details.source === 'images' || details.source === 'chart' || details.source === 'chart_image' || event.event_type.toLowerCase().includes('chart')) {
    return { source: 'images', label: 'Chart' }
  }
  
  if (typeof details.data_source === 'string') {
    return { source: details.data_source as DataSource, label: details.data_source }
  }
  
  return { source: null, label: 'Unknown' }
}

function getSourceColor(source: string | null): string {
  switch (source) {
    case 'logs': return 'bg-green-100 text-green-700 dark:bg-green-950/40 dark:text-green-400'
    case 'images': return 'bg-blue-100 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400'
    case 'correlated': return 'bg-orange-100 text-orange-700 dark:bg-orange-950/40 dark:text-orange-400'
    default: return 'bg-gray-100 text-gray-700 dark:bg-gray-800/60 dark:text-gray-300'
  }
}

function getSourceIcon(source: string | null): React.ReactNode {
  switch (source) {
    case 'logs': return <Database className="h-3 w-3" />
    case 'images': return <Image className="h-3 w-3" />
    case 'correlated': return <GitMerge className="h-3 w-3" />
    default: return <Activity className="h-3 w-3" />
  }
}

interface TimelineEventItemProps {
  event: TimelineEvent
  isLast: boolean
  _index?: number
}

function TimelineEventItem({ event, isLast }: TimelineEventItemProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const { source, label: sourceLabel } = extractSourceFromEvent(event)
  
  const severity = event.severity || 'info'
  const time = new Date(event.timestamp)
  
  const isCritical = severity === 'critical'
  const isHigh = severity === 'high'
  const isWarning = isCritical || isHigh

  return (
    <div className="relative pl-8">
      {!isLast && (
        <div 
          className={cn(
            'absolute left-[11px] top-6 w-0.5 h-full',
            isWarning ? 'bg-border' : 'bg-border/50'
          )}
        />
      )}
      
      <div className={cn(
        'absolute left-0 top-1.5 w-6 h-6 rounded-full border-2 flex items-center justify-center',
        isCritical 
          ? 'bg-red-50 border-red-400 dark:bg-red-950/50 dark:border-red-600'
          : isHigh
            ? 'bg-orange-50 border-orange-400 dark:bg-orange-950/50 dark:border-orange-600'
            : 'bg-background border-muted-foreground/30'
      )}>
        {isCritical ? (
          <AlertTriangle className="h-3 w-3 text-red-600 dark:text-red-400" />
        ) : isHigh ? (
          <AlertTriangle className="h-3 w-3 text-orange-600 dark:text-orange-400" />
        ) : (
          getEventIcon(event.event_type)
        )}
      </div>

      <Card className={cn(
        'mb-3 transition-all cursor-pointer hover:shadow-sm',
        isCritical 
          ? 'border-l-4 border-l-red-500 bg-red-50/30 dark:bg-red-950/10'
          : isHigh
            ? 'border-l-4 border-l-orange-500 bg-orange-50/30 dark:bg-orange-950/10'
            : 'border-l-2 border-l-transparent'
      )}>
        <CardHeader 
          className="pb-2 pt-3 px-3" 
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-1.5 mb-1">
                {event.severity && (
                  <SeverityBadge severity={event.severity} />
                )}
                {source && (
                  <Badge variant="outline" className={cn('flex items-center gap-1 h-5 text-xs', getSourceColor(source))}>
                    {getSourceIcon(source)}
                    {sourceLabel}
                  </Badge>
                )}
                <Badge variant="outline" className="h-5 text-xs">
                  {event.event_type}
                </Badge>
                {event.rule_id && (
                  <code className="text-xs font-mono bg-muted px-1.5 py-0.5 rounded text-primary-700">
                    {event.rule_id}
                  </code>
                )}
              </div>
              <p className="text-sm font-medium text-foreground">{event.description}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {time.toLocaleTimeString()}
                {event.details?.from_source != null && (
                  <span className="ml-2">
                    via: {String(event.details.from_source)}
                  </span>
                )}
              </p>
            </div>
            <Button variant="ghost" size="icon" className="h-7 w-7 flex-shrink-0">
              {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
          </div>
        </CardHeader>
        {isExpanded && (
          <CardContent className="pb-3 pt-2 px-3 border-t border-border/50">
            <div className="space-y-2">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="bg-muted/40 rounded-lg p-2">
                  <p className="text-xs text-muted-foreground mb-0.5">Time</p>
                  <p className="font-medium">{time.toLocaleString()}</p>
                </div>
                <div className="bg-muted/40 rounded-lg p-2">
                  <p className="text-xs text-muted-foreground mb-0.5">Event Type</p>
                  <p className="font-medium">{event.event_type}</p>
                </div>
              </div>
              {event.details && Object.keys(event.details).length > 0 && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-1.5">Details</p>
                  <div className="bg-muted/40 rounded-lg p-2.5 space-y-1.5">
                    {Object.entries(event.details).map(([key, value]) => {
                      if (['source', 'is_correlated', 'data_source'].includes(key)) return null
                      return (
                        <div key={key} className="flex items-start gap-2 text-xs">
                          <span className="text-muted-foreground font-medium whitespace-nowrap">{key}:</span>
                          <span className="text-foreground break-all">
                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  )
}

export function UnifiedTimeline({
  events,
  title = 'Unified Timeline',
  className,
  maxInitialEvents = 20,
}: UnifiedTimelineProps) {
  const [severityFilter, setSeverityFilter] = useState<EventFilter>('all')
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>('all')
  const [showAll, setShowAll] = useState(false)
  const [showOnlyViolations, setShowOnlyViolations] = useState(true)
  const [currentViolationIndex, setCurrentViolationIndex] = useState(0)

   const isViolationEvent = useCallback((event: TimelineEvent): boolean => {
     return event.event_type.toLowerCase().includes('violation') || 
            (!!event.severity && event.severity !== 'info' && !event.event_type.toLowerCase().includes('log_'))
   }, [])

  const filteredEvents = useMemo(() => {
    let result = [...events]
    
    if (showOnlyViolations) {
      result = result.filter(isViolationEvent)
    }
    
    if (severityFilter !== 'all') {
      result = result.filter((e) => e.severity === severityFilter)
    }
    
    if (sourceFilter !== 'all') {
      result = result.filter((e) => {
        const { source } = extractSourceFromEvent(e)
        return source === sourceFilter
      })
    }
    
    return result.sort((a, b) => {
      const severityCompare = compareSeverity(a.severity || 'info', b.severity || 'info')
      if (severityCompare !== 0) {
        return severityCompare
      }
      return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    })
  }, [events, severityFilter, sourceFilter, showOnlyViolations, isViolationEvent])

  const violationEvents = useMemo(() => {
    return filteredEvents.filter(isViolationEvent)
  }, [filteredEvents, isViolationEvent])

  const displayEvents = showAll 
    ? filteredEvents 
    : filteredEvents.slice(0, maxInitialEvents)

  const hasMore = filteredEvents.length > maxInitialEvents

  const clearFilters = () => {
    setSeverityFilter('all')
    setSourceFilter('all')
    setShowOnlyViolations(false)
  }

   const hasFilters = severityFilter !== 'all' || sourceFilter !== 'all' || showOnlyViolations

   const goToPreviousViolation = () => {
    if (currentViolationIndex > 0) {
      setCurrentViolationIndex(currentViolationIndex - 1)
    }
  }

  const goToNextViolation = () => {
    if (currentViolationIndex < violationEvents.length - 1) {
      setCurrentViolationIndex(currentViolationIndex + 1)
    }
  }

  if (!events || events.length === 0) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No timeline events available for this analysis.</p>
        </CardContent>
      </Card>
    )
  }

  const criticalCount = events.filter((e) => e.severity === 'critical').length
  const highCount = events.filter((e) => e.severity === 'high').length
  const mediumCount = events.filter((e) => e.severity === 'medium').length
  const lowCount = events.filter((e) => e.severity === 'low').length
  const violationCount = violationEvents.length

  return (
    <div className={cn('space-y-3 w-full min-w-0', className)}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-base font-medium flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" />
            {title} ({filteredEvents.length})
          </h3>
          
          {violationCount > 0 && (
            <div className="flex flex-wrap items-center gap-1.5">
              {criticalCount > 0 && (
                <Badge variant="critical" className="flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />
                  Critical: {criticalCount}
                </Badge>
              )}
              {highCount > 0 && (
                <Badge variant="high" className="flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3" />
                  High: {highCount}
                </Badge>
              )}
              {mediumCount > 0 && (
                <Badge variant="medium" className="flex items-center gap-1">
                  Medium: {mediumCount}
                </Badge>
              )}
              {lowCount > 0 && (
                <Badge variant="low" className="flex items-center gap-1">
                  Low: {lowCount}
                </Badge>
              )}
            </div>
          )}
        </div>
        
        <div className="flex flex-wrap items-center gap-2">
          <label className="flex items-center gap-1.5 text-sm cursor-pointer select-none">
            <input
              type="checkbox"
              checked={showOnlyViolations}
              onChange={(e) => setShowOnlyViolations(e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="text-xs font-medium">Show only violations</span>
          </label>

          {violationCount > 0 && (
            <div className="flex items-center gap-1 border rounded-lg px-2 py-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={goToPreviousViolation}
                disabled={currentViolationIndex === 0}
              >
                <ChevronLeft className="h-3 w-3" />
              </Button>
              <span className="text-xs font-mono min-w-[60px] text-center">
                {currentViolationIndex + 1}/{violationCount}
              </span>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={goToNextViolation}
                disabled={currentViolationIndex === violationCount - 1}
              >
                <ChevronRight className="h-3 w-3" />
              </Button>
            </div>
          )}

          <Select
            value={severityFilter}
            onValueChange={(v) => setSeverityFilter(v as EventFilter)}
          >
            <SelectTrigger className="w-[130px] h-8 text-xs">
              <Filter className="h-3.5 w-3.5 mr-1.5" />
              <SelectValue placeholder="Severity" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Severities</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="info">Info</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={sourceFilter}
            onValueChange={(v) => setSourceFilter(v as SourceFilter)}
          >
            <SelectTrigger className="w-[130px] h-8 text-xs">
              <Database className="h-3.5 w-3.5 mr-1.5" />
              <SelectValue placeholder="Source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Sources</SelectItem>
              <SelectItem value="logs">From Logs</SelectItem>
              <SelectItem value="images">From Charts</SelectItem>
              <SelectItem value="correlated">Correlated</SelectItem>
            </SelectContent>
          </Select>

          <Button 
            variant="ghost" 
            size="sm" 
            onClick={clearFilters} 
            className={cn(
              "h-8 px-2 transition-opacity",
              !hasFilters && "invisible pointer-events-none"
            )}
          >
            <X className="h-3.5 w-3.5 mr-1" />
            <span className="text-xs">Clear</span>
          </Button>
        </div>
      </div>

      {filteredEvents.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <Filter className="h-8 w-8 mx-auto mb-2 text-muted-foreground/50" />
            <p className="text-sm font-medium text-foreground">No events match your filters</p>
            <p className="text-xs text-muted-foreground mt-1">Try adjusting your filter criteria</p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="pt-2">
             {displayEvents.map((event, idx) => (
               <TimelineEventItem
                 key={`${event.timestamp}-${idx}`}
                 event={event}
                 isLast={idx === displayEvents.length - 1 && !showAll}
                 _index={idx}
               />
             ))}
          </div>

          {hasMore && (
            <div className="text-center pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowAll(!showAll)}
              >
                {showAll ? (
                  <>Show Less</>
                ) : (
                  <>Show {filteredEvents.length - maxInitialEvents} More Events</>
                )}
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default UnifiedTimeline
