import { useState, useRef, useCallback, useMemo, useEffect } from 'react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Progress,
  Badge,
} from '@/components/ui'
import { Upload, FileText, Image, File, X, CheckCircle2, AlertCircle, Loader2, FileCode, FileCheck, Layers } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { UploadFileItem, ValidationResult, ExtractedRule } from '@/lib/api'
import { logsApi, aiApi, reportsApi, multimodalApi, type RulesetMetaInput, type MultiModalAnalyzeResponse, type MultiModalStatusResponse } from '@/lib/api'
import { useAnalysis } from '@/lib/context/AnalysisContext'
import { 
  chartViolationsToFindings, 
  extractTemperatureFromChartResult,
  type TemperatureDataPoint 
} from '@/lib/utils/transformers'

export type FileIntent = 'log_file' | 'constraints_document' | 'image' | 'unknown'

const FILE_INTENT_LABELS: Record<FileIntent, string> = {
  log_file: 'Device Logs',
  constraints_document: 'Regulatory Constraints',
  image: 'Chart Image',
  unknown: 'Unknown',
}

const FILE_INTENT_COLORS: Record<FileIntent, string> = {
  log_file: 'bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-400',
  constraints_document: 'bg-purple-100 text-purple-700 border-purple-200 dark:bg-purple-950/40 dark:text-purple-400',
  image: 'bg-green-100 text-green-700 border-green-200 dark:bg-green-950/40 dark:text-green-400',
  unknown: 'bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-800/40 dark:text-gray-400',
}

function detectFileIntent(file: File, textPreview?: string): FileIntent {
  const name = file.name.toLowerCase()
  
  if (file.type.startsWith('image/') || name.endsWith('.png') || name.endsWith('.jpg') || name.endsWith('.jpeg')) {
    return 'image'
  }
  
  if (name.includes('constraint') || name.includes('regulation') || name.includes('rule') || name.includes('reg-')) {
    return 'constraints_document'
  }
  
  if (textPreview) {
    const preview = textPreview.substring(0, 5000)
    
    if (preview.includes('REG-') || preview.includes('REG-TEMP') || preview.includes('REG-SENS') || preview.includes('REG-ALARM')) {
      return 'constraints_document'
    }
    
    if (preview.includes('TEMP_READING') || preview.includes('DOOR_OPEN') || preview.includes('ALARM_TRIGGERED') || preview.includes('SENSOR_TIMEOUT')) {
      return 'log_file'
    }
    
    const timestampPattern = /\d{4}[-/]\d{2}[-/]\d{2}[ T]\d{2}:\d{2}/
    if (timestampPattern.test(preview)) {
      return 'log_file'
    }
  }
  
   if (name.endsWith('.txt') || name.endsWith('.log')) {
     return 'log_file'
   }
   
   if (name.endsWith('.md')) {
     return 'constraints_document'
   }
   
   return 'unknown'
 }

interface FileItemWithIntent extends UploadFileItem {
  intent: FileIntent
  userOverride?: FileIntent
  textPreview?: string
}

interface ExtractedRulesState {
  rules: ExtractedRule[]
  meta: RulesetMetaInput
  sourceFileId: string
}

interface MultiFileUploadState {
  logFiles: FileItemWithIntent[]
  constraintsFiles: FileItemWithIntent[]
  extractedRules: ExtractedRulesState | null
  isExtracting: boolean
  extractionError: string | null
  mergeWithDefaultRules: boolean
}

const ACCEPTED_TYPES = {
  'text/plain': 'txt',
  'text/markdown': 'md',
  'image/png': 'png',
  'image/jpeg': 'jpg',
  'image/jpg': 'jpg',
  'application/pdf': 'pdf',
}

interface FileUploadZoneProps {
  onUploadComplete?: (result: unknown) => void
  maxFiles?: number
  maxSize?: number
  className?: string
}

interface UploadFileItemWithIntent extends UploadFileItem {
  intent?: FileIntent
  textPreview?: string
}

