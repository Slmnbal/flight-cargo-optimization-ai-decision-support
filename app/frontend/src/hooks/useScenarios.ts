import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { queryKeys } from '@/lib/queryKeys'
import type { PaginatedScenariosOut, ScenariosQuery } from '@/types/api'

export function useScenarios(query: ScenariosQuery = {}) {
  return useQuery({
    queryKey: queryKeys.scenarios(query),
    queryFn: () => apiClient.get<PaginatedScenariosOut>('/scenarios', query),
    placeholderData: (previous) => previous,
  })
}
