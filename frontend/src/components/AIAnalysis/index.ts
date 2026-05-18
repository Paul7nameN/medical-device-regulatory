import { type RiskLevel, type TrendIndicator } from '@/lib/api'

export { RiskOverviewCard } from './RiskOverviewCard'
export { InsightsList } from './InsightsList'
export { PredictionsList } from './PredictionsList'
export { ActionPlanCard } from './ActionPlanCard'
export { NaturalLanguageSummary } from './NaturalLanguageSummary'
export { AIAnalysisSection } from './AIAnalysisSection'

export const RISK_LEVEL_COLORS: Record<RiskLevel, { bg: string; text: string; border: string; badge: string }> = {
  critical: { bg: 'bg-red-50 dark:bg-red-950/30', text: 'text-red-700 dark:text-red-400', border: 'border-red-200 dark:border-red-900', badge: 'critical' },
  high: { bg: 'bg-orange-50 dark:bg-orange-950/30', text: 'text-orange-700 dark:text-orange-400', border: 'border-orange-200 dark:border-orange-900', badge: 'high' },
  medium: { bg: 'bg-yellow-50 dark:bg-yellow-950/30', text: 'text-yellow-700 dark:text-yellow-400', border: 'border-yellow-200 dark:border-yellow-900', badge: 'medium' },
  low: { bg: 'bg-green-50 dark:bg-green-950/30', text: 'text-green-700 dark:text-green-400', border: 'border-green-200 dark:border-green-900', badge: 'low' },
}

export const TREND_INDICATOR_INFO: Record<TrendIndicator, { icon: string; color: string; label: string }> = {
  stable: { icon: 'minus', color: 'text-blue-600 dark:text-blue-400', label: 'Stable' },
  improving: { icon: 'trending-down', color: 'text-green-600 dark:text-green-400', label: 'Improving' },
  deteriorating: { icon: 'trending-up', color: 'text-red-600 dark:text-red-400', label: 'Deteriorating' },
}

export function getRiskScoreColor(score: number): string {
  if (score >= 0.75) return 'text-red-600 dark:text-red-400'
  if (score >= 0.5) return 'text-orange-600 dark:text-orange-400'
  if (score >= 0.25) return 'text-yellow-600 dark:text-yellow-400'
  return 'text-green-600 dark:text-green-400'
}

export function getRiskScoreBg(score: number): string {
  if (score >= 0.75) return 'stroke-red-500 dark:stroke-red-400'
  if (score >= 0.5) return 'stroke-orange-500 dark:stroke-orange-400'
  if (score >= 0.25) return 'stroke-yellow-500 dark:stroke-yellow-400'
  return 'stroke-green-500 dark:stroke-green-400'
}