export function FileUploadZone({
  onUploadComplete,
  maxFiles = 10,
  maxSize = 50 * 1024 * 1024,
  className,
}: FileUploadZoneProps) {
  const [files, setFiles] = useState<UploadFileItemWithIntent[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

   const [extractedRules, setExtractedRules] = useState<ExtractedRule[] | null>(null)
   const [rulesetMeta, setRulesetMeta] = useState<RulesetMetaInput | null>(null)
   const [isExtractingRules, setIsExtractingRules] = useState(false)
   const [mergeWithDefaultRules, setMergeWithDefaultRules] = useState(false)

   const extractedRulesRef = useRef<ExtractedRule[] | null>(null)
   const rulesetMetaRef = useRef<RulesetMetaInput | null>(null)
   const mergeWithDefaultRulesRef = useRef(false)

   const { refreshHistory, setIsAnalyzing, setError, switchAnalysis, startBatchAnalysis, batchStatus, isAnalyzing } = useAnalysis()

  const generateId = () => Math.random().toString(36).substring(2, 9)

  const validateFile = (file: File): string | null => {
    const isValidType = Object.keys(ACCEPTED_TYPES).includes(file.type) ||
      file.name.endsWith('.txt') ||
      file.name.endsWith('.md') ||
      file.name.endsWith('.png') ||
      file.name.endsWith('.jpg') ||
      file.name.endsWith('.jpeg') ||
      file.name.endsWith('.pdf')

    if (!isValidType) {
      return `File type "${file.type}" not accepted. Use .txt, .md, .png, .jpg, .jpeg, or .pdf`
    }

    if (file.size > maxSize) {
      return `File size exceeds maximum of ${maxSize / 1024 / 1024}MB`
    }

    return null
  }

  const addFiles = useCallback(async (newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles)
    const filesToAdd: UploadFileItemWithIntent[] = []

    for (const file of fileArray) {
      if (files.length + filesToAdd.length >= maxFiles) {
        break
      }

      const error = validateFile(file)
      
      let intent: FileIntent = 'unknown'
      let textPreview: string | undefined
      
       const isTextFile = file.name.endsWith('.txt') || 
                         file.name.endsWith('.md') || 
                         file.type === 'text/plain' || 
                         file.type === 'text/markdown'
       
       if (isTextFile) {
         try {
           textPreview = await file.text()
           intent = detectFileIntent(file, textPreview)
         } catch {
           intent = detectFileIntent(file)
         }
       } else {
         intent = detectFileIntent(file)
       }

      filesToAdd.push({
        id: generateId(),
        file,
        name: file.name,
        size: file.size,
        type: file.type,
        progress: 0,
        status: error ? 'error' : 'pending',
        error: error || undefined,
        intent,
        textPreview,
      })
    }

    setFiles(prev => [...prev, ...filesToAdd])
  }, [files.length, maxFiles, maxSize])

  const removeFile = useCallback((id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id))
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files) {
      addFiles(e.dataTransfer.files)
    }
  }, [addFiles])

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addFiles(e.target.files)
    }
  }, [addFiles])

  const uploadFile = async (fileItem: UploadFileItemWithIntent): Promise<UploadFileItemWithIntent> => {
    console.log('📤 [uploadFile] Starting upload for:', fileItem.name, 'intent:', fileItem.intent)

    if (fileItem.status === 'success' || fileItem.status === 'uploading') {
      console.log('📤 [uploadFile] Already done or uploading, skipping')
      return fileItem
    }

    setFiles(prev => prev.map(f =>
      f.id === fileItem.id ? { ...f, status: 'uploading' as const, progress: 0 } : f
    ))

    setIsAnalyzing(true)

    try {
      const isImage = fileItem.type.startsWith('image/') || 
        fileItem.name.endsWith('.png') || 
        fileItem.name.endsWith('.jpg') || 
        fileItem.name.endsWith('.jpeg')
      
      const isConstraintsDoc = fileItem.intent === 'constraints_document'
      const isLogFile = fileItem.intent === 'log_file' || 
        ((fileItem.name.endsWith('.txt') || fileItem.name.endsWith('.md')) && !isConstraintsDoc)

      let result: unknown
      let shouldRefreshHistory = true
      
       if (isImage) {
         const currentExtractedRules = extractedRulesRef.current
         const currentRulesetMeta = rulesetMetaRef.current
         
         console.log('📤 [uploadFile] Processing as image', currentExtractedRules ? 'with custom rules' : 'with default rules')
         const formData = new FormData()
         formData.append('file', fileItem.file)
         
         if (currentExtractedRules && currentExtractedRules.length > 0) {
           formData.append('extracted_rules', JSON.stringify(currentExtractedRules))
           console.log('📤 [uploadFile] Added extracted_rules to formData:', currentExtractedRules.length, 'rules')
           
           if (currentRulesetMeta) {
             formData.append('ruleset_meta', JSON.stringify(currentRulesetMeta))
           }
         }
         
         result = await aiApi.analyzeChart(formData)
       } else if (isConstraintsDoc) {
        console.log('📤 [uploadFile] Processing as constraints document - extracting rules')
        setIsExtractingRules(true)
        
        const text = fileItem.textPreview || (await fileItem.file.text())
        
        const extractResult = await aiApi.extractRules({
          document_text: text,
          filename: fileItem.name,
        })
        
        console.log('📤 [uploadFile] Rule extraction result:', extractResult)
        
         if (extractResult.success && extractResult.rules && extractResult.rules.length > 0) {
           setExtractedRules(extractResult.rules)
           extractedRulesRef.current = extractResult.rules
           const newMeta = {
             ...extractResult.meta,
             source: 'extracted',
             filename: fileItem.name,
             rule_count: extractResult.rules.length,
           }
           setRulesetMeta(newMeta)
           rulesetMetaRef.current = newMeta
           console.log(`✅ [uploadFile] Extracted ${extractResult.rules.length} rules from ${fileItem.name}`)
           result = extractResult
         } else {
           const errorMsg = extractResult.error || 'Failed to extract rules from document'
           throw new Error(errorMsg)
         }
         
         shouldRefreshHistory = false
       } else if (isLogFile) {
         const currentExtractedRules = extractedRulesRef.current
         const currentRulesetMeta = rulesetMetaRef.current
         const currentMerge = mergeWithDefaultRulesRef.current
         
         console.log('📤 [uploadFile] Processing as log file', currentExtractedRules ? 'with custom rules' : 'with default rules')
         
         const text = await fileItem.file.text()
         const rawLogs = text.split(/\r?\n/).filter(line => line.trim().length > 0)

         const requestParams: {
           raw_logs: string[]
           device_id: string
           extracted_rules?: ExtractedRule[]
           ruleset_meta?: RulesetMetaInput
           merge_with_default_rules?: boolean
         } = {
           raw_logs: rawLogs,
           device_id: fileItem.name.replace(/\.[^/.]+$/, ''),
         }

         if (currentExtractedRules && currentExtractedRules.length > 0) {
           requestParams.extracted_rules = currentExtractedRules
           requestParams.ruleset_meta = currentRulesetMeta || undefined
           requestParams.merge_with_default_rules = currentMerge
           console.log('📤 [uploadFile] Using extracted rules for validation:', currentExtractedRules.length, 'rules')
         }

         result = await reportsApi.generateFromLogs(requestParams)
      } else {
        console.log('📤 [uploadFile] Processing as generic file')
        const formData = new FormData()
        formData.append('file', fileItem.file)
        result = await logsApi.ingest(formData)
      }

      setFiles(prev => prev.map(f =>
        f.id === fileItem.id ? {
          ...f,
          status: 'success' as const,
          progress: 100,
        } : f
      ))

      onUploadComplete?.(result)

      if (shouldRefreshHistory) {
        console.log('🔄 [uploadFile] Refreshing history...')
        try {
          await refreshHistory()
          console.log('🔄 [uploadFile] Auto-selecting latest analysis...')
          switchAnalysis(0)
        } catch (refreshError) {
          console.warn('⚠️ [uploadFile] refreshHistory failed:', refreshError)
        }
      }

      return { ...fileItem, status: 'success', progress: 100 }
      
    } catch (error) {
      console.error('❌ [uploadFile] CAUGHT ERROR:', error)
      console.error('❌ [uploadFile] Error type:', typeof error)
      console.error('❌ [uploadFile] Error keys:', error instanceof Object ? Object.keys(error) : 'N/A')
      
      const errorMessage = error instanceof Error 
        ? error.message 
        : (typeof error === 'object' && error !== null && 'message' in error)
          ? String((error as { message: string }).message)
          : 'Upload failed'
      
      console.error('❌ [uploadFile] Final error message:', errorMessage)
      
      setError(errorMessage)
      setFiles(prev => prev.map(f =>
        f.id === fileItem.id ? {
          ...f,
          status: 'error' as const,
          error: errorMessage,
        } : f
      ))
      return { ...fileItem, status: 'error', error: errorMessage }
    } finally {
      console.log('🔚 [uploadFile] Finally: setIsAnalyzing(false)')
      setIsAnalyzing(false)
    }
  }

   const uploadAllFiles = async () => {
     const pendingFiles = files.filter(f => f.status === 'pending' || f.status === 'error')
     
     const sortedFiles = [...pendingFiles].sort((a, b) => {
       const aPriority = a.intent === 'constraints_document' ? 0 : 
                        a.intent === 'log_file' ? 2 : 1
       const bPriority = b.intent === 'constraints_document' ? 0 : 
                        b.intent === 'log_file' ? 2 : 1
       return aPriority - bPriority
     })
     
     console.log('📤 [uploadAllFiles] Uploading:', sortedFiles.length, 'files (sorted: constraints first)')
     for (const file of sortedFiles) {
       await uploadFile(file)
     }
   }

   const uploadAllFilesBatch = async () => {
     console.log('📤 [uploadAllFilesBatch] Starting batch mode analysis')

     const logFiles: File[] = []
     const chartImages: File[] = []
     const constraintsDocs: File[] = []

     for (const fileItem of files) {
       if (fileItem.intent === 'log_file') {
         logFiles.push(fileItem.file)
       } else if (fileItem.intent === 'image') {
         chartImages.push(fileItem.file)
       } else if (fileItem.intent === 'constraints_document') {
         constraintsDocs.push(fileItem.file)
       }
     }

     console.log('📤 [uploadAllFilesBatch] Grouped:', {
       logs: logFiles.length,
       charts: chartImages.length,
       constraints: constraintsDocs.length,
     })

     try {
       const response = await multimodalApi.analyze(
         logFiles,
         chartImages,
         constraintsDocs,
         {
           merge_logs: true,
           extract_rules: constraintsDocs.length > 0,
           align_charts: chartImages.length > 0,
           correlate_findings: true,
         }
       )

       console.log('📤 [uploadAllFilesBatch] Started analysis session:', response.session_id)

       startBatchAnalysis(response.session_id)

     } catch (error: unknown) {
       console.error('❌ [uploadAllFilesBatch] Failed:', error)
       const errorMessage = error instanceof Error
         ? error.message
         : (typeof error === 'object' && error !== null && 'message' in error)
           ? String((error as { message: string }).message)
           : 'Batch analysis failed'
       setError(errorMessage)
       setIsAnalyzing(false)
     }
   }

   const getFileIcon = (type: string, name: string, intent?: FileIntent) => {
    if (intent === 'constraints_document') {
      return <FileCode className="h-5 w-5 text-purple-600 dark:text-purple-400" />
    }
    if (intent === 'log_file') {
      return <FileText className="h-5 w-5 text-blue-600 dark:text-blue-400" />
    }
    if (type.startsWith('image/') || name.endsWith('.png') || name.endsWith('.jpg') || name.endsWith('.jpeg')) {
      return <Image className="h-5 w-5 text-cyan-600 dark:text-cyan-400" />
    }
    if (name.endsWith('.txt')) {
      return <FileText className="h-5 w-5 text-muted-foreground" />
    }
    return <File className="h-5 w-5 text-red-500 dark:text-red-400" />
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  const pendingCount = files.filter(f => f.status === 'pending' || f.status === 'error').length
  const uploadingCount = files.filter(f => f.status === 'uploading').length
  const successCount = files.filter(f => f.status === 'success').length

   const fileGroupCounts = useMemo(() => {
     const counts = { log_file: 0, constraints_document: 0, image: 0, unknown: 0 }
     for (const file of files) {
       if (file.intent && file.intent in counts) {
         counts[file.intent as keyof typeof counts]++
       }
     }
     return counts
   }, [files])

   return (
     <Card className={className}>
       <CardHeader className="pb-3">
           <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
             <CardTitle className="text-base font-medium flex items-center gap-2">
               <Upload className="h-5 w-5 text-primary" />
               Upload Files
             </CardTitle>
           </div>
         
         {batchStatus && batchStatus.current_step && (
           <div className="mt-3">
             <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
               <span>{batchStatus.current_step}</span>
               <span>
                 {batchStatus.progress !== undefined 
                   ? `${Math.round(batchStatus.progress * 100)}%` 
                   : batchStatus.status}
               </span>
             </div>
             <Progress 
               value={batchStatus.progress !== undefined ? batchStatus.progress * 100 : undefined} 
               className="h-1.5"
             />
           </div>
         )}
       </CardHeader>
       <CardContent>
         <div
           onDragOver={handleDragOver}
           onDragLeave={handleDragLeave}
           onDrop={handleDrop}
           onClick={() => fileInputRef.current?.click()}
           className={cn(
             'relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all touch-target',
             isDragging
               ? 'border-primary bg-primary/5'
               : 'border-border/80 hover:border-primary/50 hover:bg-muted/40'
           )}
           role="button"
           tabIndex={0}
           aria-label="Drag and drop files here or click to browse"
           onKeyDown={(e) => {
             if (e.key === 'Enter' || e.key === ' ') {
               e.preventDefault()
               fileInputRef.current?.click()
             }
           }}
         >
           <input
             ref={fileInputRef}
             type="file"
             multiple
              accept=".txt,.md,.png,.jpg,.jpeg,.pdf,text/plain,text/markdown,image/*,application/pdf"
             onChange={handleInputChange}
             className="hidden"
           />

           <Upload className={cn(
             'h-12 w-12 mx-auto mb-4 transition-colors',
             isDragging ? 'text-primary' : 'text-slate-400'
           )} />

           <p className="text-foreground font-medium mb-1">
             Drag and drop files here, or click to browse
           </p>
            <p className="text-sm text-muted-foreground">
               Supports: .txt/.md (logs or regulatory constraints), .png/.jpg/.jpeg (chart images)
             </p>
           <p className="text-xs text-slate-400 mt-2">
             Max {maxFiles} files, {maxSize / 1024 / 1024}MB each
           </p>
         </div>

          {files.length > 0 && (
            <div className="mt-6 space-y-3">
              <div className="flex flex-col gap-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-2">
                     <p className="text-sm font-medium text-foreground">
                       {files.length} file{files.length !== 1 ? 's' : ''} selected
                     </p>
                     
                     {fileGroupCounts.log_file > 0 && (
                       <Badge className={cn("text-xs", FILE_INTENT_COLORS.log_file)}>
                         <FileText className="h-3 w-3 mr-1" />
                         {fileGroupCounts.log_file} log{fileGroupCounts.log_file !== 1 ? 's' : ''}
                       </Badge>
                     )}
                     {fileGroupCounts.image > 0 && (
                       <Badge className={cn("text-xs", FILE_INTENT_COLORS.image)}>
                         <Image className="h-3 w-3 mr-1" />
                         {fileGroupCounts.image} chart{fileGroupCounts.image !== 1 ? 's' : ''}
                       </Badge>
                     )}
                     {fileGroupCounts.constraints_document > 0 && (
                       <Badge className={cn("text-xs", FILE_INTENT_COLORS.constraints_document)}>
                         <FileCode className="h-3 w-3 mr-1" />
                         {fileGroupCounts.constraints_document} constraint{fileGroupCounts.constraints_document !== 1 ? 's' : ''}
                       </Badge>
                     )}
                   </div>
                   
                   <div className="flex items-center gap-2 text-sm">
                     {isExtractingRules && (
                       <span className="text-purple-600 flex items-center gap-1">
                         <Loader2 className="h-4 w-4 animate-spin" />
                         Extracting rules...
                       </span>
                     )}
                     {isAnalyzing && (
                        <span className="text-primary flex items-center gap-1">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Analyzing...
                        </span>
                      )}
                   </div>
                </div>

               {extractedRules && (
                 <div className="flex items-center justify-between p-3 bg-purple-50 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-900/50 rounded-lg">
                   <div className="flex items-center gap-2">
                     <FileCheck className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                     <div>
                       <p className="text-sm font-medium text-purple-700 dark:text-purple-300">
                         Custom Rules Loaded
                       </p>
                       <p className="text-xs text-purple-600 dark:text-purple-400">
                         {extractedRules.length} rules from {rulesetMeta?.filename || 'document'}
                         {rulesetMeta?.average_confidence && ` • avg confidence: ${(rulesetMeta.average_confidence * 100).toFixed(0)}%`}
                       </p>
                     </div>
                   </div>
                   <div className="flex items-center gap-2">
                       <label className="flex items-center gap-1 text-xs cursor-pointer">
                         <input
                           type="checkbox"
                           checked={mergeWithDefaultRules}
                           onChange={(e) => {
                             setMergeWithDefaultRules(e.target.checked)
                             mergeWithDefaultRulesRef.current = e.target.checked
                           }}
                           className="rounded border-gray-300"
                         />
                         <span className="text-muted-foreground">Merge with default rules</span>
                       </label>
                       <button
                         onClick={() => {
                           setExtractedRules(null)
                           setRulesetMeta(null)
                           extractedRulesRef.current = null
                           rulesetMetaRef.current = null
                         }}
                         className="text-xs text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                       >
                         Clear
                       </button>
                   </div>
                 </div>
               )}
             </div>

             <div className="space-y-2">
              {files.map((file) => (
                <div
                  key={file.id}
                  className={cn(
                    'flex items-center gap-3 p-3 rounded-lg border transition-colors',
                    file.status === 'error'
                      ? 'bg-red-50 border-red-200 dark:bg-red-950/30 dark:border-red-900/50'
                      : 'bg-muted/40 border-slate-200'
                  )}
                >
                  <div className="flex-shrink-0">
                    {getFileIcon(file.type, file.name)}
                  </div>

                   <div className="flex-1 min-w-0">
                     <div className="flex items-center justify-between">
                       <div className="flex items-center gap-2 min-w-0">
                         <p className="text-sm font-medium text-foreground truncate">
                           {file.name}
                         </p>
                         {file.intent && file.intent !== 'unknown' && (
                           <Badge 
                             variant="secondary" 
                             className={cn(
                               "shrink-0 text-xs",
                               FILE_INTENT_COLORS[file.intent]
                             )}
                           >
                             {file.intent === 'constraints_document' && (
                               <FileCode className="h-3 w-3 mr-1" />
                             )}
                             {file.intent === 'log_file' && (
                               <FileText className="h-3 w-3 mr-1" />
                             )}
                             {file.intent === 'image' && (
                               <Image className="h-3 w-3 mr-1" />
                             )}
                             {FILE_INTENT_LABELS[file.intent]}
                           </Badge>
                         )}
                       </div>
                       <div className="flex items-center gap-2">
                         {file.status === 'success' && (
                           <CheckCircle2 className="h-4 w-4 text-green-600 flex-shrink-0" />
                         )}
                         {file.status === 'error' && (
                           <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0" />
                         )}
                         {file.status === 'uploading' && (
                           <Loader2 className="h-4 w-4 text-primary animate-spin flex-shrink-0" />
                         )}
                         <button
                           onClick={(e) => {
                             e.stopPropagation()
                             removeFile(file.id)
                           }}
                           className="p-1 hover:bg-border rounded touch-target"
                           aria-label={`Remove ${file.name}`}
                         >
                           <X className="h-4 w-4 text-muted-foreground" />
                         </button>
                       </div>
                     </div>

                     <p className="text-xs text-muted-foreground">
                       {formatFileSize(file.size)}
                     </p>

                    {file.error && (
                      <p className="text-xs text-red-600 mt-1">
                        {file.error}
                      </p>
                    )}

                    {file.status === 'uploading' && (
                      <Progress value={file.progress} className="h-1.5 mt-2" />
                    )}
                  </div>
                </div>
              ))}
            </div>

              {pendingCount > 0 && (
                 <div className="flex items-center justify-between pt-2 border-t border-slate-200">
                   <button
                     onClick={() => {
                       setFiles([])
                       setExtractedRules(null)
                       setRulesetMeta(null)
                       extractedRulesRef.current = null
                       rulesetMetaRef.current = null
                     }}
                     className="text-sm text-muted-foreground hover:text-foreground touch-target"
                   >
                     Clear all
                   </button>
                   
                   <Button
                     onClick={uploadAllFilesBatch}
                     disabled={isAnalyzing}
                     className="touch-target"
                   >
                     {isAnalyzing ? (
                       <>
                         <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                         Analyzing...
                       </>
                     ) : (
                       <>
                         <Layers className="h-4 w-4 mr-2" />
                         Analyze {pendingCount} file{pendingCount !== 1 ? 's' : ''}
                       </>
                     )}
                   </Button>
                 </div>
              )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
