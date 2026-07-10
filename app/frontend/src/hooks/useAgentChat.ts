import { useCallback, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import type { AgentAskRequest, AgentAskResponse } from '@/types/api'

export interface ChatMessage {
  id: string
  role: 'user' | 'agent'
  content: string
}

/**
 * Sohbet geçmişi backend'de var (agent_messages tablosu, session_id ile) ama
 * bunu okuyan bir GET endpoint'i yok -- agent zaten her cevapta önceki turları
 * kendi hafızasında (son 20 mesaj) tutuyor, bu yüzden frontend'in kendi local
 * state'i (sayfa yenilenince sıfırlanan) yeterli; ayrı bir history endpoint'i
 * eklemek bu aşamada gereksiz karmaşıklık olurdu.
 */
export function useAgentChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: (question: string) =>
      apiClient.post<AgentAskResponse>('/agent/ask', {
        question,
        session_id: sessionId,
      } satisfies AgentAskRequest),
  })

  const sendMessage = useCallback(
    (question: string) => {
      const trimmed = question.trim()
      if (!trimmed) return

      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'user', content: trimmed }])

      mutation.mutate(trimmed, {
        onSuccess: (response) => {
          setSessionId(response.session_id)
          setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'agent', content: response.answer }])
        },
      })
    },
    [mutation],
  )

  return { messages, sendMessage, isPending: mutation.isPending, error: mutation.error }
}
