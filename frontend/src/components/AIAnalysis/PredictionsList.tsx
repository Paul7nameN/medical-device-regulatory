import { Card, CardContent, CardHeader, CardTitle, Badge } from '@/components/ui'
import { Sparkles, Clock, AlertTriangle, ShieldCheck } from 'lucide-react'
import type { Prediction } from '@/lib/api'
import { cn } from '@/lib/utils'

interface PredictionsListProps {
  predictions: Prediction[]
  className?: string
}

function PredictionItem({ prediction }: { prediction: Prediction }) {
  const confidencePercent = Math.round(prediction.confidence * 100)

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return 'bg-red-50 dark:bg-red-950/300 dark:bg-red-600'
    if (confidence >= 0.6) return 'bg-orange-500 dark:bg-orange-600'
    if (confidence >= 0.4) return 'bg-yellow-500 dark:bg-yellow-400'
    return 'bg-blue-500'
  }

  return (
    <Card className="border-slate-200">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="h-4 w-4 text-purple-500 dark:text-purple-400" />
              <span className="text-xs font-medium text-purple-600">Prediction</span>
              {prediction.estimated_probability && (
                <Badge variant="outline" className="text-xs">
                  {prediction.estimated_probability}
                </Badge>
              )}
            </div>
            <CardTitle className="text-sm font-medium">{prediction.scenario}</CardTitle>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
            <span>Confidence</span>
            <span className="font-medium">{confidencePercent}%</span>
          </div>
          <div className="w-full bg-border rounded-full h-2">
            <div
              className={cn('h-2 rounded-full transition-all', getConfidenceColor(prediction.confidence))}
              style={{ width: `${confidencePercent}%` }}
            />
          </div>
        </div>

        {prediction.timeframe && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span>Timeframe: {prediction.timeframe}</span>
          </div>
        )}

        {prediction.risk_factors_driving_this.length > 0 && (
          <div>
            <div className="flex items-center gap-1 text-xs font-medium text-muted-foreground mb-2">
              <AlertTriangle className="h-3 w-3" />
              Risk Factors
            </div>
            <ul className="space-y-1">
              {prediction.risk_factors_driving_this.map((factor, i) => (
                <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                  <span className="text-orange-500 mt-1">•</span>
                  {factor}
                </li>
              ))}
            </ul>
          </div>
        )}

        {prediction.mitigation_potential && (
          <div>
            <div className="flex items-center gap-1 text-xs font-medium text-muted-foreground mb-1">
              <ShieldCheck className="h-3 w-3 text-green-500" />
              Mitigation Potential
            </div>
            <p className="text-sm text-muted-foreground">{prediction.mitigation_potential}</p>
          </div>
        )}

        {prediction.why_concerning && (
          <div className="p-2 bg-red-50 dark:bg-red-950/30 rounded border border-red-100">
            <p className="text-sm text-red-700">
              <strong>Why concerning:</strong> {prediction.why_concerning}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function PredictionsList({ predictions, className }: PredictionsListProps) {
  if (!predictions || predictions.length === 0) {
    return null
  }

  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-purple-500 dark:text-purple-400" />
        <h3 className="text-base font-medium">Predictions ({predictions.length})</h3>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {predictions.map((prediction) => (
          <PredictionItem key={prediction.id} prediction={prediction} />
        ))}
      </div>
    </div>
  )
}
