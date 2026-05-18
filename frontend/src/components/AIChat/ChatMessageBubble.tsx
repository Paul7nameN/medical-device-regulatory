import { User, Bot } from 'lucide-react'
import type { ChatMessage } from '@/lib/api'
import { cn } from '@/lib/utils'

interface ChatMessageBubbleProps {
  message: ChatMessage
}

export function ChatMessageBubble({ message }: ChatMessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex gap-3 mb-4', isUser ? 'flex-row-reverse' : 'flex-row')}>
       <div
         className={cn(
           'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
           isUser ? 'bg-primary/10' : 'bg-purple-100 dark:bg-purple-900/30'
         )}
       >
         {isUser ? (
           <User className="h-4 w-4 text-primary" />
         ) : (
           <Bot className="h-4 w-4 text-purple-600 dark:text-purple-400" />
         )}
       </div>
       <div
         className={cn(
           'max-w-[80%] rounded-2xl px-4 py-3',
           isUser
             ? 'bg-primary text-primary-foreground rounded-tr-none'
             : 'bg-muted text-foreground rounded-tl-none'
         )}
       >
         <p className="text-sm whitespace-pre-wrap">{message.content}</p>
       </div>
    </div>
  )
}
