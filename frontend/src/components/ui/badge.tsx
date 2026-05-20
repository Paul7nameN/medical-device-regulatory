import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"
import { DataSource, SEVERITY_COLORS, DATA_SOURCE_LABELS, DATA_SOURCE_COLORS, DATA_SOURCE_DESCRIPTIONS } from "@/lib/api"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-4 focus:ring-primary/30 focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
         critical: "border-transparent bg-red-100 text-red-700 border-red-200 dark:bg-red-950/50 dark:text-red-400 dark:border-red-900",
         high: "border-transparent bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-950/50 dark:text-orange-400 dark:border-orange-900",
         medium: "border-transparent bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-950/50 dark:text-yellow-400 dark:border-yellow-900",
         low: "border-transparent bg-green-100 text-green-700 border-green-200 dark:bg-green-950/50 dark:text-green-400 dark:border-green-900",
         info: "border-transparent bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-950/50 dark:text-blue-400 dark:border-blue-900",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

type SeverityLevel = keyof typeof SEVERITY_COLORS

interface SeverityBadgeProps extends Omit<BadgeProps, 'variant'> {
  severity: SeverityLevel
}

function SeverityBadge({ severity, className, ...props }: SeverityBadgeProps) {
  const variantMap: Record<SeverityLevel, BadgeProps['variant']> = {
    critical: 'critical',
    high: 'high',
    medium: 'medium',
    low: 'low',
    info: 'info',
  }

  return (
    <Badge 
      variant={variantMap[severity] || 'default'} 
      className={className}
      {...props}
    >
      {severity.charAt(0).toUpperCase() + severity.slice(1)}
    </Badge>
  )
}

interface DataSourceBadgeProps extends Omit<BadgeProps, 'variant'> {
  source: DataSource
  showLabel?: boolean
}

function DataSourceBadge({ 
  source, 
  showLabel = true, 
  className,
  ...props 
}: DataSourceBadgeProps) {
  const label = DATA_SOURCE_LABELS[source]
  const colors = DATA_SOURCE_COLORS[source]

  return (
    <Badge 
      variant="outline" 
      className={cn(colors.badge, className)}
      title={DATA_SOURCE_DESCRIPTIONS[source]}
      {...props}
    >
      {showLabel && label}
    </Badge>
  )
}

export interface ConfidenceBadgeProps extends Omit<BadgeProps, 'variant'> {
  confidence: number
  showLabel?: boolean
  breakdown?: {
    log?: number
    chart?: number
    alignment?: number
  }
}

function ConfidenceBadge({ 
  confidence, 
  showLabel = true,
  breakdown,
  className,
  ...props 
}: ConfidenceBadgeProps) {
  const percentage = Math.round(confidence * 100)
  
  let variant: BadgeProps['variant'] = 'low'
  if (percentage < 50) variant = 'critical'
  else if (percentage < 70) variant = 'high'
  else if (percentage < 85) variant = 'medium'

  let tooltip = `Confidence: ${percentage}%`
  if (breakdown) {
    const parts: string[] = []
    if (breakdown.log !== undefined) parts.push(`Log: ${Math.round(breakdown.log * 100)}%`)
    if (breakdown.chart !== undefined) parts.push(`Chart: ${Math.round(breakdown.chart * 100)}%`)
    if (breakdown.alignment !== undefined) parts.push(`Alignment: ${Math.round(breakdown.alignment * 100)}%`)
    if (parts.length > 0) {
      tooltip = `${tooltip} (${parts.join(', ')})`
    }
  }

  return (
    <Badge 
      variant={variant}
      className={cn(className)}
      title={tooltip}
      {...props}
    >
      {showLabel && `${percentage}%`}
    </Badge>
  )
}

export { Badge, SeverityBadge, DataSourceBadge, ConfidenceBadge, badgeVariants }
