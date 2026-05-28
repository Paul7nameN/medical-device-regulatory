import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle, Badge } from '@/components/ui'
import { CheckCircle, AlertTriangle, XCircle, TrendingUp } from 'lucide-react'
import {
  getComplianceStatus,
  getComplianceStatusLabel,
  getComplianceStatusColor,
  getComplianceStatusBg,
  type ComplianceStatus,
} from '@/lib/utils/transformers'

interface ComplianceScoreProps {
  score: number
  totalRules?: number
  passedRules?: number
  failedRules?: number
  hasCritical?: boolean
  className?: string
  disclaimer?: string
}

function getScoreColor(score: number): string {
  if (score >= 85) return 'text-green-600 dark:text-green-400'
  if (score >= 70) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-red-600 dark:text-red-400'
}

function getScoreBg(score: number): string {
  if (score >= 85) return 'stroke-green-500 dark:stroke-green-400'
  if (score >= 70) return 'stroke-yellow-500 dark:stroke-yellow-400'
  return 'stroke-red-500 dark:stroke-red-400'
}

function getStatusIcon(status: ComplianceStatus): React.ReactNode {
  switch (status) {
    case 'CONFORM':
      return <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
    case 'CONFORM_WITH_RESERVE':
      return <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
    case 'NON_CONFORM':
      return <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
  }
}

export function ComplianceScore({
  score,
  totalRules,
  passedRules,
  failedRules,
  hasCritical = false,
  className,
  disclaimer,
}: ComplianceScoreProps) {
  const effectiveScore = hasCritical ? 0 : score
  const status = getComplianceStatus(effectiveScore, hasCritical)
  const circumference = 2 * Math.PI * 45
  const offset = circumference - (effectiveScore / 100) * circumference

  const defaultDisclaimer =
    'Per GDP / ISO 13485 standards: 1 CRITICAL violation = NON-CONFORM. Score is indicative and based on MED-THERM-2026 regulatory constraints.'

  const finalDisclaimer = disclaimer ?? defaultDisclaimer

  return (
    <Card
      className={cn(
        'overflow-hidden flex flex-col border',
        getComplianceStatusBg(status),
        className
      )}
    >
      <CardHeader className="pb-2 flex-shrink-0">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            Compliance Score
          </CardTitle>
          <Badge
            variant="outline"
            className={cn(
              'font-semibold',
              getComplianceStatusColor(status).replace('text-', 'border-')
            )}
          >
            <span className={getComplianceStatusColor(status)}>
              {getComplianceStatusLabel(status)}
            </span>
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        <div className="flex flex-col sm:flex-row items-center gap-6 flex-1">
          <div className="relative flex items-center justify-center">
            <svg
              className="w-32 h-32 transform -rotate-90 text-gray-200 dark:text-gray-700"
              viewBox="0 0 112 112"
            >
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
                className={getScoreBg(effectiveScore)}
                strokeWidth="10"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                style={{ transition: 'stroke-dashoffset 0.5s ease-in-out' }}
              />
            </svg>
            <div className="absolute flex flex-col items-center">
              <span className={cn('text-3xl font-bold', getScoreColor(effectiveScore))}>
                {effectiveScore}%
              </span>
            </div>
          </div>

          <div className="flex flex-col gap-3 w-full sm:w-auto">
            <div className="flex items-center gap-2">
              {getStatusIcon(status)}
              <span className={cn('font-medium', getComplianceStatusColor(status))}>
                {getComplianceStatusLabel(status)}
              </span>
              {hasCritical && (
                <Badge variant="destructive" className="ml-2">
                  CRITICAL VIOLATIONS
                </Badge>
              )}
            </div>

            <div className="text-xs text-muted-foreground">
              Per GDP standards: ≥85% = CONFORM, 70-84% = CONFORM WITH RESERVE, {'<'}70% or
              any CRITICAL = NON-CONFORM
            </div>

            {totalRules !== undefined &&
              passedRules !== undefined &&
              failedRules !== undefined && (
                <div className="grid grid-cols-3 gap-4 text-center mt-2">
                  <div className="p-2 bg-muted/40 rounded-lg">
                    <div className="text-2xl font-bold text-foreground">{totalRules}</div>
                    <div className="text-xs text-muted-foreground">Total Rules</div>
                  </div>
                  <div className="p-2 bg-green-50 dark:bg-green-950/40 rounded-lg">
                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {passedRules}
                    </div>
                    <div className="text-xs text-green-600 dark:text-green-400">Passed</div>
                  </div>
                  <div className="p-2 bg-red-50 dark:bg-red-950/30 rounded-lg">
                    <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                      {failedRules}
                    </div>
                    <div className="text-xs text-red-600 dark:text-red-400">Failed</div>
                  </div>
                </div>
              )}
          </div>
        </div>

        {finalDisclaimer && (
          <p className="text-xs text-muted-foreground mt-4 pt-4 border-t border-border flex-shrink-0">
            {finalDisclaimer}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

export function ComplianceScoreSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="h-5 w-40 bg-border rounded animate-pulse" />
          <div className="h-6 w-28 bg-border rounded animate-pulse" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col sm:flex-row items-center gap-6">
          <div className="w-32 h-32 rounded-full bg-border animate-pulse" />
          <div className="flex flex-col gap-3 w-full sm:w-auto">
            <div className="h-5 w-36 bg-border rounded animate-pulse" />
            <div className="h-10 w-full bg-border rounded animate-pulse" />
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
