import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import type { GenerateDemandResponse } from '@/types/api'

export function useGenerateDemand() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => apiClient.post<GenerateDemandResponse>('/dataset/generate-demand'),
    onSuccess: () => {
      // Yeni pending talepler eklendi -- kargo talepleri/uçuşlar tabloları ve
      // veri seti özeti bayat kaldı.
      queryClient.invalidateQueries({ queryKey: ['cargo-requests'] })
      queryClient.invalidateQueries({ queryKey: ['flights'] })
      queryClient.invalidateQueries({ queryKey: ['dataset-summary'] })
    },
  })
}
