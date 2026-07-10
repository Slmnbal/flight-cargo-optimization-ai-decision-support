import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import type { OptimizeResponse } from '@/types/api'

export function useOptimize() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (scenarioName: string) =>
      apiClient.post<OptimizeResponse>('/optimize', undefined, { scenario_name: scenarioName }),
    onSuccess: () => {
      // Optimizasyon, cargo_requests.status'u ve yeni OptimizationResult
      // satırlarını değiştiriyor -- ilgili tüm görünümler bayat kalır.
      queryClient.invalidateQueries({ queryKey: ['kpis'] })
      queryClient.invalidateQueries({ queryKey: ['kpis-trend'] })
      queryClient.invalidateQueries({ queryKey: ['results'] })
      queryClient.invalidateQueries({ queryKey: ['cargo-requests'] })
      queryClient.invalidateQueries({ queryKey: ['flights'] })
    },
  })
}
