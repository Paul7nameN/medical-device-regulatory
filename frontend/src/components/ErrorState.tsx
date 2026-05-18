import { Card, CardContent, Button } from '@/components/ui'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface ErrorStateProps {
  title?: string
  message: string
  onRetry?: () => void
  retryLabel?: string
  className?: string
}

export function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
  retryLabel = 'Try again',
  className,
}: ErrorStateProps) {
  return (
    <Card className={className}>
      <CardContent className="flex flex-col items-center justify-center py-12">
        <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4">
          <AlertTriangle className="h-6 w-6 text-red-600" />
        </div>
        <h3 className="text-base font-medium text-foreground mb-1">{title}</h3>
        <p className="text-sm text-muted-foreground text-center max-w-md mb-4">{message}</p>
        {onRetry && (
          <Button
            variant="default"
            size="sm"
            onClick={onRetry}
            className="touch-target"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            {retryLabel}
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

interface ApiErrorStateProps {
  error: {
    message?: string
    status_code?: number
    detail?: string
  } | null
  onRetry?: () => void
  className?: string
}

export function ApiErrorState({ error, onRetry, className }: ApiErrorStateProps) {
  const message = error?.detail || error?.message || 'Failed to fetch data from API'
  const title = error?.status_code ? `Error ${error.status_code}` : 'Connection Error'

  return (
    <ErrorState
      title={title}
      message={message}
      onRetry={onRetry}
      className={className}
    />
  )
}

interface EmptyStateProps {
  title?: string
  message: string
  icon?: React.ReactNode
  action?: React.ReactNode
  className?: string
}

export function EmptyState({
  title = 'No data available',
  message,
  icon,
  action,
  className,
}: EmptyStateProps) {
  return (
    <Card className={className}>
      <CardContent className="flex flex-col items-center justify-center py-12">
        {icon || (
          <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-4">
            <AlertTriangle className="h-6 w-6 text-slate-400" />
          </div>
        )}
        <h3 className="text-base font-medium text-foreground mb-1">{title}</h3>
        <p className="text-sm text-muted-foreground text-center max-w-md mb-4">{message}</p>
        {action}
      </CardContent>
    </Card>
  )
}

export default ErrorState
