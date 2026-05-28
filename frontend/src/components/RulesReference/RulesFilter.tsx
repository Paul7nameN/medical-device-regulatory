import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Badge,
} from '@/components/ui'
import { Filter, X } from 'lucide-react'
import type { RuleCategory, ValidationType } from '@/lib/constants/regulatoryRules'
import {
  CATEGORY_NAMES,
  getCategories,
} from '@/lib/constants/regulatoryRules'

interface RulesFilterProps {
  selectedCategory: RuleCategory | null
  selectedValidationType: ValidationType | null
  onCategoryChange: (category: RuleCategory | null) => void
  onValidationTypeChange: (type: ValidationType | null) => void
  totalRules: number
  filteredCount: number
}

export function RulesFilter({
  selectedCategory,
  selectedValidationType,
  onCategoryChange,
  onValidationTypeChange,
  totalRules,
  filteredCount,
}: RulesFilterProps) {
  const categories = getCategories()

  const hasFilters = selectedCategory !== null || selectedValidationType !== null

  const clearFilters = () => {
    onCategoryChange(null)
    onValidationTypeChange(null)
  }

  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-4">
      <div className="flex items-center gap-2 flex-shrink-0">
        <Filter className="h-4 w-4 text-slate-400 flex-shrink-0" />
        <span className="text-sm text-slate-600 whitespace-nowrap">
          Showing <strong>{filteredCount}</strong> of <strong>{totalRules}</strong> rules
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-[180px_140px_auto] items-center gap-3 flex-shrink-0">
        <Select
          value={selectedCategory || 'all'}
          onValueChange={(value) => onCategoryChange(value === 'all' ? null : (value as RuleCategory))}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="All Categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {categories.map((cat) => (
              <SelectItem key={cat} value={cat} className="truncate">
                <span className="font-medium">{cat}</span>
                <span className="text-slate-500 ml-2 text-xs hidden sm:inline">
                  — {CATEGORY_NAMES[cat]}
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={selectedValidationType || 'all'}
          onValueChange={(value) => onValidationTypeChange(value === 'all' ? null : (value as ValidationType))}
        >
          <SelectTrigger className="w-full">
            {selectedValidationType === 'operational' ? (
              <div className="flex items-center gap-2">
                <Badge variant="info" className="text-xs">
                  Operational
                </Badge>
              </div>
            ) : selectedValidationType === 'inspection' ? (
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  Inspection
                </Badge>
              </div>
            ) : (
              <SelectValue placeholder="All Types" />
            )}
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="operational">
              <div className="flex items-center gap-2">
                <Badge variant="info" className="text-xs flex-shrink-0">
                  Operational
                </Badge>
                <span className="text-slate-500 text-xs">
                  — Validated from logs
                </span>
              </div>
            </SelectItem>
            <SelectItem value="inspection">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs flex-shrink-0">
                  Inspection
                </Badge>
                <span className="text-slate-500 text-xs">
                  — Requires physical check
                </span>
              </div>
            </SelectItem>
          </SelectContent>
        </Select>

        {/* Butonul Clear apare doar când este nevoie, în coloana auto */}
        {hasFilters && (
          <button
            onClick={clearFilters}
            className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors whitespace-nowrap justify-self-end"
          >
            <X className="h-3 w-3" />
            Clear
          </button>
        )}
      </div>
    </div>
  )
}
