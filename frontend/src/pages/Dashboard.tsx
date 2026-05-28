import { useState, useMemo, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '@/components/ui'
import { SummaryCard } from '@/components/SummaryCard'
import { FileUploadZone } from '@/components/FileUploadZone'
import { ComplianceScore, ComplianceScoreSkeleton } from '@/components/ComplianceScore'
import { GraphSection } from '@/components/GraphSection'
import { ViolationsTable } from '@/components/ViolationsTable'
import { ErrorState } from '@/components/ErrorState'
import { ExportReportButton } from '@/components/ExportReportButton'
import { 
  type RegCategory, 
  type CorrelationInsight, 
  type ConflictingFinding,
  type TimelineEvent,
  type AggregatedComplianceReport,
} from '@/lib/api'
import {
  type SeverityCounts,
  findingsToDetectedViolations,
  calculateComplianceScoreFromSeverityCounts,
  groupViolationsByCategory,
} from '@/lib/utils/transformers'
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from '@/components/ui'
import { AIAnalysisSection } from '@/components/AIAnalysis'
import { AIChat } from '@/components/AIChat'
import { RulesList } from '@/components/RulesReference'
import { CorrelationInsights, ConflictsSection } from '@/components/MultiModal/CorrelationInsights'
import { UnifiedTimeline } from '@/components/MultiModal/UnifiedTimeline'
import { AlignmentUncertaintyBanner } from '@/components/AlignmentUncertaintyBanner'
import {
  Upload,
  BarChart3,
  LineChart,
  AlertTriangle,
  History,
  FileText,
  X,
  Trash2,
  BookOpen,
  Loader2,
  Clock,
  Info,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAnalysis } from '@/lib/context/AnalysisContext'

interface MultiModalData {
  report?: AggregatedComplianceReport
  correlation_insights?: CorrelationInsight[]
  conflicting_findings?: ConflictingFinding[]
  timeline_events?: TimelineEvent[]
  alignment_uncertain?: boolean
  alignment_confidence?: number
  alignment_method?: string
}

function parseTimestampUTC(timestamp: string): Date {
  const hasTimezone = /Z|[+-]\d{2}:\d{2}$/.test(timestamp)
  if (hasTimezone) {
    return new Date(timestamp)
  }
  return new Date(timestamp + 'Z')
}

function EmptyStateCard({
  icon: Icon,
  title,
  description,
  actionLabel,
  actionTo,
  onActionClick,
}: {
  icon: React.ElementType
  title: string
  description: string
  actionLabel?: string
  actionTo?: string
  onActionClick?: () => void
}) {
  return (
    <Card className="border-dashed border-border/80 bg-muted/20">
      <CardContent className="p-8 text-center">
        <div className="mx-auto w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-4">
          <Icon className="h-6 w-6 text-muted-foreground" />
        </div>
        <h3 className="text-sm font-medium text-foreground mb-1">{title}</h3>
        <p className="text-sm text-muted-foreground mb-4">{description}</p>
        {actionLabel && (
          onActionClick ? (
            <Button onClick={onActionClick} size="sm" className="touch-target">
              <Upload className="h-4 w-4 mr-2" />
              {actionLabel}
            </Button>
          ) : actionTo ? (
            <Link to={actionTo}>
              <Button size="sm" className="touch-target">
                <Upload className="h-4 w-4 mr-2" />
                {actionLabel}
              </Button>
            </Link>
          ) : null
        )}
      </CardContent>
    </Card>
  )
}

interface DashboardPageProps {
  isLoading?: boolean
}

export function DashboardPage({ isLoading = false }: DashboardPageProps) {
  const [activeTab, setActiveTab] = useState('overview')
  const {
    latestAnalysis,
    hasData,
    isAnalyzing,
    error,
    clearError,
    analysisHistory,
    switchAnalysis,
    removeAnalysis,
    clearHistory,
    activeAnalysisIndex,
  } = useAnalysis()

  const [multiModalData, setMultiModalData] = useState<MultiModalData | null>(null)

  useEffect(() => {
    if (!latestAnalysis || !latestAnalysis.validationResult) {
      setMultiModalData(null)
      return
    }

    const vr = latestAnalysis.validationResult as any

    if (!vr.data_sources && !vr.correlation_insights && !vr.alignment_uncertain) {
      setMultiModalData(null)
      return
    }

    let alignmentMethod: string | undefined
    if (vr.data_sources && vr.data_sources.length > 0) {
      const alignedSource = vr.data_sources.find((s: any) => s.alignment)
      if (alignedSource?.alignment?.method) {
        alignmentMethod = alignedSource.alignment.method
      }
    }

    setMultiModalData({
      report: vr,
      correlation_insights: vr.correlation_insights,
      conflicting_findings: vr.conflicting_findings,
      timeline_events: vr.temporal_analysis?.event_timeline,
      alignment_uncertain: vr.alignment_uncertain,
      alignment_confidence: vr.multi_modal_confidence,
      alignment_method: alignmentMethod,
    })
  }, [latestAnalysis])

  const hasMultiModalData = multiModalData && (
    multiModalData.correlation_insights?.length || 
    multiModalData.conflicting_findings?.length ||
    multiModalData.timeline_events?.length ||
    multiModalData.alignment_uncertain
  )

  console.log('🟢 Dashboard: latestAnalysis =', latestAnalysis)
  console.log('🟢 Dashboard: hasData =', hasData)
  console.log('🟢 Dashboard: analysisHistory.length =', analysisHistory.length)
  console.log('🟢 Dashboard: latestAnalysis?.aiAnalysis =', latestAnalysis?.aiAnalysis)
  if (latestAnalysis?.aiAnalysis) {
    console.log('🟢 Dashboard: aiAnalysis.insights =', latestAnalysis.aiAnalysis.insights?.length)
    console.log('🟢 Dashboard: aiAnalysis.risk_level =', latestAnalysis.aiAnalysis.session_risk_overview?.risk_level)
  }

  const showLoading = isLoading || isAnalyzing

  const categoryData = useMemo(() => {
    if (!hasData || !latestAnalysis) {
      return null
    }
    return groupViolationsByCategory(latestAnalysis.validationResult.findings)
  }, [hasData, latestAnalysis])

  const violations = useMemo(() => {
    if (!hasData || !latestAnalysis) {
      return null
    }
    return findingsToDetectedViolations(latestAnalysis.validationResult.findings)
  }, [hasData, latestAnalysis])

  const telemetrySeries = useMemo(() => {
    if (!hasData || !latestAnalysis) {
      return {}
    }
    return latestAnalysis.telemetrySeries ?? {}
  }, [hasData, latestAnalysis])

  const complianceScore = useMemo(() => {
    if (!hasData || !latestAnalysis) {
      return null
    }
    const r = latestAnalysis.validationResult

    const failedFindings = r.findings.filter((f) => !f.passed)
    const failedBySeverity = {
      critical: failedFindings.filter((f) => f.severity === 'critical').length,
      high: failedFindings.filter((f) => f.severity === 'high').length,
      medium: failedFindings.filter((f) => f.severity === 'medium').length,
      low: failedFindings.filter((f) => f.severity === 'low').length,
      info: failedFindings.filter((f) => f.severity === 'info').length,
    }

    return {
      score: calculateComplianceScoreFromSeverityCounts(r.passed_count, failedBySeverity),
      total: r.passed_count + r.failed_count,
      passed: r.passed_count,
      failed: r.failed_count,
      hasCritical: failedBySeverity.critical > 0,
    }
  }, [hasData, latestAnalysis])

  const severityCounts = useMemo(() => {
    if (!hasData || !latestAnalysis) {
      return null
    }
    const failed = latestAnalysis.validationResult.findings.filter((f) => !f.passed)
    return {
      critical: failed.filter((f) => f.severity === 'critical').length,
      high: failed.filter((f) => f.severity === 'high').length,
      medium: failed.filter((f) => f.severity === 'medium').length,
      low: failed.filter((f) => f.severity === 'low').length,
    }
  }, [hasData, latestAnalysis])

  const criticalCount = useMemo(
    () => (violations ? violations.filter((v) => v.severity === 'critical').length : 0),
    [violations]
  )
  const openCount = useMemo(
    () => (violations ? violations.filter((v) => v.status === 'open').length : 0),
    [violations]
  )
  const acknowledgedCount = useMemo(
    () =>
      violations ? violations.filter((v) => v.status === 'acknowledged').length : 0,
    [violations]
  )
  const resolvedCount = useMemo(
    () =>
      violations ? violations.filter((v) => v.status === 'resolved').length : 0,
    [violations]
  )

  const handleLoadAnalysis = (index: number) => {
    switchAnalysis(index)
    setActiveTab('overview')
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground font-heading">
            Analysis Hub
          </h1>
          <p className="text-muted-foreground mt-1">
            MED-THERM compliance overview for your medical devices
          </p>
        </div>
        <ErrorState
          title="Failed to load data"
          message={error}
          onRetry={clearError}
          retryLabel="Clear Error"
        />
      </div>
    )
  }

  if (!hasData && !isAnalyzing) {
    return (
      <div className="flex flex-col items-center">
        <div className="w-full max-w-3xl">
          <div className="text-center mb-2">
            <h2 className="text-lg sm:text-xl font-bold text-foreground font-heading mb-1">
              Upload files to start compliance analysis
            </h2>
            <p className="text-xs sm:text-sm text-muted-foreground">
              Drag and drop device log files (.txt) or chart images (.png, .jpg) below
            </p>
          </div>
          <FileUploadZone
            onUploadComplete={() => {}}
            maxFiles={10}
            maxSize={50 * 1024 * 1024}
          />
        </div>
      </div>
    )
  }

  if (!hasData && isAnalyzing) {
    return (
      <div className="min-h-[40vh] flex flex-col items-center pt-4 sm:pt-8">
        <Card className="w-full max-w-md border-border bg-muted/40">
          <CardContent className="p-12 text-center">
            <Loader2 className="h-16 w-16 mx-auto mb-6 text-primary animate-spin" />
            <h3 className="text-xl font-semibold text-foreground mb-3">
              Analyzing your files...
            </h3>
            <p className="text-base text-muted-foreground">
              Please wait while we process your device logs or chart images.
            </p>
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
            Analysis Hub
          </h1>
          <p className="text-muted-foreground mt-1">
            {latestAnalysis
              ? `Device: ${latestAnalysis.deviceId || 'Unknown'} • ${analysisHistory.length > 1 ? `Analysis ${activeAnalysisIndex + 1} of ${analysisHistory.length}` : 'Single analysis loaded'}`
              : 'MED-THERM compliance overview for your medical devices'}
          </p>
        </div>

        {latestAnalysis && complianceScore && (
          <div className="flex items-center gap-2">
            <ExportReportButton
              analysis={latestAnalysis}
              complianceScore={complianceScore.score}
              severityCounts={severityCounts ?? undefined}
              telemetrySeries={telemetrySeries}
            />
          </div>
        )}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="w-full sm:w-auto flex flex-row overflow-x-auto sm:overflow-visible sm:grid sm:grid-cols-5 gap-1 sm:gap-0 pb-1 sm:pb-0">
          <TabsTrigger value="overview" className="touch-target flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 min-w-16 sm:min-w-0 py-2 sm:py-0">
            <BarChart3 className="h-4 w-4" />
            <span className="text-xs sm:text-sm">Overview</span>
          </TabsTrigger>
          <TabsTrigger value="graphs" className="touch-target flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 min-w-16 sm:min-w-0 py-2 sm:py-0">
            <LineChart className="h-4 w-4" />
            <span className="text-xs sm:text-sm">Graphs</span>
          </TabsTrigger>
          <TabsTrigger value="violations" className="touch-target flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 min-w-16 sm:min-w-0 py-2 sm:py-0 relative">
            <div className="relative">
              <AlertTriangle className="h-4 w-4" />
              {criticalCount > 0 && (
                <span className="absolute -top-2 -right-3 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-medium text-white px-1">
                  {criticalCount > 9 ? '9+' : criticalCount}
                </span>
              )}
            </div>
            <span className="text-xs sm:text-sm">Violations</span>
          </TabsTrigger>
          <TabsTrigger value="timeline" className="touch-target flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 min-w-16 sm:min-w-0 py-2 sm:py-0 relative">
            <div className="relative">
              <Clock className="h-4 w-4" />
              {hasMultiModalData && multiModalData?.timeline_events?.length ? (
                <span className="absolute -top-2 -right-3 flex h-4 min-w-4 items-center justify-center rounded-full bg-blue-500 text-[10px] font-medium text-white px-1">
                  {multiModalData.timeline_events.length > 9 ? '9+' : multiModalData.timeline_events.length}
                </span>
              ) : null}
            </div>
            <span className="text-xs sm:text-sm">Timeline</span>
          </TabsTrigger>
          <TabsTrigger value="rules" className="touch-target flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-2 min-w-16 sm:min-w-0 py-2 sm:py-0">
            <BookOpen className="h-4 w-4" />
            <span className="text-xs sm:text-sm">Rules</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6 space-y-6">
          {multiModalData?.alignment_uncertain && (
            <AlignmentUncertaintyBanner
              alignmentConfidence={multiModalData.alignment_confidence}
              alignmentMethod={multiModalData.alignment_method}
            />
          )}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 flex flex-col">
              {isAnalyzing && !hasData ? (
                <Card className="border-border bg-muted/40 h-full">
                  <CardContent className="p-8 text-center">
                    <Loader2 className="h-12 w-12 mx-auto mb-4 text-primary animate-spin" />
                    <h3 className="text-lg font-semibold text-foreground mb-2">
                      Analyzing your files...
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      Please wait while we process your device logs or chart images.
                    </p>
                  </CardContent>
                </Card>
              ) : showLoading ? (
                <ComplianceScoreSkeleton />
              ) : !complianceScore ? (
                <Card className="border-dashed border-border/80 bg-muted/20 h-full">
                  <CardContent className="p-8">
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold text-foreground mb-2">
                        No compliance data available
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        Upload device log files or chart images to generate a compliance analysis.
                      </p>
                    </div>
                    <FileUploadZone
                      onUploadComplete={() => {}}
                      maxFiles={10}
                      maxSize={50 * 1024 * 1024}
                    />
                  </CardContent>
                </Card>
               ) : (
                 <ComplianceScore
                   score={complianceScore.score}
                   totalRules={complianceScore.total}
                   passedRules={complianceScore.passed}
                   failedRules={complianceScore.failed}
                   hasCritical={complianceScore.hasCritical}
                   className="h-full"
                 />
               )}
            </div>

            <div className="flex flex-col gap-4">
              {showLoading ? (
                <Card className="h-full">
                  <CardContent className="p-6">
                    <div className="h-24 bg-border rounded animate-pulse" />
                  </CardContent>
                </Card>
              ) : !severityCounts ? (
                <Card className="h-full">
                  <CardContent className="p-6">
                    <div className="grid grid-cols-2 gap-4">
                      {['Critical', 'High', 'Medium', 'Low'].map((level) => (
                        <div
                          key={level}
                          className="text-center p-3 bg-muted/40 rounded-lg"
                        >
                          <div className="text-3xl font-bold text-muted-foreground">-</div>
                          <div className="text-xs text-muted-foreground">{level}</div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card className="h-full">
                  <CardContent className="p-6">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center p-3 bg-red-50 dark:bg-red-950/30 rounded-lg">
                        <div className="text-3xl font-bold text-red-600 dark:text-red-400">
                          {severityCounts.critical}
                        </div>
                        <div className="text-xs text-red-700 dark:text-red-400">Critical</div>
                      </div>
                      <div className="text-center p-3 bg-orange-50 dark:bg-orange-950/30 rounded-lg">
                        <div className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                          {severityCounts.high}
                        </div>
                        <div className="text-xs text-orange-700 dark:text-orange-400">High</div>
                      </div>
                      <div className="text-center p-3 bg-yellow-50 dark:bg-yellow-950/30 rounded-lg">
                        <div className="text-3xl font-bold text-yellow-600 dark:text-yellow-400">
                          {severityCounts.medium}
                        </div>
                        <div className="text-xs text-yellow-700 dark:text-yellow-400">Medium</div>
                      </div>
                      <div className="text-center p-3 bg-green-50 dark:bg-green-950/30 rounded-lg">
                        <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                          {severityCounts.low}
                        </div>
                        <div className="text-xs text-green-700 dark:text-green-400">Low</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>

          <div>
            <h2 className="text-lg font-semibold text-foreground font-heading mb-4">
              Compliance by Category
            </h2>
            {!categoryData ? (
              <Card className="border-dashed border-border/80 bg-muted/20">
                <CardContent className="p-6 text-center">
                  <p className="text-sm text-muted-foreground">
                    Upload log files to see category breakdown
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {(Object.entries(categoryData) as [RegCategory, SeverityCounts][]).map(
                  ([category, counts]) => (
                    <SummaryCard
                      key={category}
                      category={category}
                      counts={counts}
                    />
                  )
                )}
              </div>
            )}
          </div>

          {latestAnalysis?.aiAnalysis && (
            <div className="mt-8 pt-6 border-t">
              <AIAnalysisSection aiAnalysis={latestAnalysis.aiAnalysis} />
            </div>
          )}

          {multiModalData?.correlation_insights && multiModalData.correlation_insights.length > 0 && (
            <div className="mt-8 pt-6 border-t">
              <CorrelationInsights insights={multiModalData.correlation_insights} />
            </div>
          )}

          {multiModalData?.conflicting_findings && multiModalData.conflicting_findings.length > 0 && (
            <div className="mt-6">
              <ConflictsSection findings={multiModalData.conflicting_findings} />
            </div>
          )}

          {hasMultiModalData && multiModalData?.timeline_events && multiModalData.timeline_events.length > 0 && (
            <div className="mt-6">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Clock className="h-5 w-5 text-primary" />
                    Timeline Events
                    <Badge variant="outline" className="ml-2">
                      {multiModalData.timeline_events.length} events
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-3">
                    Quick preview of events. Go to the Timeline tab for the full interactive view.
                  </p>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => setActiveTab('timeline')}
                    className="flex items-center gap-1.5"
                  >
                    <Clock className="h-4 w-4" />
                    View Full Timeline
                  </Button>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="graphs" className="mt-6 space-y-6">
          <GraphSection
            telemetrySeries={telemetrySeries}
            isLoading={showLoading}
          />
        </TabsContent>

        <TabsContent value="timeline" className="mt-6 space-y-6">
          {!hasData || !latestAnalysis ? (
            <EmptyStateCard
              icon={Clock}
              title="No timeline data"
              description="Upload log files or chart images to generate a unified event timeline."
              actionLabel="Go to Overview"
              onActionClick={() => setActiveTab('overview')}
            />
          ) : multiModalData?.timeline_events && multiModalData.timeline_events.length > 0 ? (
            <>
              {multiModalData.alignment_uncertain && (
                <AlignmentUncertaintyBanner
                  alignmentConfidence={multiModalData.alignment_confidence}
                  alignmentMethod={multiModalData.alignment_method}
                />
              )}
              <UnifiedTimeline 
                events={multiModalData.timeline_events} 
                title="Unified Event Timeline"
              />
            </>
          ) : (
            <div className="space-y-4">
              <EmptyStateCard
                icon={Clock}
                title="No multi-modal timeline"
                description="This analysis was created using single-file mode. Upload multiple files in Unified Batch mode to generate a correlated timeline with events from both logs and chart images."
                actionLabel="Go to Overview"
                onActionClick={() => setActiveTab('overview')}
              />
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Info className="h-4 w-4 text-muted-foreground" />
                    About Unified Timelines
                  </CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground space-y-2">
                  <p>
                    <strong>Unified Batch mode</strong> (in FileUploadZone) enables:
                  </p>
                  <ul className="list-disc pl-5 space-y-1">
                    <li>Correlating events from multiple log files</li>
                    <li>Time-aligning chart images with log timelines</li>
                    <li>Detecting cross-source conflicts</li>
                    <li>Generating a single unified timeline view</li>
                  </ul>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="violations" className="mt-6 space-y-6">
          {!violations ? (
            <EmptyStateCard
              icon={AlertTriangle}
              title="No violations data"
              description="Upload log files to analyze for compliance violations."
              actionLabel="Go to Overview"
              onActionClick={() => setActiveTab('overview')}
            />
          ) : (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card className="border-red-200 bg-red-50 dark:bg-red-950/30">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-400" />
                      Critical
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold text-red-600 dark:text-red-400">
                      {criticalCount}
                    </p>
                    <p className="text-xs text-red-700 dark:text-red-400">
                      Requires immediate attention
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Open</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">
                      {openCount}
                    </p>
                    <p className="text-xs text-muted-foreground">Awaiting resolution</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">
                      Acknowledged
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold text-yellow-600">
                      {acknowledgedCount}
                    </p>
                    <p className="text-xs text-muted-foreground">In progress</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Resolved</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                      {resolvedCount}
                    </p>
                    <p className="text-xs text-muted-foreground">Completed</p>
                  </CardContent>
                </Card>
              </div>

              <ViolationsTable
                data={violations || []}
                title="All Violations"
              />
            </>
          )}
        </TabsContent>

        <TabsContent value="history" className="mt-6 space-y-6">
          {analysisHistory.length === 0 ? (
            <EmptyStateCard
              icon={History}
              title="No analysis history"
              description="Upload files to create analysis records."
              actionLabel="Go to Overview"
              onActionClick={() => setActiveTab('overview')}
            />
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
                          confirm(`Sigur vrei să ștergi TOATE cele ${analysisHistory.length} analize?\nAceastă acțiune este IREVERSIBILĂ!`)
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
                          total > 0
                            ? Math.round((passed / total) * 100)
                            : 100
                        const isActive = index === activeAnalysisIndex

                        return (
                          <tr
                            key={index}
                            className={cn(
                              'border-b border-slate-100 dark:border-slate-800 transition-colors',
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
                                      ? 'text-yellow-600 dark:text-yellow-400'
                                      : 'text-red-600 dark:text-red-400'
                                )}
                              >
                                {score}%
                              </span>
                            </td>
                            <td className="py-3 px-4">
                              {failed > 0 ? (
                                <Badge variant={failed > 5 ? 'critical' : 'outline'}>
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
        </TabsContent>

        <TabsContent value="rules" className="mt-6">
          <RulesList />
        </TabsContent>
      </Tabs>

      {hasData && latestAnalysis && (
        <AIChat
          analysisSessionId={latestAnalysis.analysisSessionId}
          aiAnalysis={latestAnalysis.aiAnalysis}
          defaultCollapsed={true}
          className="fixed bottom-6 right-6 z-50"
        />
      )}
    </div>
  )
}

export default DashboardPage
