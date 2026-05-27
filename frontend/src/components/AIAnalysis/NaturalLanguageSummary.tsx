import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import { Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

interface NaturalLanguageSummaryProps {
  summary: string
  className?: string
}

 export function NaturalLanguageSummary({ summary, className }: NaturalLanguageSummaryProps) {
   return (
     <Card className={cn('border-purple-200 dark:border-purple-900/50 bg-gradient-to-br from-purple-50/50 to-white dark:from-purple-950/30 dark:to-card', className)}>
       <CardHeader className="pb-3">
         <div className="flex items-center gap-2">
           <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
             <Sparkles className="h-5 w-5 text-purple-600 dark:text-purple-400" />
           </div>
           <CardTitle className="text-base font-medium">AI Summary</CardTitle>
         </div>
       </CardHeader>
       <CardContent>
         <div className="prose prose-sm max-w-none">
           <p className="text-muted-foreground leading-relaxed whitespace-pre-line">
             {summary}
           </p>
         </div>
       </CardContent>
     </Card>
   )
 }
