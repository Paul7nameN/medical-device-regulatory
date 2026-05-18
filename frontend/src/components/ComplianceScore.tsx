import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import { CheckCircle, AlertTriangle, XCircle, TrendingUp } from 'lucide-react'

interface ComplianceScoreProps {
  score: number
  totalRules?: number
  passedRules?: number
  failedRules?: number
  className?: string
}

function getScoreColor(score: number): string {
  if (score >= 90) return 'text-cta dark:text-cta'
  if (score >= 70) return 'text-yellow-600 dark:text-yellow-400'
  if (score >= 50) return 'text-orange-600 dark:text-orange-400'
  return 'text-red-600 dark:text-red-400'
}

function getScoreBg(score: number): string {
  if (score >= 90) return 'stroke-cta dark:stroke-cta'
  if (score >= 70) return 'stroke-yellow-500 dark:stroke-yellow-400'
  if (score >= 50) return 'stroke-orange-500 dark:stroke-orange-400'
  return 'stroke-red-500 dark:stroke-red-400'
}

function getScoreStatus(score: number): { icon: React.ReactNode; label: string } {
  if (score >= 90) return { icon: <CheckCircle className="h-5 w-5 text-cta" />, label: 'Excellent' }
  if (score >= 70) return { icon: <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />, label: 'Good' }
  if (score >= 50) return { icon: <AlertTriangle className="h-5 w-5 text-orange-600 dark:text-orange-400" />, label: 'Needs Attention' }
  return { icon: <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />, label: 'Critical' }
}

export function ComplianceScore({ score, totalRules, passedRules, failedRules, className }: ComplianceScoreProps) {
  const status = getScoreStatus(score)
  const circumference = 2 * Math.PI * 45
  const offset = circumference - (score / 100) * circumference

  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          Compliance Score
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col sm:flex-row items-center gap-6">
          <div className="relative flex items-center justify-center">
             <svg className="w-32 h-32 transform -rotate-90 text-gray-200 dark:text-gray-700" viewBox="0 0 112 112">
               <circle
                 cx="56"
                 cy="56"
                 r="45"
                 fill="none"
                 stroke="currentColor"
                 strokeWidth="10"
               />
              <circle
                cx="56"
                cy="56"
                r="45"
                fill="none"
                className={getScoreBg(score)}
                strokeWidth="10"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                style={{ transition: 'stroke-dashoffset 0.5s ease-in-out' }}
              />
            </svg>
            <div className="absolute flex flex-col items-center">
              <span className={cn('text-3xl font-bold', getScoreColor(score))}>
                {score}%
              </span>
            </div>
          </div>

          <div className="flex flex-col gap-3 w-full sm:w-auto">
            <div className="flex items-center gap-2">
              {status.icon}
              <span className="font-medium">{status.label}</span>
            </div>

            {totalRules !== undefined && passedRules !== undefined && failedRules !== undefined && (
              <div className="grid grid-cols-3 gap-4 text-center">
                 <div className="p-2 bg-muted/40 rounded-lg">
                   <div className="text-2xl font-bold text-foreground">{totalRules}</div>
                   <div className="text-xs text-muted-foreground">Total Rules</div>
                 </div>
                 <div className="p-2 bg-green-50 dark:bg-green-950/40 rounded-lg">
                   <div className="text-2xl font-bold text-green-600 dark:text-green-400">{passedRules}</div>
                   <div className="text-xs text-green-600 dark:text-green-400">Passed</div>
                 </div>
                 <div className="p-2 bg-red-50 dark:bg-red-950/30 rounded-lg">
                   <div className="text-2xl font-bold text-red-600 dark:text-red-400">{failedRules}</div>
                   <div className="text-xs text-red-600 dark:text-red-400">Failed</div>
                 </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function ComplianceScoreSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="h-5 w-40 bg-border rounded animate-pulse" />
      </CardHeader>
      <CardContent>
        <div className="flex flex-col sm:flex-row items-center gap-6">
          <div className="w-32 h-32 rounded-full bg-border animate-pulse" />
          <div className="flex flex-col gap-3 w-full sm:w-auto">
            <div className="h-5 w-24 bg-border rounded animate-pulse" />
            <div className="grid grid-cols-3 gap-4">
              <div className="h-16 bg-border rounded-lg animate-pulse" />
              <div className="h-16 bg-border rounded-lg animate-pulse" />
              <div className="h-16 bg-border rounded-lg animate-pulse" />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
