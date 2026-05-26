import { useState, useMemo } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import {
  SortingState,
  ColumnFiltersState,
  FilterFn,
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
} from '@tanstack/react-table'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  SeverityBadge,
  DataSourceBadge,
  ConfidenceBadge,
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  Input,
} from '@/components/ui'
import { DetectedViolation, REG_CATEGORIES, type DataSource, DATA_SOURCE_LABELS, compareSeverity } from '@/lib/api'
import { AlertTriangle, Filter, X, Eye, ChevronUp, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ViolationsTableProps {
  data: DetectedViolation[]
  title?: string
  onFilterChange?: (filters: ColumnFiltersState) => void
  initialFilters?: ColumnFiltersState
  className?: string
}

const severityFilterFn: FilterFn<DetectedViolation> = (row, columnId, filterValue) => {
  if (!filterValue || filterValue === 'all') return true
  return row.getValue(columnId) === filterValue
}

const regCategoryFilterFn: FilterFn<DetectedViolation> = (row, columnId, filterValue) => {
  if (!filterValue || filterValue === 'all') return true
  const regCode: string = row.getValue(columnId)
  return regCode.startsWith(filterValue)
}

interface DateRangeFilter {
  from?: string
  to?: string
}

const dateRangeFilterFn: FilterFn<DetectedViolation> = (row, columnId, filterValue: DateRangeFilter | undefined) => {
  if (!filterValue || (!filterValue.from && !filterValue.to)) return true
  
  const timestampStr: string = row.getValue(columnId)
  const rowDate = new Date(timestampStr)
  
  if (filterValue.from) {
    const fromDate = new Date(filterValue.from)
    fromDate.setHours(0, 0, 0, 0)
    if (rowDate < fromDate) return false
  }
  
  if (filterValue.to) {
    const toDate = new Date(filterValue.to)
    toDate.setHours(23, 59, 59, 999)
    if (rowDate > toDate) return false
  }
  
  return true
}

const dataSourceFilterFn: FilterFn<DetectedViolation> = (row, columnId, filterValue) => {
  if (!filterValue || filterValue === 'all') return true
  const source: DataSource | undefined = row.getValue(columnId)
  return source === filterValue
}

type ConfidenceFilter = 'all' | 'high' | 'medium' | 'low' | 'none'

const confidenceFilterFn: FilterFn<DetectedViolation> = (row, columnId, filterValue: ConfidenceFilter) => {
  if (!filterValue || filterValue === 'all') return true
  
  const confidence: number | undefined = row.getValue(columnId)
  
  if (filterValue === 'none') {
    return confidence === undefined
  }
  
  if (confidence === undefined) return false
  
  if (filterValue === 'high') return confidence >= 0.85
  if (filterValue === 'medium') return confidence >= 0.70 && confidence < 0.85
  if (filterValue === 'low') return confidence < 0.70
  
  return true
}

export function ViolationsTable({
  data,
  title = 'Detected Violations',
  onFilterChange,
  initialFilters = [],
  className,
}: ViolationsTableProps) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'severity', desc: false },
    { id: 'detected_at', desc: true },
  ])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>(initialFilters)
  const [selectedViolation, setSelectedViolation] = useState<DetectedViolation | null>(null)

  const hasDataSourceField = useMemo(
    () => data.some((d) => d.data_source !== undefined),
    [data]
  )

  const hasConfidenceField = useMemo(
    () => data.some((d) => d.confidence !== undefined),
    [data]
  )

  const availableDataSources = useMemo(() => {
    const sources = new Set<DataSource>()
    for (const d of data) {
      if (d.data_source) sources.add(d.data_source)
    }
    return Array.from(sources)
  }, [data])

  const columns = useMemo((): ColumnDef<DetectedViolation>[] => {
    const baseColumns: ColumnDef<DetectedViolation>[] = [
    {
      accessorKey: 'reg_code',
      header: ({ column }) => (
        <button
          className={cn('flex items-center gap-1 font-medium', 'cursor-pointer')}
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
        >
          REG Code
          {column.getIsSorted() === 'asc' && <ChevronUp className="h-3 w-3" />}
          {column.getIsSorted() === 'desc' && <ChevronDown className="h-3 w-3" />}
        </button>
      ),
      cell: ({ row }) => (
        <code className="text-sm font-mono bg-muted px-2 py-0.5 rounded text-primary-700">
          {row.getValue('reg_code')}
        </code>
      ),
      filterFn: regCategoryFilterFn,
    },
    {
      accessorKey: 'severity',
      header: ({ column }) => (
        <button
          className={cn('flex items-center gap-1 font-medium', 'cursor-pointer')}
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
        >
          Severity
          {column.getIsSorted() === 'asc' && <ChevronUp className="h-3 w-3" />}
          {column.getIsSorted() === 'desc' && <ChevronDown className="h-3 w-3" />}
        </button>
      ),
      cell: ({ row }) => (
        <SeverityBadge severity={row.getValue('severity')} />
      ),
      filterFn: severityFilterFn,
      sortingFn: (rowA, rowB) => compareSeverity(rowA.getValue('severity'), rowB.getValue('severity')),
    },
    {
      accessorKey: 'description',
      header: ({ column }) => (
        <button
          className={cn('flex items-center gap-1 font-medium', 'cursor-pointer')}
          onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
        >
          Description
          {column.getIsSorted() === 'asc' && <ChevronUp className="h-3 w-3" />}
          {column.getIsSorted() === 'desc' && <ChevronDown className="h-3 w-3" />}
        </button>
      ),
      cell: ({ row }) => {
        const desc: string | undefined = row.getValue('description')
        return (
          <span className="text-sm text-foreground line-clamp-2">
            {desc || 'No description'}
          </span>
        )
      },
    },
     {
       accessorKey: 'detected_at',
       header: ({ column }) => (
         <button
           className={cn('flex items-center gap-1 font-medium', 'cursor-pointer')}
           onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
         >
           Detected
           {column.getIsSorted() === 'asc' && <ChevronUp className="h-3 w-3" />}
           {column.getIsSorted() === 'desc' && <ChevronDown className="h-3 w-3" />}
         </button>
       ),
       cell: ({ row }) => {
         const timestamp: string = row.getValue('detected_at')
         return (
           <span className="text-sm text-muted-foreground">
             {new Date(timestamp).toLocaleString()}
           </span>
         )
       },
       filterFn: dateRangeFilterFn,
     },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => {
        const status: DetectedViolation['status'] = row.getValue('status')
        const statusColors: Record<string, string> = {
          open: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 border-red-200 dark:border-red-900/50',
          acknowledged: 'bg-yellow-100 text-yellow-700 border-yellow-200',
          resolved: 'bg-green-100 text-green-700 border-green-200',
        }
         return (
           <Badge className={cn(statusColors[status])}>
             {status.charAt(0).toUpperCase() + status.slice(1)}
           </Badge>
         )
       },
     },
    ]

    const dynamicColumns = []

    if (hasDataSourceField) {
      dynamicColumns.push({
        accessorKey: 'data_source' as const,
        header: 'Source',
        cell: ({ row }: { row: { original: DetectedViolation } }) => {
          const source: DataSource | undefined = row.original.data_source
          if (!source) {
            return <span className="text-sm text-muted-foreground">-</span>
          }
          return <DataSourceBadge source={source} />
        },
        filterFn: dataSourceFilterFn,
      })
    }

    if (hasConfidenceField) {
      dynamicColumns.push({
        accessorKey: 'confidence' as const,
        header: 'Confidence',
        cell: ({ row }: { row: { original: DetectedViolation } }) => {
          const confidence: number | undefined = row.original.confidence
          if (confidence === undefined) {
            return <span className="text-sm text-muted-foreground">-</span>
          }
          return (
            <ConfidenceBadge 
              confidence={confidence} 
              breakdown={row.original.confidence_breakdown}
            />
          )
        },
        filterFn: confidenceFilterFn,
      })
    }

     const actionsColumn: ColumnDef<DetectedViolation>[] = [
      {
        id: 'actions',
        header: 'Actions',
       cell: ({ row }) => (
        <Dialog>
          <DialogTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 px-2"
              onClick={() => setSelectedViolation(row.original)}
            >
              <Eye className="h-4 w-4" />
              <span className="sr-only">View details</span>
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-500" />
                Violation Details
              </DialogTitle>
              <DialogDescription>
                Complete details for this detected regulatory violation
              </DialogDescription>
            </DialogHeader>
            {selectedViolation && (
              <div className="space-y-4">
                 <div className="grid grid-cols-2 gap-4">
                   <div>
                     <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                       REG Code
                     </label>
                     <p className="font-mono text-lg text-primary">
                       {selectedViolation.reg_code}
                     </p>
                   </div>
                   <div>
                     <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                       Severity
                     </label>
                     <div className="mt-1">
                       <SeverityBadge severity={selectedViolation.severity} />
                     </div>
                   </div>
                   <div>
                     <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                       Status
                     </label>
                     <p className="mt-1">{selectedViolation.status}</p>
                   </div>
                   <div>
                     <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                       Risk Score
                     </label>
                     <p className="mt-1 font-medium">
                       {selectedViolation.risk_score !== undefined
                         ? `${selectedViolation.risk_score}/100`
                         : 'N/A'}
                     </p>
                   </div>
                   {selectedViolation.data_source && (
                     <div>
                       <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                         Data Source
                       </label>
                       <div className="mt-1">
                         <DataSourceBadge source={selectedViolation.data_source} />
                       </div>
                     </div>
                   )}
                   {selectedViolation.confidence !== undefined && (
                     <div>
                       <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                         Confidence
                       </label>
                       <div className="mt-1">
                         <ConfidenceBadge 
                           confidence={selectedViolation.confidence}
                           breakdown={selectedViolation.confidence_breakdown}
                         />
                       </div>
                     </div>
                   )}
                 </div>
                 {selectedViolation.confidence_breakdown && (
                   <div className="bg-muted/40 rounded-lg p-3">
                     <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide block mb-2">
                       Confidence Breakdown
                     </label>
                     <div className="grid grid-cols-3 gap-3 text-center">
                       {selectedViolation.confidence_breakdown.log !== undefined && (
                         <div>
                           <p className="text-xs text-muted-foreground">Logs</p>
                           <p className="text-sm font-medium">
                             {Math.round(selectedViolation.confidence_breakdown.log * 100)}%
                           </p>
                         </div>
                       )}
                       {selectedViolation.confidence_breakdown.chart !== undefined && (
                         <div>
                           <p className="text-xs text-muted-foreground">Chart</p>
                           <p className="text-sm font-medium">
                             {Math.round(selectedViolation.confidence_breakdown.chart * 100)}%
                           </p>
                         </div>
                       )}
                       {selectedViolation.confidence_breakdown.alignment !== undefined && (
                         <div>
                           <p className="text-xs text-muted-foreground">Alignment</p>
                           <p className="text-sm font-medium">
                             {Math.round(selectedViolation.confidence_breakdown.alignment * 100)}%
                           </p>
                         </div>
                       )}
                     </div>
                   </div>
                 )}
                <div>
                  <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Description
                  </label>
                  <p className="mt-1 text-foreground">
                    {selectedViolation.description || 'No description provided'}
                  </p>
                </div>
                {selectedViolation.evidence && selectedViolation.evidence.length > 0 && (
                  <div>
                    <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2 block">
                      Evidence ({selectedViolation.evidence.length} item{selectedViolation.evidence.length !== 1 ? 's' : ''})
                    </label>
                    <div className="space-y-2">
                      {selectedViolation.evidence.map((ev, idx) => (
                        <div key={idx} className="p-3 bg-muted/40 rounded-lg border border-border">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-foreground">
                              Entry #{ev.entry_index}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {new Date(ev.timestamp).toLocaleString()}
                            </span>
                          </div>
                          <p className="text-sm text-muted-foreground">{ev.explanation}</p>
                          <p className="text-xs text-muted-foreground mt-1 font-mono">
                            {ev.log_type}: {ev.raw_value}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
           </DialogContent>
         </Dialog>
       ),
     },
    ]

    return [...baseColumns, ...dynamicColumns, ...actionsColumn]
  }, [hasDataSourceField, hasConfidenceField])

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      columnFilters,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: (updater) => {
      setColumnFilters(updater)
      if (typeof updater === 'function') {
        onFilterChange?.(updater(columnFilters))
      } else {
        onFilterChange?.(updater)
      }
    },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
     filterFns: {
       severity: severityFilterFn,
       regCategory: regCategoryFilterFn,
       dataSource: dataSourceFilterFn,
       confidence: confidenceFilterFn,
     },
   })

  const severityFilter = columnFilters.find(f => f.id === 'severity')
  const categoryFilter = columnFilters.find(f => f.id === 'reg_code')
  const dateRangeFilter = columnFilters.find(f => f.id === 'detected_at') as { value?: DateRangeFilter } | undefined
  const dataSourceFilter = columnFilters.find(f => f.id === 'data_source')
  const confidenceFilter = columnFilters.find(f => f.id === 'confidence')

  const filteredRowCount = table.getFilteredRowModel().rows.length

  const clearFilters = () => {
    setColumnFilters([])
    onFilterChange?.([])
  }

  const handleDateFromChange = (value: string) => {
    const currentTo = dateRangeFilter?.value?.to
    if (!value && !currentTo) {
      setColumnFilters(prev => prev.filter(f => f.id !== 'detected_at'))
    } else {
      setColumnFilters(prev => {
        const filtered = prev.filter(f => f.id !== 'detected_at')
        return [...filtered, { id: 'detected_at', value: { from: value || undefined, to: currentTo } }]
      })
    }
  }

  const handleDateToChange = (value: string) => {
    const currentFrom = dateRangeFilter?.value?.from
    if (!value && !currentFrom) {
      setColumnFilters(prev => prev.filter(f => f.id !== 'detected_at'))
    } else {
      setColumnFilters(prev => {
        const filtered = prev.filter(f => f.id !== 'detected_at')
        return [...filtered, { id: 'detected_at', value: { from: currentFrom, to: value || undefined } }]
      })
    }
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <CardTitle className="text-base font-medium flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            {title}
            <Badge variant={filteredRowCount > 0 ? 'outline' : 'low'}>
              {filteredRowCount}/{data.length}
            </Badge>
          </CardTitle>

           <div className="flex flex-wrap items-center gap-2">
             <Select
               value={(severityFilter?.value as string) || 'all'}
               onValueChange={(value) => {
                 if (value === 'all') {
                   setColumnFilters(prev => prev.filter(f => f.id !== 'severity'))
                 } else {
                   setColumnFilters(prev => {
                     const filtered = prev.filter(f => f.id !== 'severity')
                     return [...filtered, { id: 'severity', value }]
                   })
                 }
               }}
             >
               <SelectTrigger className="w-[140px] h-9">
                 <SelectValue placeholder="All Severities" />
               </SelectTrigger>
               <SelectContent>
                 <SelectItem value="all">All Severities</SelectItem>
                 <SelectItem value="critical">Critical</SelectItem>
                 <SelectItem value="high">High</SelectItem>
                 <SelectItem value="medium">Medium</SelectItem>
                 <SelectItem value="low">Low</SelectItem>
                 <SelectItem value="info">Info</SelectItem>
               </SelectContent>
             </Select>

             <Select
               value={(categoryFilter?.value as string) || 'all'}
               onValueChange={(value) => {
                 if (value === 'all') {
                   setColumnFilters(prev => prev.filter(f => f.id !== 'reg_code'))
                 } else {
                   setColumnFilters(prev => {
                     const filtered = prev.filter(f => f.id !== 'reg_code')
                     return [...filtered, { id: 'reg_code', value }]
                   })
                 }
               }}
             >
               <SelectTrigger className="w-[180px] h-9">
                 <SelectValue placeholder="All Categories" />
               </SelectTrigger>
               <SelectContent>
                 <SelectItem value="all">All Categories</SelectItem>
                 {Object.entries(REG_CATEGORIES).map(([key, label]) => (
                   <SelectItem key={key} value={`REG-${key}`}>
                     {label} ({key})
                   </SelectItem>
                 ))}
                </SelectContent>
              </Select>

              {hasDataSourceField && availableDataSources.length > 0 && (
                <Select
                  value={(dataSourceFilter?.value as string) || 'all'}
                  onValueChange={(value) => {
                    if (value === 'all') {
                      setColumnFilters(prev => prev.filter(f => f.id !== 'data_source'))
                    } else {
                      setColumnFilters(prev => {
                        const filtered = prev.filter(f => f.id !== 'data_source')
                        return [...filtered, { id: 'data_source', value }]
                      })
                    }
                  }}
                >
                  <SelectTrigger className="w-[130px] h-9">
                    <SelectValue placeholder="All Sources" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Sources</SelectItem>
                    {availableDataSources.map((source) => (
                      <SelectItem key={source} value={source}>
                        {DATA_SOURCE_LABELS[source] || source}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}

              {hasConfidenceField && (
                <Select
                  value={(confidenceFilter?.value as string) || 'all'}
                  onValueChange={(value) => {
                    if (value === 'all') {
                      setColumnFilters(prev => prev.filter(f => f.id !== 'confidence'))
                    } else {
                      setColumnFilters(prev => {
                        const filtered = prev.filter(f => f.id !== 'confidence')
                        return [...filtered, { id: 'confidence', value }]
                      })
                    }
                  }}
                >
                  <SelectTrigger className="w-[140px] h-9">
                    <SelectValue placeholder="All Confidence" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Confidence</SelectItem>
                    <SelectItem value="high">High (≥85%)</SelectItem>
                    <SelectItem value="medium">Medium (70-84%)</SelectItem>
                    <SelectItem value="low">Low (under 70%)</SelectItem>
                    <SelectItem value="none">No Confidence</SelectItem>
                  </SelectContent>
                </Select>
              )}

              <div className="flex items-center gap-1">
               <Input
                 type="date"
                 value={dateRangeFilter?.value?.from || ''}
                 onChange={(e) => handleDateFromChange(e.target.value)}
                 className="w-[140px] h-9 text-sm"
                 placeholder="From"
               />
               <span className="text-slate-400 text-sm">→</span>
               <Input
                 type="date"
                 value={dateRangeFilter?.value?.to || ''}
                 onChange={(e) => handleDateToChange(e.target.value)}
                 className="w-[140px] h-9 text-sm"
                 placeholder="To"
               />
             </div>

             <Input
               placeholder="Search description..."
               value={(columnFilters.find(f => f.id === 'description')?.value as string) || ''}
               onChange={(e) => {
                 const value = e.target.value
                 if (value === '') {
                   setColumnFilters(prev => prev.filter(f => f.id !== 'description'))
                 } else {
                   setColumnFilters(prev => {
                     const filtered = prev.filter(f => f.id !== 'description')
                     return [...filtered, { id: 'description', value }]
                   })
                 }
               }}
               className="w-[180px] h-9"
             />

             {columnFilters.length > 0 && (
               <Button
                 variant="ghost"
                 size="sm"
                 onClick={clearFilters}
                 className="h-9 px-2"
               >
                 <X className="h-4 w-4 mr-1" />
                 Clear
               </Button>
             )}
           </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {filteredRowCount === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
            <Filter className="h-12 w-12 mb-2 opacity-50" />
            <p className="text-lg font-medium">No violations found</p>
            <p className="text-sm">Try adjusting your filters or upload logs for analysis</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                  <TableRow key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <TableHead key={header.id}>
                        {header.isPlaceholder
                          ? null
                          : flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                      </TableHead>
                    ))}
                  </TableRow>
                ))}
              </TableHeader>
              <TableBody>
                {table.getRowModel().rows.map((row) => (
                  <TableRow key={row.id}>
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id}>
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext()
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function ViolationsTableSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="h-5 w-48 bg-border rounded animate-pulse" />
          <div className="flex gap-2">
            <div className="h-9 w-36 bg-border rounded animate-pulse" />
            <div className="h-9 w-36 bg-border rounded animate-pulse" />
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="p-4 space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-12 bg-muted rounded animate-pulse" />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
