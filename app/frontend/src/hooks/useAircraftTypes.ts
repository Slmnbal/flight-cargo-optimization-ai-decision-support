import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { queryKeys } from '@/lib/queryKeys'
import type { AircraftTypeOut } from '@/types/api'

export function useAircraftTypes() {
  return useQuery({
    queryKey: queryKeys.aircraftTypes,
    queryFn: () => apiClient.get<AircraftTypeOut[]>('/aircraft-types'),
    staleTime: 5 * 60_000,
  })
}
