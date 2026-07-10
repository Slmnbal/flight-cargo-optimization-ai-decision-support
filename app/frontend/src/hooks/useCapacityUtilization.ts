import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { queryKeys } from '@/lib/queryKeys'
import type { CapacityUtilizationOut } from '@/types/api'

export function useCapacityUtilization(flightId: number | undefined) {
  return useQuery({
    queryKey: queryKeys.capacityUtilization(flightId ?? -1),
    queryFn: () => apiClient.get<CapacityUtilizationOut>(`/flights/${flightId}/capacity-utilization`),
    enabled: flightId !== undefined,
  })
}
