import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { queryKeys } from '@/lib/queryKeys'
import type { OptimizationResultOut } from '@/types/api'

export function useResults(scenarioName: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.results(scenarioName),
    queryFn: () => apiClient.get<OptimizationResultOut[]>(`/results/${encodeURIComponent(scenarioName)}`),
    enabled,
  })
}
