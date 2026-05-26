import { AlertTriangle, Info, X } from 'lucide-react'
import { Button, Badge } from '@/components/ui'
import { useState } from 'react'
import { cn } from '@/lib/utils'

interface AlignmentUncertaintyBannerProps {
  alignmentConfidence?: number
  alignmentMethod?: string
  onDismiss?: () => void
  className?: string
}

export function AlignmentUncertaintyBanner({
  alignmentConfidence,
  alignmentMethod,
  onDismiss,
  className,
}: AlignmentUncertaintyBannerProps) {
  const [isVisible, setIsVisible] = useState(true)

  const handleDismiss = () => {
    setIsVisible(false)
    onDismiss?.()
  }

  if (!isVisible) return null

  const confidencePercent = alignmentConfidence !== undefined 
    ? Math.round(alignmentConfidence * 100) 
    : null

  const isLowConfidence = confidencePercent !== null && confidencePercent < 70

  return (
    <div className={cn(
      'border rounded-lg',
      isLowConfidence 
        ? 'bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-900' 
        : 'bg-yellow-50 dark:bg-yellow-950/30 border-yellow-200 dark:border-yellow-900',
      className
    )}>
      <div className="p-3 sm:p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className={cn(
              'p-2 rounded-lg flex-shrink-0 mt-0.5',
              isLowConfidence 
                ? 'bg-amber-100 dark:bg-amber-900/50' 
                : 'bg-yellow-100 dark:bg-yellow-900/50'
            )}>
              <AlertTriangle className={cn(
                'h-5 w-5',
                isLowConfidence 
                  ? 'text-amber-600 dark:text-amber-400' 
                  : 'text-yellow-600 dark:text-yellow-400'
              )} />
            </div>
            <div className="flex-1 min-w-0">
              <h4 className={cn(
                'text-sm font-medium flex items-center gap-2',
                isLowConfidence
                  ? 'text-amber-800 dark:text-amber-200'
                  : 'text-yellow-800 dark:text-yellow-200'
              )}>
                Chart Time Alignment Uncertain
                {confidencePercent !== null && (
                  <Badge variant="outline" className={cn(
                    'ml-1 text-xs',
                    isLowConfidence 
                      ? 'bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300 border-amber-300 dark:border-amber-700' 
                      : 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-700 dark:text-yellow-300 border-yellow-300 dark:border-yellow-700'
                  )}>
                    {confidencePercent}% confidence
                  </Badge>
                )}
              </h4>
              <p className={cn(
                'text-xs sm:text-sm mt-1',
                isLowConfidence
                  ? 'text-amber-700 dark:text-amber-300'
                  : 'text-yellow-700 dark:text-yellow-300'
              )}>
                Chart images were analyzed, but the time range alignment could not be confirmed with high confidence.
                Correlated findings and timeline events may be less accurate.
              </p>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {alignmentMethod && (
                  <div className="flex items-center gap-1">
                    <Info className={cn(
                      'h-3.5 w-3.5',
                      isLowConfidence 
                        ? 'text-amber-600 dark:text-amber-400' 
                        : 'text-yellow-600 dark:text-yellow-400'
                    )} />
                    <span className={cn(
                      'text-xs',
                      isLowConfidence
                        ? 'text-amber-600 dark:text-amber-400'
                        : 'text-yellow-600 dark:text-yellow-400'
                    )}>
                      Alignment method: <span className="font-medium">{alignmentMethod}</span>
                    </span>
                  </div>
                )}
              </div>
              <div className={cn(
                'mt-3 text-xs flex items-start gap-1.5 p-2 rounded',
                isLowConfidence
                  ? 'bg-amber-100/50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300'
                  : 'bg-yellow-100/50 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
              )}>
                <Info className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" />
                <span>
                  <strong>Recommended:</strong> Verify correlated findings manually. 
                  Log-based violations remain accurate and should be trusted as ground truth.
                </span>
              </div>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDismiss}
            className={cn(
              'h-7 w-7 p-0 rounded-full',
              isLowConfidence
                ? 'text-amber-600 dark:text-amber-400 hover:text-amber-700 hover:bg-amber-100 dark:hover:bg-amber-900/50'
                : 'text-yellow-600 dark:text-yellow-400 hover:text-yellow-700 hover:bg-yellow-100 dark:hover:bg-yellow-900/50'
            )}
          >
            <X className="h-4 w-4" />
            <span className="sr-only">Dismiss</span>
          </Button>
        </div>
      </div>
    </div>
  )
}

export function SimpleAlignmentBanner({
  isUncertain,
  confidence,
  className,
}: {
  isUncertain?: boolean
  confidence?: number
  className?: string
}) {
  if (!isUncertain) return null

  return (
    <div className={cn(
      'bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 rounded-lg p-3',
      className
    )}>
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 flex-shrink-0" />
        <span className="text-sm text-amber-800 dark:text-amber-200">
          Chart alignment uncertain
          {confidence !== undefined && (
            <span className="text-amber-600 dark:text-amber-400 ml-1">
              ({Math.round(confidence * 100)}% confidence)
            </span>
          )}
        </span>
      </div>
    </div>
  )
}

export default AlignmentUncertaintyBanner
