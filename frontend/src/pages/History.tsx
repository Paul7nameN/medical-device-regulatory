import { useNavigate } from 'react-router-dom'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Badge,
  Button,
} from '@/components/ui'
import { History, FileText, X, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAnalysis } from '@/lib/context/AnalysisContext'

function parseTimestampUTC(timestamp: string): Date {
  const hasTimezone = /Z|[+-]\d{2}:\d{2}$/.test(timestamp)
  if (hasTimezone) {
    return new Date(timestamp)
  }
  return new Date(timestamp + 'Z')
}

export function HistoryPage() {
  const navigate = useNavigate()
  const {
    analysisHistory,
    activeAnalysisIndex,
    switchAnalysis,
    removeAnalysis,
    clearHistory,
  } = useAnalysis()

  const handleLoadAnalysis = (index: number) => {
    switchAnalysis(index)
    navigate('/')
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-foreground font-heading">
          Analysis History
        </h1>
        <p className="text-muted-foreground mt-1">
          {analysisHistory.length} analysis{analysisHistory.length !== 1 ? 'es' : ''} stored
        </p>
      </div>

      {analysisHistory.length === 0 ? (
        <Card className="border-dashed border-border/80 bg-muted/20">
          <CardContent className="p-8 text-center">
            <div className="mx-auto w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-4">
              <History className="h-6 w-6 text-muted-foreground" />
            </div>
            <h3 className="text-sm font-medium text-foreground mb-1">
              No analysis history
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              Upload files to create analysis records.
            </p>
            <Button
              onClick={() => navigate('/')}
              size="sm"
              className="touch-target"
            >
              <FileText className="h-4 w-4 mr-2" />
              Go to Home
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                <History className="h-5 w-5 text-primary" />
                Analysis History ({analysisHistory.length} records)
              </CardTitle>
              {analysisHistory.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={async () => {
                    if (
                      confirm(
                        `Sigur vrei să ștergi TOATE cele ${analysisHistory.length} analize?\nAceastă acțiune este IREVERSIBILĂ!`
                      )
                    ) {
                      await clearHistory()
                    }
                  }}
                  className="touch-target"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear All
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border bg-muted/40">
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                      #
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                      Device
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                      Analyzed At
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                      Score
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                      Violations
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                      Status
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {analysisHistory.map((analysis, index) => {
                    const vr = analysis.validationResult
                    const passed = vr.passed_count || 0
                    const failed = vr.failed_count || 0
                    const total = passed + failed
                    const score =
                      total > 0 ? Math.round((passed / total) * 100) : 100
                    const isActive = index === activeAnalysisIndex

                    return (
                      <tr
                        key={index}
                        className={cn(
                          'border-b border-slate-100 transition-colors',
                          isActive ? 'bg-primary/5' : 'hover:bg-muted/40'
                        )}
                      >
                        <td className="py-3 px-4 text-sm">
                          <span className="font-medium">{index + 1}</span>
                        </td>
                        <td className="py-3 px-4 text-sm">
                          <span className="font-mono text-primary">
                            {analysis.deviceId || 'Unknown'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm text-muted-foreground">
                          {parseTimestampUTC(analysis.analyzedAt).toLocaleString()}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={cn(
                              'text-sm font-bold',
                              score >= 90
                                ? 'text-green-600 dark:text-green-400'
                                : score >= 70
                                  ? 'text-yellow-600'
                                  : 'text-red-600 dark:text-red-400'
                            )}
                          >
                            {score}%
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          {failed > 0 ? (
                            <Badge
                              variant={failed > 5 ? 'critical' : 'outline'}
                            >
                              {failed}
                            </Badge>
                          ) : (
                            <Badge variant="low">0</Badge>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          {isActive ? (
                            <Badge variant="low">Active</Badge>
                          ) : (
                            <Badge variant="outline">Stored</Badge>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {!isActive && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleLoadAnalysis(index)}
                                className="h-8 px-2 touch-target"
                              >
                                <FileText className="h-4 w-4 mr-1" />
                                <span className="text-xs">Load</span>
                              </Button>
                            )}
                            {analysisHistory.length > 0 && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={async () => {
                                  if (
                                    confirm(
                                      'Remove this analysis from history?'
                                    )
                                  ) {
                                    await removeAnalysis(index)
                                  }
                                }}
                                className="h-8 px-2 touch-target text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-400 dark:text-red-400 hover:bg-red-50 dark:bg-red-950/30 dark:hover:bg-red-950/50"
                              >
                                <X className="h-4 w-4" />
                                <span className="sr-only">Remove</span>
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default HistoryPage
