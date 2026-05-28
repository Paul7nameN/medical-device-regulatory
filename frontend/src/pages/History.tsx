import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Badge,
  Button,
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
  Skeleton,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui'
import { History, FileText, Trash2, AlertTriangle, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'
import { calculateComplianceScoreFromSeverityCounts } from '@/lib/utils/transformers'
import { useAnalysis } from '@/lib/context/AnalysisContext'

function parseTimestampUTC(timestamp: string): Date {
  const hasTimezone = /Z|[+-]\d{2}:\d{2}$/.test(timestamp)
  if (hasTimezone) {
    return new Date(timestamp)
  }
   return new Date(timestamp + 'Z')
}

function getCorrectComplianceScore(validationResult: any): number {
  if (!validationResult?.findings || !Array.isArray(validationResult.findings)) {
    const passed = validationResult?.passed_count || 0
    const failed = validationResult?.failed_count || 0
    const total = passed + failed
    return total > 0 ? Math.round((passed / total) * 100) : 100
  }

  const failedFindings = validationResult.findings.filter((f: any) => !f.passed)
  const failedBySeverity = {
    critical: failedFindings.filter((f: any) => f.severity === 'critical').length,
    high: failedFindings.filter((f: any) => f.severity === 'high').length,
    medium: failedFindings.filter((f: any) => f.severity === 'medium').length,
    low: failedFindings.filter((f: any) => f.severity === 'low').length,
    info: failedFindings.filter((f: any) => f.severity === 'info').length,
  }

  return calculateComplianceScoreFromSeverityCounts(
    validationResult.passed_count || 0,
    failedBySeverity
  )
}

function AnalysisCard({
  analysis,
  index,
  isActive,
  onLoad,
  onDelete,
}: {
  analysis: any
  index: number
  isActive: boolean
  onLoad: () => void
  onDelete: () => void
}) {
  const vr = analysis.validationResult
  const score = getCorrectComplianceScore(vr)
  const failed = vr.failed_count || 0

  return (
    <Card
      className={cn(
        'overflow-hidden transition-colors',
        isActive && 'ring-2 ring-primary ring-offset-2 dark:ring-offset-0'
      )}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4 mb-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs text-muted-foreground">#{index + 1}</span>
              {isActive && <Badge variant="low">Active</Badge>}
            </div>
            <div className="font-mono text-primary text-sm truncate">
              {analysis.deviceId || 'Unknown'}
            </div>
          </div>
          <span
            className={cn(
              'text-lg font-bold flex-shrink-0',
              score >= 90
                ? 'text-green-600 dark:text-green-400'
                : score >= 70
                  ? 'text-yellow-600 dark:text-yellow-400'
                  : 'text-red-600 dark:text-red-400'
            )}
          >
            {score}%
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
          <Clock className="h-3.5 w-3.5" />
          <span>{parseTimestampUTC(analysis.analyzedAt).toLocaleString()}</span>
        </div>

        <div className="flex items-center justify-between gap-2">
          <Badge variant={failed > 5 ? 'critical' : failed > 0 ? 'outline' : 'low'}>
            {failed} violation{failed !== 1 ? 's' : ''}
          </Badge>

          <div className="flex items-center gap-1">
            {!isActive && (
              <Button variant="ghost" size="sm" onClick={onLoad} className="h-8 px-2 touch-target">
                <FileText className="h-4 w-4 mr-1" />
                <span className="text-xs">Load</span>
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={onDelete}
              className="h-8 px-2 touch-target text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-400 hover:bg-red-50 dark:bg-red-950/30 dark:hover:bg-red-950/50"
            >
              <Trash2 className="h-4 w-4" />
              <span className="sr-only">Remove</span>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function HistoryPage() {
  const navigate = useNavigate()
  const {
    analysisHistory,
    activeAnalysisIndex,
    isLoadingHistory,
    switchAnalysis,
    removeAnalysis,
    clearHistory,
  } = useAnalysis()

  const [deleteIndex, setDeleteIndex] = useState<number | null>(null)
  const [showClearAllDialog, setShowClearAllDialog] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const handleLoadAnalysis = (index: number) => {
    switchAnalysis(index)
    navigate('/')
  }

  const handleDeleteSingle = async () => {
    if (deleteIndex === null) return
    setIsDeleting(true)
    try {
      await removeAnalysis(deleteIndex)
    } finally {
      setIsDeleting(false)
      setDeleteIndex(null)
    }
  }

  const handleClearAll = async () => {
    setIsDeleting(true)
    try {
      await clearHistory()
    } finally {
      setIsDeleting(false)
      setShowClearAllDialog(false)
    }
  }

  if (isLoadingHistory) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-9 w-48 mb-2" />
          <Skeleton className="h-5 w-64" />
        </div>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <Skeleton className="h-5 w-44" />
              <Skeleton className="h-9 w-28" />
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/40 hover:bg-muted/40">
                  <TableHead className="w-16"><Skeleton className="h-4 w-6" /></TableHead>
                  <TableHead><Skeleton className="h-4 w-20" /></TableHead>
                  <TableHead><Skeleton className="h-4 w-24" /></TableHead>
                  <TableHead><Skeleton className="h-4 w-12" /></TableHead>
                  <TableHead><Skeleton className="h-4 w-16" /></TableHead>
                  <TableHead><Skeleton className="h-4 w-14" /></TableHead>
                  <TableHead className="text-right"><Skeleton className="h-4 w-16 ml-auto" /></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {[0, 1, 2].map((i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton className="h-5 w-6" /></TableCell>
                    <TableCell><Skeleton className="h-5 w-32" /></TableCell>
                    <TableCell><Skeleton className="h-5 w-36" /></TableCell>
                    <TableCell><Skeleton className="h-5 w-10" /></TableCell>
                    <TableCell><Skeleton className="h-5 w-16" /></TableCell>
                    <TableCell><Skeleton className="h-5 w-14" /></TableCell>
                    <TableCell className="text-right"><Skeleton className="h-8 w-20 ml-auto" /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground font-heading">
            Analysis History
          </h1>
          <p className="text-muted-foreground mt-1">
            {analysisHistory.length} analysis{analysisHistory.length !== 1 ? 'es' : ''} stored
          </p>
        </div>
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
        <>
          <div className="hidden sm:block">
            <Card>
              <CardHeader className="pb-3">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <CardTitle className="text-base font-medium flex items-center gap-2">
                    <History className="h-5 w-5 text-primary" />
                    Analysis History ({analysisHistory.length} records)
                  </CardTitle>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowClearAllDialog(true)}
                    className="touch-target"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Clear All
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-muted/40 hover:bg-muted/40">
                        <TableHead className="w-16">#</TableHead>
                        <TableHead>Device</TableHead>
                        <TableHead>Analyzed At</TableHead>
                        <TableHead>Score</TableHead>
                        <TableHead>Violations</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                      <TableBody>
                        {analysisHistory.map((analysis, index) => {
                          const vr = analysis.validationResult
                          const score = getCorrectComplianceScore(vr)
                          const failed = vr.failed_count || 0
                          const isActive = index === activeAnalysisIndex

                        return (
                          <TableRow
                            key={index}
                            data-state={isActive ? 'active' : undefined}
                            className={cn(isActive && 'bg-primary/5')}
                          >
                            <TableCell className="py-3">
                              <span className="font-medium">{index + 1}</span>
                            </TableCell>
                            <TableCell className="py-3">
                              <span className="font-mono text-primary">
                                {analysis.deviceId || 'Unknown'}
                              </span>
                            </TableCell>
                            <TableCell className="py-3 text-muted-foreground text-sm">
                              {parseTimestampUTC(analysis.analyzedAt).toLocaleString()}
                            </TableCell>
                            <TableCell className="py-3">
                              <span
                                className={cn(
                                  'text-sm font-bold',
                                  score >= 90
                                    ? 'text-green-600 dark:text-green-400'
                                    : score >= 70
                                      ? 'text-yellow-600 dark:text-yellow-400'
                                      : 'text-red-600 dark:text-red-400'
                                )}
                              >
                                {score}%
                              </span>
                            </TableCell>
                            <TableCell className="py-3">
                              {failed > 0 ? (
                                <Badge
                                  variant={failed > 5 ? 'critical' : 'outline'}
                                >
                                  {failed}
                                </Badge>
                              ) : (
                                <Badge variant="low">0</Badge>
                              )}
                            </TableCell>
                            <TableCell className="py-3">
                              {isActive ? (
                                <Badge variant="low">Active</Badge>
                              ) : (
                                <Badge variant="outline">Stored</Badge>
                              )}
                            </TableCell>
                            <TableCell className="py-3 text-right">
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
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => setDeleteIndex(index)}
                                  className="h-8 px-2 touch-target text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-400 hover:bg-red-50 dark:bg-red-950/30 dark:hover:bg-red-950/50"
                                >
                                  <Trash2 className="h-4 w-4" />
                                  <span className="sr-only">Remove</span>
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        )
                      })}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="sm:hidden grid grid-cols-1 gap-3">
            <div className="flex items-center justify-between">
              <Badge variant="secondary">{analysisHistory.length} records</Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowClearAllDialog(true)}
                className="touch-target h-8 text-xs"
              >
                <Trash2 className="h-3.5 w-3.5 mr-1" />
                Clear All
              </Button>
            </div>

            {analysisHistory.map((analysis, index) => (
              <AnalysisCard
                key={index}
                analysis={analysis}
                index={index}
                isActive={index === activeAnalysisIndex}
                onLoad={() => handleLoadAnalysis(index)}
                onDelete={() => setDeleteIndex(index)}
              />
            ))}
          </div>
        </>
      )}

      <Dialog open={deleteIndex !== null} onOpenChange={(open) => !open && !isDeleting && setDeleteIndex(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              Delete analysis
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to remove this analysis from history?
              <br />
              <span className="text-red-600 dark:text-red-400 font-medium">
                This action cannot be undone.
              </span>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button
              variant="ghost"
              onClick={() => setDeleteIndex(null)}
              disabled={isDeleting}
              className="touch-target"
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteSingle}
              disabled={isDeleting}
              className="touch-target"
            >
              {isDeleting ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showClearAllDialog} onOpenChange={(open) => !open && !isDeleting && setShowClearAllDialog(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              Clear all history
            </DialogTitle>
            <DialogDescription>
              This will permanently delete <strong>all {analysisHistory.length} analysis record{analysisHistory.length !== 1 ? 's' : ''}</strong>.
              <br />
              <span className="text-red-600 dark:text-red-400 font-medium">
                Această acțiune este IREVERSIBILĂ!
              </span>
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button
              variant="ghost"
              onClick={() => setShowClearAllDialog(false)}
              disabled={isDeleting}
              className="touch-target"
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleClearAll}
              disabled={isDeleting}
              className="touch-target"
            >
              {isDeleting ? 'Deleting...' : 'Delete All'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default HistoryPage
