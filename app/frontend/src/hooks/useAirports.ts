import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { queryKeys } from '@/lib/queryKeys'
import type { AirportOut } from '@/types/api'

export function useAirports() {
  return useQuery({
    queryKey: queryKeys.airports,
    queryFn: () => apiClient.get<AirportOut[]>('/airports'),
    staleTime: 5 * 60_000, // referans verisi, nadiren değişir
  })
}
