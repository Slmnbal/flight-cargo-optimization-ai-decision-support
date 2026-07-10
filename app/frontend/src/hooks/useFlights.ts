import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { queryKeys } from '@/lib/queryKeys'
import type { FlightsQuery, PaginatedFlightsOut } from '@/types/api'

export function useFlights(query: FlightsQuery = {}) {
  return useQuery({
    queryKey: queryKeys.flights(query),
    queryFn: () => apiClient.get<PaginatedFlightsOut>('/flights', query),
    placeholderData: (previous) => previous,
  })
}
