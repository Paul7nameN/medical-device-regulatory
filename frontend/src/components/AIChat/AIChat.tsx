import { useState, useRef, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, Input, Button, Badge } from '@/components/ui'
import { MessageCircle, Send, Bot, Loader2, Sparkles } from 'lucide-react'
import { aiApi } from '@/lib/api'
import type { ChatMessage, AIAnalysisResult } from '@/lib/api'
import { ChatMessageBubble } from './ChatMessageBubble'
import { QuickSuggestions } from './QuickSuggestions'
import { cn } from '@/lib/utils'

interface AIChatProps {
  analysisSessionId?: string
  aiAnalysis?: AIAnalysisResult
  className?: string
  defaultCollapsed?: boolean
}

export function AIChat({ analysisSessionId, aiAnalysis, className, defaultCollapsed = false }: AIChatProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const hasAnalysis = !!(analysisSessionId || aiAnalysis)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: ChatMessage = { role: 'user', content: input.trim() }
    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setInput('')
    setIsLoading(true)

    try {
      const response = await aiApi.chat({
        analysis_session_id: analysisSessionId,
        message: userMessage.content,
        chat_history: newMessages.slice(0, -1),
      })

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.message,
      }
      setMessages([...newMessages, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      }
      setMessages([...newMessages, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

   const handleSuggestion = (text: string) => {
     setInput(text)
   }

  if (isCollapsed) {
    return (
      <Button
        variant="default"
        size="icon"
        className={cn(
          'rounded-full shadow-lg h-14 w-14 p-0 relative flex items-center justify-center',
          className
        )}
        onClick={() => setIsCollapsed(false)}
      >
        <MessageCircle className="h-7 w-7" />
        {messages.length > 0 && (
          <Badge
            variant="destructive"
            className="absolute -top-1 -right-1 h-5 w-5 p-0 flex items-center justify-center text-xs"
          >
            {messages.length}
          </Badge>
        )}
      </Button>
    )
  }

  return (
    <Card className={cn('fixed bottom-6 right-6 w-96 max-w-[calc(100vw-3rem)] flex flex-col h-[500px] max-h-[70vh] shadow-xl z-50', className)}>
      <CardHeader className="pb-2 border-b flex flex-row items-center justify-between">
         <div className="flex items-center gap-2">
           <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
             <Bot className="h-5 w-5 text-purple-600 dark:text-purple-400" />
           </div>
           <div>
             <CardTitle className="text-sm font-medium">AI Assistant</CardTitle>
             <p className="text-xs text-muted-foreground">
               {hasAnalysis ? 'Ask about this analysis' : 'Ask about compliance'}
             </p>
           </div>
         </div>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setIsCollapsed(true)}>
          <MessageCircle className="h-4 w-4" />
        </Button>
      </CardHeader>

       <CardContent className="flex-1 overflow-y-auto p-4">
         {messages.length === 0 ? (
           <div className="flex flex-col items-center justify-center h-full text-center">
             <div className="p-4 bg-muted rounded-full mb-4">
               <Sparkles className="h-8 w-8 text-muted-foreground" />
             </div>
             <p className="text-sm font-medium text-foreground mb-1">How can I help you?</p>
             <p className="text-xs text-muted-foreground mb-6">
               {hasAnalysis
                 ? 'Ask questions about this analysis session'
                 : 'Ask about MED-THERM compliance'}
             </p>
             <QuickSuggestions onSuggestion={handleSuggestion} hasAnalysis={hasAnalysis} />
           </div>
         ) : (
           <div>
             {messages.map((msg, i) => (
               <ChatMessageBubble key={i} message={msg} />
             ))}
             {isLoading && (
               <div className="flex gap-3 mb-4">
                 <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                   <Bot className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                 </div>
                 <div className="bg-muted rounded-2xl rounded-tl-none px-4 py-3">
                   <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                 </div>
               </div>
             )}
             <div ref={messagesEndRef} />
           </div>
         )}
       </CardContent>

      <div className="p-3 border-t">
        <div className="flex gap-2">
          <Input
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            className="touch-target"
          />
          <Button
            variant="default"
            size="icon"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="touch-target h-10 w-10"
          >
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
      </div>
    </Card>
  )
}
