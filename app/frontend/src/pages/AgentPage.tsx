import { useState, type FormEvent } from 'react'
import { useAgentChat } from '@/hooks/useAgentChat'
import { ChatMessage } from '@/components/agent/ChatMessage'
import { Icon } from '@/components/icons/Icon'

export function AgentPage() {
  const { messages, sendMessage, isPending, error } = useAgentChat()
  const [input, setInput] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isPending) return
    sendMessage(input)
    setInput('')
  }

  return (
    <div className="card flex h-[calc(100vh-10rem)] flex-col">
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center gap-3 py-16 text-center">
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-chrome-soft text-chrome">
              <Icon name="chat" size={18} />
            </span>
            <p className="max-w-md text-sm text-ink-muted">
              Sorular sorabilirsin, örn. "1 numaralı talep neden reddedildi?" veya "priority_class nasıl işliyor?".
              Agent, gerçek veritabanı verisine ve proje dokümantasyonuna (RAG) dayanarak cevap verir, veri uydurmaz.
            </p>
          </div>
        )}
        {messages.map((m) => (
          <ChatMessage key={m.id} message={m} />
        ))}
        {isPending && <p className="text-sm text-ink-muted">Agent yazıyor...</p>}
        {error && <p className="text-sm text-critical">{error.message}</p>}
      </div>
      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-border p-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Bir soru sor..."
          className="flex-1 rounded-full border border-border bg-surface px-4 py-2 text-sm text-ink placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-brand"
        />
        <button
          type="submit"
          disabled={isPending || !input.trim()}
          className="rounded-full bg-brand px-5 py-2 text-sm font-medium text-white hover:bg-brand-hover disabled:opacity-50"
        >
          Gönder
        </button>
      </form>
    </div>
  )
}
