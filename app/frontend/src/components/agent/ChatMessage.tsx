import type { ChatMessage as ChatMessageType } from '@/hooks/useAgentChat'

export function ChatMessage({ message }: { message: ChatMessageType }) {
  const isUser = message.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[75%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm ${
          isUser ? 'bg-brand text-white' : 'border border-border bg-surface text-ink'
        }`}
      >
        {message.content}
      </div>
    </div>
  )
}
