import { Button } from '@/components/ui'
import { Sparkles, HelpCircle, AlertTriangle, CheckCircle, FileText } from 'lucide-react'

interface QuickSuggestionsProps {
  onSuggestion: (text: string) => void
  hasAnalysis: boolean
}

export function QuickSuggestions({ onSuggestion, hasAnalysis }: QuickSuggestionsProps) {
  const suggestions = hasAnalysis
    ? [
        { icon: HelpCircle, text: "De ce este asta un risc critic?" },
        { icon: AlertTriangle, text: "Ce trebuie să fac ACUM?" },
        { icon: CheckCircle, text: "Explică-mi în termeni simpli" },
        { icon: FileText, text: "Scrie-mi un email pentru manager" },
      ]
    : [
        { icon: HelpCircle, text: "Ce reguli există în MED-THERM?" },
        { icon: Sparkles, text: "Cum funcționează analiza AI?" },
      ]

  return (
    <div className="flex flex-wrap gap-2 justify-center">
      {suggestions.map((suggestion, i) => (
        <Button
          key={i}
          variant="outline"
          size="sm"
          onClick={() => onSuggestion(suggestion.text)}
          className="text-xs h-auto py-2 px-3 touch-target"
        >
          <suggestion.icon className="h-3 w-3 mr-1.5 text-primary" />
          {suggestion.text}
        </Button>
      ))}
    </div>
  )
}
