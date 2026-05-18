import { useState, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '@/components/ui'
import { SummaryCard } from '@/components/SummaryCard'
import { FileUploadZone } from '@/components/FileUploadZone'
import { ComplianceScore, ComplianceScoreSkeleton } from '@/components/ComplianceScore'
import {
  TemperatureChart,
  TemperatureChartSkeleton,
} from '@/components/TemperatureChart'
import { ViolationsTable } from '@/components/ViolationsTable'
import { ErrorState } from '@/components/ErrorState'
import { type RegCategory } from '@/lib/api'
import {
  type SeverityCounts,
  findingsToDetectedViolations,
  calculateComplianceScoreFromCounts,
  groupViolationsByCategory,
} from '@/lib/utils/transformers'
import { REGULATORY_CONSTANTS } from '@/lib/constants'
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from '@/components/ui'
import { AIAnalysisSection } from '@/components/AIAnalysis'
import { AIChat } from '@/components/AIChat'
import { RulesList } from '@/components/RulesReference'
import {
  Upload,
  BarChart3,
  Thermometer,
  AlertTriangle,
  History,
  Info,
  FileText,
  Image,
   X,
   Trash2,
   BookOpen,
   Loader2,
 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAnalysis } from '@/lib/context/AnalysisContext'

const safeRange = REGULATORY_CONSTANTS.safeTemperatureRange

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
  const navigate = useNavigate()
  const [selectedCategory, setSelectedCategory] = useState<RegCategory | null>(null)
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

  console.log('🟢 Dashboard: latestAnalysis =', latestAnalysis)
  console.log('🟢 Dashboard: hasData =', hasData)
  console.log('🟢 Dashboard: analysisHistory.length =', analysisHistory.length)
  console.log('🟢 Dashboard: latestAnalysis?.aiAnalysis =', latestAnalysis?.aiAnalysis)
  if (latestAnalysis?.aiAnalysis) {
    console.log('🟢 Dashboard: aiAnalysis.insights =', latestAnalysis.aiAnalysis.insights?.length)
    console.log('🟢 Dashboard: aiAnalysis.risk_level =', latestAnalysis.aiAnalysis.session_risk_overview?.risk_level)
  }

  const handleCategoryClick = (category: RegCategory) => {
    setSelectedCategory((prev) => (prev === category ? null : category))
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

  const filteredViolations = useMemo(() => {
    if (!violations) return []
    if (!selectedCategory) return violations
    return violations.filter((v) =>
      v.reg_code.startsWith(`REG-${selectedCategory}`)
    )
  }, [violations, selectedCategory])

  const temperatureData = useMemo(() => {
    if (!hasData || !latestAnalysis) {
      return null
    }
    return latestAnalysis.temperatureData
  }, [hasData, latestAnalysis])

  const complianceScore = useMemo(() => {
    if (!hasData || !latestAnalysis) {
      return null
    }
    const r = latestAnalysis.validationResult
    return {
      score: calculateComplianceScoreFromCounts(r.passed_count, r.failed_count),
      total: r.passed_count + r.failed_count,
      passed: r.passed_count,
      failed: r.failed_count,
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

  const sourceCounts = useMemo(() => {
    if (!temperatureData) return { logFile: 0, chartImage: 0, unknown: 0 }

    let logFile = 0
    let chartImage = 0
    let unknown = 0

    for (const point of temperatureData) {
      if (point.source === 'log_file') logFile++
      else if (point.source === 'chart_image') chartImage++
      else unknown++
    }

    return { logFile, chartImage, unknown }
  }, [temperatureData])

  const dataSourceBadge = useMemo(() => {
    if (!temperatureData) return null

    const { logFile, chartImage } = sourceCounts
    const hasLog = logFile > 0
    const hasChart = chartImage > 0

    if (hasLog && hasChart) {
      return (
        <Badge variant="outline" className="gap-1.5">
          <FileText className="h-3 w-3" />
          <span>Logs</span>
          <span className="text-muted-foreground">+</span>
          <Image className="h-3 w-3" />
          <span>Images</span>
        </Badge>
      )
    }

    if (hasChart) {
      return (
        <Badge variant="outline" className="gap-1.5">
          <Image className="h-3 w-3" />
          <span>From Chart Images</span>
        </Badge>
      )
    }

    return (
      <Badge variant="outline" className="gap-1.5">
        <FileText className="h-3 w-3" />
        <span>From Device Logs</span>
      </Badge>
    )
  }, [temperatureData, sourceCounts])

  const excursions = useMemo(() => {
    if (!temperatureData) return []
    return temperatureData.filter(
      (d) => d.sensorA < safeRange.min || d.sensorA > safeRange.max
    )
  }, [temperatureData])

  const excursionsB = useMemo(() => {
    if (!temperatureData) return []
    return temperatureData.filter(
      (d) =>
        d.sensorB !== undefined &&
        (d.sensorB < safeRange.min || d.sensorB > safeRange.max)
    )
  }, [temperatureData])

  const avgTempA = useMemo(() => {
    if (!temperatureData || temperatureData.length === 0) return null
    return (
      temperatureData.reduce((sum, d) => sum + d.sensorA, 0) / temperatureData.length
    ).toFixed(1)
  }, [temperatureData])

  const avgTempB = useMemo(() => {
    if (!temperatureData) return null
    const hasB = temperatureData.some((d) => d.sensorB !== undefined)
    if (!hasB) return null
    return (
      temperatureData.reduce(
        (sum, d) => sum + (d.sensorB || d.sensorA),
        0
      ) / temperatureData.length
    ).toFixed(1)
  }, [temperatureData])

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

    // ============================================
    // LAYOUT DUAL: Cand nu avem date, afisam pagina simpla cu Upload
    // ============================================
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

    // ============================================
    // Cand avem date SAU suntem in timpul analizei
    // ============================================
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

   // ============================================
   // Cand avem date, afisam dashboard-ul normal
   // ============================================
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
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="w-full sm:w-auto grid grid-cols-4 sm:inline-flex">
            <TabsTrigger value="overview" className="touch-target">
              <BarChart3 className="h-4 w-4 mr-2 hidden sm:inline" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="temperature" className="touch-target">
              <Thermometer className="h-4 w-4 mr-2 hidden sm:inline" />
              Temperature
            </TabsTrigger>
            <TabsTrigger value="violations" className="touch-target">
              <AlertTriangle className="h-4 w-4 mr-2 hidden sm:inline" />
              Violations
              {criticalCount > 0 && (
                <Badge variant="critical" className="ml-2 hidden sm:inline-flex">
                  {criticalCount}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="rules" className="touch-target">
              <BookOpen className="h-4 w-4 mr-2 hidden sm:inline" />
              Rules
            </TabsTrigger>
          </TabsList>

         <TabsContent value="overview" className="mt-6 space-y-6">
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
        </TabsContent>

         <TabsContent value="temperature" className="mt-6 space-y-6">
           {!temperatureData || temperatureData.length === 0 ? (
             <EmptyStateCard
               icon={Thermometer}
               title="No temperature data available"
               description="Temperature readings will appear here after uploading device log files or chart images."
               actionLabel="Go to Overview"
               onActionClick={() => setActiveTab('overview')}
             />
           ) : (
            <>
              {dataSourceBadge && (
                <div className="flex items-center gap-2">
                  {dataSourceBadge}
                </div>
              )}

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {avgTempA && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <Thermometer className="h-4 w-4 text-primary" />
                        Sensor A (Avg)
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p
                        className={cn(
                          'text-2xl font-bold',
                          Number(avgTempA) >= safeRange.min &&
                            Number(avgTempA) <= safeRange.max
                            ? 'text-green-600 dark:text-green-400'
                            : 'text-red-600 dark:text-red-400'
                        )}
                      >
                        {avgTempA}°C
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {excursions.length > 0 ? (
                          <span className="text-red-600 dark:text-red-400">
                            {excursions.length} excursions detected
                          </span>
                        ) : (
                          <span className="text-green-600 dark:text-green-400">Within safe range</span>
                        )}
                      </p>
                    </CardContent>
                  </Card>
                )}

                {avgTempB !== null && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <Thermometer className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                        Sensor B (Avg)
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p
                        className={cn(
                          'text-2xl font-bold',
                          Number(avgTempB) >= safeRange.min &&
                            Number(avgTempB) <= safeRange.max
                            ? 'text-green-600 dark:text-green-400'
                            : 'text-red-600 dark:text-red-400'
                        )}
                      >
                        {avgTempB}°C
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {excursionsB.length > 0 ? (
                          <span className="text-red-600 dark:text-red-400">
                            {excursionsB.length} excursions detected
                          </span>
                        ) : (
                          <span className="text-green-600 dark:text-green-400">Within safe range</span>
                        )}
                      </p>
                    </CardContent>
                  </Card>
                )}

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Safe Range</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-2xl font-bold text-foreground">
                      {safeRange.min}°C - {safeRange.max}°C
                    </p>
                    <p className="text-xs text-muted-foreground">REG-TEMP requirement</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Status</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-2">
                      {excursions.length === 0 && excursionsB.length === 0 ? (
                        <Badge variant="low">Compliant</Badge>
                      ) : (
                        <Badge variant="critical">
                          {excursions.length + excursionsB.length} Issues
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      From {temperatureData.length} readings
                    </p>
                  </CardContent>
                </Card>
              </div>

              {showLoading ? (
                <TemperatureChartSkeleton />
              ) : (
                <TemperatureChart data={temperatureData} />
              )}

              <Card className="border-border bg-muted/40">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Info className="h-4 w-4 text-muted-foreground" />
                    About Temperature Monitoring
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-muted-foreground">
                    <div>
                      <h4 className="font-medium text-foreground mb-2">
                        REG-TEMP Requirements
                      </h4>
                      <ul className="space-y-1">
                        <li className="flex items-start gap-2">
                          <span className="text-primary mt-0.5">•</span>
                          <span>
                            <strong>REG-TEMP-1:</strong> Temperature must stay within
                            2-8°C range
                          </span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-primary mt-0.5">•</span>
                          <span>
                            <strong>REG-TEMP-2:</strong> Excursions must recover
                            within 30 minutes
                          </span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-primary mt-0.5">•</span>
                          <span>
                            <strong>REG-TEMP-3:</strong> Temperature recovery
                            verification
                          </span>
                        </li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-foreground mb-2">
                        Chart Features
                      </h4>
                      <ul className="space-y-1">
                        <li className="flex items-start gap-2">
                          <span className="text-primary mt-0.5">•</span>
                          <span>
                            <strong>Green band:</strong> Safe temperature range
                            (2-8°C)
                          </span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-primary mt-0.5">•</span>
                          <span>
                            <strong>Red/Orange highlights:</strong> Excursions outside
                            safe range
                          </span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-primary mt-0.5">•</span>
                          <span>
                            <strong>Brush control:</strong> Drag to zoom into specific
                            time ranges
                          </span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-primary mt-0.5">•</span>
                          <span>
                            <strong>Legend toggle:</strong> Click legend items to
                            show/hide sensor data
                          </span>
                        </li>
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
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
                data={filteredViolations}
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
