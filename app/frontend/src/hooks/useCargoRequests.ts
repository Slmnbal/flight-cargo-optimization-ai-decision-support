import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { queryKeys } from '@/lib/queryKeys'
import type { CargoRequestsQuery, PaginatedCargoRequestsOut } from '@/types/api'

export function useCargoRequests(query: CargoRequestsQuery = {}) {
  return useQuery({
    queryKey: queryKeys.cargoRequests(query),
    queryFn: () => apiClient.get<PaginatedCargoRequestsOut>('/cargo-requests', query),
    placeholderData: (previous) => previous,
  })
}
