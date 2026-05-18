import { useState, useRef, useCallback } from 'react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Progress,
} from '@/components/ui'
import { Upload, FileText, Image, File, X, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { UploadFileItem, ValidationResult } from '@/lib/api'
import { logsApi, aiApi, reportsApi } from '@/lib/api'
import { useAnalysis } from '@/lib/context/AnalysisContext'
import { 
  chartViolationsToFindings, 
  extractTemperatureFromChartResult,
  type TemperatureDataPoint 
} from '@/lib/utils/transformers'

const ACCEPTED_TYPES = {
  'text/plain': 'txt',
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

export function FileUploadZone({
  onUploadComplete,
  maxFiles = 10,
  maxSize = 50 * 1024 * 1024,
  className,
}: FileUploadZoneProps) {
  const [files, setFiles] = useState<UploadFileItem[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { refreshHistory, setIsAnalyzing, setError, switchAnalysis } = useAnalysis()

  const generateId = () => Math.random().toString(36).substring(2, 9)

  const validateFile = (file: File): string | null => {
    const isValidType = Object.keys(ACCEPTED_TYPES).includes(file.type) ||
      file.name.endsWith('.txt') ||
      file.name.endsWith('.png') ||
      file.name.endsWith('.jpg') ||
      file.name.endsWith('.jpeg') ||
      file.name.endsWith('.pdf')

    if (!isValidType) {
      return `File type "${file.type}" not accepted. Use .txt, .png, .jpg, .jpeg, or .pdf`
    }

    if (file.size > maxSize) {
      return `File size exceeds maximum of ${maxSize / 1024 / 1024}MB`
    }

    return null
  }

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles)
    const filesToAdd: UploadFileItem[] = []

    for (const file of fileArray) {
      if (files.length + filesToAdd.length >= maxFiles) {
        break
      }

      const error = validateFile(file)
      filesToAdd.push({
        id: generateId(),
        file,
        name: file.name,
        size: file.size,
        type: file.type,
        progress: 0,
        status: error ? 'error' : 'pending',
        error: error || undefined,
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

  const uploadFile = async (fileItem: UploadFileItem): Promise<UploadFileItem> => {
    console.log('📤 [uploadFile] Starting upload for:', fileItem.name)

    if (fileItem.status === 'success' || fileItem.status === 'uploading') {
      console.log('📤 [uploadFile] Already done or uploading, skipping')
      return fileItem
    }

    setFiles(prev => prev.map(f =>
      f.id === fileItem.id ? { ...f, status: 'uploading' as const, progress: 0 } : f
    ))

    setIsAnalyzing(true)

    try {
      console.log('📤 [uploadFile] Step 1: Determine file type')
      const isImage = fileItem.type.startsWith('image/') || 
        fileItem.name.endsWith('.png') || 
        fileItem.name.endsWith('.jpg') || 
        fileItem.name.endsWith('.jpeg')
      
      console.log('📤 [uploadFile] isImage:', isImage, 'type:', fileItem.type)

      let result: unknown
      
      if (isImage) {
        console.log('📤 [uploadFile] Step 2a: Uploading image to /api/ai/analyze-chart')
        const formData = new FormData()
        formData.append('file', fileItem.file)
        result = await aiApi.analyzeChart(formData)
        console.log('📤 [uploadFile] Image API response:', result)
      } else if (fileItem.name.endsWith('.txt')) {
        console.log('📤 [uploadFile] Step 2b: Uploading .txt to /api/reports/generate')
        const text = await fileItem.file.text()
        console.log('📤 [uploadFile] Text file length:', text.length)
        
        const rawLogs = text.split(/\r?\n/).filter(line => line.trim().length > 0)
        console.log('📤 [uploadFile] Raw log lines:', rawLogs.length)

        result = await reportsApi.generateFromLogs({
          raw_logs: rawLogs,
          device_id: fileItem.name.replace(/\.[^/.]+$/, ''),
        })
        console.log('📤 [uploadFile] Reports API response:', result)
      } else {
        console.log('📤 [uploadFile] Step 2c: Uploading other file type to /api/logs/ingest')
        const formData = new FormData()
        formData.append('file', fileItem.file)
        result = await logsApi.ingest(formData)
        console.log('📤 [uploadFile] Logs API response:', result)
      }

      console.log('✅ [uploadFile] Step 3: API call SUCCESS! Now marking as success')
      
      setFiles(prev => prev.map(f =>
        f.id === fileItem.id ? {
          ...f,
          status: 'success' as const,
          progress: 100,
        } : f
      ))

      onUploadComplete?.(result)

       console.log('🔄 [uploadFile] Step 4: Refreshing history...')
       try {
         await refreshHistory()
         console.log('✅ [uploadFile] History refreshed successfully!')
         
         // Dupa un nou upload, selecteaza automat cea mai recenta analiză (index 0, pentru ca sunt sortate descrescator)
         console.log('🔄 [uploadFile] Auto-selecting latest analysis...')
         switchAnalysis(0)
       } catch (refreshError) {
         console.warn('⚠️ [uploadFile] refreshHistory failed (but upload was successful):', refreshError)
       }

       console.log('✅ [uploadFile] DONE - Upload successful!')
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
    console.log('📤 [uploadAllFiles] Uploading:', pendingFiles.length, 'files')
    for (const file of pendingFiles) {
      await uploadFile(file)
    }
  }

  const getFileIcon = (type: string, name: string) => {
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

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-medium flex items-center gap-2">
          <Upload className="h-5 w-5 text-primary" />
          Upload Files
        </CardTitle>
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
            accept=".txt,.png,.jpg,.jpeg,.pdf,text/plain,image/*,application/pdf"
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
            Supports: .txt (logs), .png/.jpg/.jpeg (images), .pdf (documents)
          </p>
          <p className="text-xs text-slate-400 mt-2">
            Max {maxFiles} files, {maxSize / 1024 / 1024}MB each
          </p>
        </div>

        {files.length > 0 && (
          <div className="mt-6 space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-foreground">
                {files.length} file{files.length !== 1 ? 's' : ''} selected
              </p>
              <div className="flex items-center gap-2 text-sm">
                {successCount > 0 && (
                  <span className="text-green-600 flex items-center gap-1">
                    <CheckCircle2 className="h-4 w-4" />
                    {successCount} complete
                  </span>
                )}
                {uploadingCount > 0 && (
                  <span className="text-primary flex items-center gap-1">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    {uploadingCount} uploading
                  </span>
                )}
              </div>
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
                      <p className="text-sm font-medium text-foreground truncate">
                        {file.name}
                      </p>
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
                  onClick={() => setFiles([])}
                  className="text-sm text-muted-foreground hover:text-foreground touch-target"
                >
                  Clear all
                </button>
                <Button
                  onClick={uploadAllFiles}
                  disabled={uploadingCount > 0}
                  className="touch-target"
                >
                  {uploadingCount > 0 ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-2" />
                      Upload {pendingCount} file{pendingCount !== 1 ? 's' : ''}
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
