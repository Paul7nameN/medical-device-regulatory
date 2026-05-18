import { useAnalysis } from '@/lib/context/AnalysisContext'
import { Shield, Upload, X, Activity } from 'lucide-react'
import { Button } from '@/components/ui'
import { Link } from 'react-router-dom'
import { useState } from 'react'

export function DataModeBanner() {
  const { hasData, latestAnalysis, clearAnalysis } = useAnalysis()
  const [isClearing, setIsClearing] = useState(false)

  const handleClear = () => {
    setIsClearing(true)
    clearAnalysis()
    setTimeout(() => setIsClearing(false), 500)
  }

  if (!hasData) {
    return (
      <div className="bg-muted/40 border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
               <Activity className="h-5 w-5 text-muted-foreground flex-shrink-0" />
               <div>
                 <p className="text-sm font-medium text-foreground">
                   No Analysis Data
                 </p>
                 <p className="text-xs text-muted-foreground">
                   Upload device log files to begin compliance analysis
                 </p>
               </div>
            </div>
            <Link
              to="/upload"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-primary bg-primary/10 hover:bg-primary/15 px-3 py-1.5 rounded-md transition-colors touch-target"
            >
              <Upload className="h-3.5 w-3.5" />
              Upload Logs
            </Link>
          </div>
        </div>
      </div>
    )
  }

  const result = latestAnalysis?.validationResult
  const passed = result?.passed_count || 0
  const failed = result?.failed_count || 0
  const total = passed + failed
  const entries = result?.total_entries || 0
  const deviceId = latestAnalysis?.deviceId || 'unknown'

   return (
     <div className="bg-emerald-50 dark:bg-emerald-950/30 border-b border-emerald-200 dark:border-emerald-900">
       <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
         <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
           <div className="flex items-center gap-2">
             <Shield className="h-5 w-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
             <div>
               <p className="text-sm font-medium text-emerald-800 dark:text-emerald-200">
                 Live Analysis
               </p>
               <p className="text-xs text-emerald-600 dark:text-emerald-400">
                 Device: <span className="font-mono">{deviceId}</span>
                 <span className="mx-1.5">•</span>
                 {entries} log entries
                 <span className="mx-1.5">•</span>
                 <span className="text-emerald-700 dark:text-emerald-300">{passed} passed</span>
                 <span className="mx-1">/</span>
                 <span className={failed > 0 ? 'text-red-600 dark:text-red-400' : 'text-muted-foreground'}>{failed} failed</span>
               </p>
             </div>
           </div>
           <Button
             variant="ghost"
             size="sm"
             onClick={handleClear}
             disabled={isClearing}
             className="text-emerald-700 dark:text-emerald-300 hover:text-emerald-900 dark:hover:text-emerald-100 hover:bg-emerald-100 dark:hover:bg-emerald-900/40 touch-target h-8 px-2.5"
           >
             <X className="h-3.5 w-3.5 mr-1.5" />
             Clear
           </Button>
         </div>
       </div>
     </div>
   )
}

export default DataModeBanner
