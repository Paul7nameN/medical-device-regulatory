import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FileUploadZone } from '@/components/FileUploadZone'
import { Card, CardContent, CardHeader, CardTitle, Badge } from '@/components/ui'
import { FileText, Image, CheckCircle2, Info } from 'lucide-react'
import { useAnalysis } from '@/lib/context/AnalysisContext'

interface AnalysisResultCounts {
  passed: number
  failed: number
  critical: number
  hasData: boolean
}

function extractResultCounts(result: unknown): AnalysisResultCounts {
  const defaultCounts = { passed: 0, failed: 0, critical: 0, hasData: false }

  if (!result || typeof result !== 'object') {
    return defaultCounts
  }

  const obj = result as Record<string, unknown>

  if ('report' in obj && obj.report && typeof obj.report === 'object') {
    const report = obj.report as Record<string, unknown>
    const passed = typeof report.passed_count === 'number' ? report.passed_count : 0
    const failed = typeof report.failed_count === 'number' ? report.failed_count : 0
    const critical = typeof report.critical_count === 'number' ? report.critical_count : 0
    return { passed, failed, critical, hasData: passed + failed > 0 }
  }

  if ('success' in obj && typeof obj.success === 'boolean') {
    if (obj.success && 'result' in obj && obj.result && typeof obj.result === 'object') {
      const chartResult = obj.result as Record<string, unknown>
      if ('violations' in chartResult && Array.isArray(chartResult.violations)) {
        const violations = chartResult.violations
        const failed = violations.length
        const critical = violations.filter((v: unknown) => {
          if (v && typeof v === 'object') {
            const violation = v as Record<string, unknown>
            const conf = typeof violation.confidence === 'number' ? violation.confidence : 0.5
            return conf > 0.8
          }
          return false
        }).length
        return { passed: 0, failed, critical, hasData: failed > 0 }
      }
    }
  }

  if ('findings' in obj && Array.isArray(obj.findings)) {
    const findings = obj.findings as Array<Record<string, unknown>>
    const passed = findings.filter((f) => f.passed === true).length
    const failed = findings.filter((f) => f.passed === false).length
    const critical = findings.filter((f) => f.severity === 'critical').length
    return { passed, failed, critical, hasData: passed + failed > 0 }
  }

  return defaultCounts
}

export function UploadPage() {
  const [uploadResult, setUploadResult] = useState<unknown>(null)
  const [showResult, setShowResult] = useState(false)
  const navigate = useNavigate()

  const { analysisHistory, hasData } = useAnalysis()

  const handleUploadComplete = (result: unknown) => {
    setUploadResult(result)
    setShowResult(true)
  }

  useEffect(() => {
    if (hasData && showResult) {
      const timer = setTimeout(() => {
        navigate('/')
      }, 3000)
      return () => clearTimeout(timer)
    }
  }, [hasData, showResult, navigate])

  const resultCounts = extractResultCounts(uploadResult)

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-foreground font-heading">
          Upload Files
        </h1>
        <p className="text-muted-foreground mt-1">
          Upload log files, images, or documents for MED-THERM compliance analysis
        </p>
      </div>

       {analysisHistory.length > 0 && (
         <Card className="border-border bg-muted/40/50">
           <CardContent className="p-4">
             <Link to="/" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary">
               <FileText className="h-4 w-4" />
               <span>{analysisHistory.length} analysis{analysisHistory.length !== 1 ? 'es' : ''} stored in history</span>
               <span className="text-primary ml-auto">View Analysis →</span>
             </Link>
           </CardContent>
         </Card>
       )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-slate-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              Log Files (.txt)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Raw device logs, temperature telemetry, and system events.
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Image className="h-4 w-4 text-muted-foreground" />
              Images (.png, .jpg)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Temperature chart screenshots, gauge photos, and visual evidence.
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              Documents (.pdf)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Compliance reports, device manuals, and documentation.
            </p>
          </CardContent>
        </Card>
      </div>

      <FileUploadZone
        onUploadComplete={handleUploadComplete}
        maxFiles={10}
        maxSize={50 * 1024 * 1024}
      />

      {showResult && uploadResult && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
              Analysis Complete
            </CardTitle>
          </CardHeader>
          <CardContent>
           <p className="text-sm text-green-700 mb-3">
               Your files have been analyzed successfully. You will be redirected to the
               <Link to="/" className="font-medium text-primary hover:underline mx-1">Home</Link>
               page shortly...
             </p>
            {resultCounts.hasData && (
              <div className="flex flex-wrap gap-2">
                {resultCounts.passed > 0 && (
                  <Badge variant="low">{resultCounts.passed} Rules Passed</Badge>
                )}
                {resultCounts.failed > 0 && (
                  <Badge variant="critical">{resultCounts.failed} Violations Detected</Badge>
                )}
                {resultCounts.critical > 0 && (
                  <Badge variant="outline">{resultCounts.critical} Critical Issues</Badge>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card className="border-border bg-muted/40">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Info className="h-4 w-4 text-muted-foreground" />
            Tips for Best Results
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="text-sm text-muted-foreground space-y-2">
            <li className="flex items-start gap-2">
              <span className="text-primary mt-0.5">•</span>
              <span>
                Include complete log files with timestamps for accurate temporal
                analysis
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-0.5">•</span>
              <span>
                For temperature charts, ensure the Y-axis is clearly labeled with
                temperature values
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-0.5">•</span>
              <span>
                Multiple files from the same device session can be uploaded together
                for consolidated analysis
              </span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}

export default UploadPage
