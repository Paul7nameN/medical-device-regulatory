import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import { REG_CATEGORIES, type RegCategory } from '@/lib/api'
import { AlertTriangle, Thermometer, Activity, Shield, Zap, Fan, Box, BarChart3 } from 'lucide-react'
import { Badge } from '@/components/ui'
import { cn } from '@/lib/utils'

interface SeverityCounts {
  critical: number
  high: number
  medium: number
  low: number
  info: number
}

interface SummaryCardProps {
  category: RegCategory
  counts: SeverityCounts
  onClick?: () => void
  className?: string
}

const categoryIcons: Record<RegCategory, React.ReactNode> = {
  TEMP: <Thermometer className="h-5 w-5" />,
  SENS: <Activity className="h-5 w-5" />,
  ALARM: <AlertTriangle className="h-5 w-5" />,
  DATA: <Shield className="h-5 w-5" />,
  POWER: <Zap className="h-5 w-5" />,
  COOL: <Fan className="h-5 w-5" />,
  INS: <Box className="h-5 w-5" />,
  OPS: <BarChart3 className="h-5 w-5" />,
}

const categoryColors: Record<RegCategory, string> = {
  TEMP: 'text-orange-600 bg-orange-50 dark:text-orange-400 dark:bg-orange-950/40',
  SENS: 'text-purple-600 bg-purple-50 dark:text-purple-400 dark:bg-purple-950/40',
  ALARM: 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-950/40',
  DATA: 'text-teal-600 bg-teal-50 dark:text-teal-400 dark:bg-teal-950/40',
  POWER: 'text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-950/40',
  COOL: 'text-cyan-600 bg-cyan-50 dark:text-cyan-400 dark:bg-cyan-950/40',
  INS: 'text-indigo-600 bg-indigo-50 dark:text-indigo-400 dark:bg-indigo-950/40',
  OPS: 'text-slate-600 bg-slate-50 dark:text-slate-400 dark:bg-slate-800/50',
}

export function SummaryCard({ category, counts, onClick, className }: SummaryCardProps) {
  const total = counts.critical + counts.high + counts.medium + counts.low
  const hasIssues = total > 0

   return (
     <Card
       onClick={onClick}
       className={cn(
         'transition-all duration-200',
         onClick && 'hover:shadow-lg hover:border-primary/50',
         hasIssues && total > 3 && 'border-red-200',
         className
       )}
       role={onClick ? 'button' : undefined}
       tabIndex={onClick ? 0 : undefined}
       onKeyDown={(e) => {
         if (onClick && (e.key === 'Enter' || e.key === ' ')) {
           e.preventDefault()
           onClick()
         }
       }}
     >
       <CardHeader className="pb-2">
         <div className="flex items-center justify-between min-h-[48px]">
           <CardTitle className="text-base font-medium flex items-center gap-2">
             <span className={cn(
               'p-2 rounded-md flex-shrink-0',
               categoryColors[category]
             )}>
               {categoryIcons[category]}
             </span>
             <span className="text-sm sm:text-base leading-tight">{REG_CATEGORIES[category]}</span>
           </CardTitle>
           {hasIssues && (
             <Badge variant={counts.critical > 0 ? 'critical' : counts.high > 0 ? 'high' : 'medium'} className="flex-shrink-0">
               {total} issue{total !== 1 ? 's' : ''}
             </Badge>
           )}
           {!hasIssues && (
             <Badge variant="low" className="flex-shrink-0">No issues</Badge>
           )}
         </div>
       </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {counts.critical > 0 && (
            <Badge variant="critical" aria-label={`${counts.critical} critical violations`}>
              Critical: {counts.critical}
            </Badge>
          )}
          {counts.high > 0 && (
            <Badge variant="high" aria-label={`${counts.high} high priority violations`}>
              High: {counts.high}
            </Badge>
          )}
          {counts.medium > 0 && (
            <Badge variant="medium" aria-label={`${counts.medium} medium priority violations`}>
              Medium: {counts.medium}
            </Badge>
          )}
          {counts.low > 0 && (
            <Badge variant="low" aria-label={`${counts.low} low priority violations`}>
              Low: {counts.low}
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export function createEmptySeverityCounts(): SeverityCounts {
  return {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    info: 0,
  }
}
