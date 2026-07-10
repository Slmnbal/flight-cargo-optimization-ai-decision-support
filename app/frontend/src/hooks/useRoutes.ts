import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { queryKeys } from '@/lib/queryKeys'
import type { RouteOut } from '@/types/api'

export function useRoutes() {
  return useQuery({
    queryKey: queryKeys.routes,
    queryFn: () => apiClient.get<RouteOut[]>('/routes'),
    staleTime: 5 * 60_000, // referans verisi, nadiren değişir
  })
}
