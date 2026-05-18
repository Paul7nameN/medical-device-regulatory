import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import { Badge } from '@/components/ui'
import { CheckCircle, XCircle, AlertTriangle } from 'lucide-react'

interface PassFailSummaryProps {
  passed: number
  failed: number
  critical?: number
  high?: number
  title?: string
  showSeverity?: boolean
  className?: string
}

export function PassFailSummary({
  passed,
  failed,
  critical = 0,
  high = 0,
  title = 'Summary',
  showSeverity = true,
  className,
}: PassFailSummaryProps) {
  const total = passed + failed
  const passRate = total > 0 ? Math.round((passed / total) * 100) : 0

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
         <div className="flex items-center gap-4 mb-4">
           <div className="flex items-center gap-2">
             <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
             <span className="text-2xl font-bold text-green-600 dark:text-green-400">{passed}</span>
             <Badge variant="low">Passed</Badge>
           </div>
           <span className="text-slate-300 dark:text-slate-600">/</span>
           <div className="flex items-center gap-2">
             <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
             <span className="text-2xl font-bold text-red-600 dark:text-red-400">{failed}</span>
             <Badge variant={failed > 0 ? 'critical' : 'info'}>Failed</Badge>
           </div>
         </div>

         <div className="h-2 bg-muted rounded-full overflow-hidden">
           <div
             className={`h-full rounded-full transition-all duration-500 ${
               passRate >= 90
                 ? 'bg-green-500 dark:bg-green-600'
                 : passRate >= 70
                   ? 'bg-yellow-500 dark:bg-yellow-600'
                   : passRate >= 50
                     ? 'bg-orange-500 dark:bg-orange-600'
                     : 'bg-red-500 dark:bg-red-600'
             }`}
             style={{ width: `${passRate}%` }}
           />
         </div>
         <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{passRate}% pass rate ({passed}/{total})</p>

         {showSeverity && failed > 0 && (
           <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
             <div className="flex flex-wrap items-center gap-3">
               {critical > 0 && (
                 <div className="flex items-center gap-1.5">
                   <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-400" />
                   <span className="text-sm font-medium text-red-700 dark:text-red-400">{critical} Critical</span>
                 </div>
               )}
               {high > 0 && (
                 <div className="flex items-center gap-1.5">
                   <AlertTriangle className="h-4 w-4 text-orange-600 dark:text-orange-400" />
                   <span className="text-sm font-medium text-orange-700 dark:text-orange-400">{high} High</span>
                 </div>
               )}
               {!critical && !high && failed > 0 && (
                 <p className="text-sm text-slate-500 dark:text-slate-400">No critical or high severity failures</p>
               )}
             </div>
           </div>
         )}
      </CardContent>
    </Card>
  )
}

interface PassFailSummarySkeletonProps {
  className?: string
}

export function PassFailSummarySkeleton({ className }: PassFailSummarySkeletonProps) {
  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="h-5 w-24 bg-border rounded animate-pulse" />
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 mb-4">
          <div className="h-8 w-20 bg-border rounded animate-pulse" />
          <div className="h-8 w-20 bg-border rounded animate-pulse" />
        </div>
        <div className="h-2 bg-border rounded-full animate-pulse" />
        <div className="h-3 w-32 bg-border rounded mt-1 animate-pulse" />
      </CardContent>
    </Card>
  )
}

export default PassFailSummary
