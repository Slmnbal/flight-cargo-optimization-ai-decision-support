import { useQuery } from '@tanstack/react-query'
import { apiClient, ApiError } from '@/lib/apiClient'
import { queryKeys } from '@/lib/queryKeys'
import type { KpiSummaryOut } from '@/types/api'

export function useKpis(scenarioName: string) {
  return useQuery({
    queryKey: queryKeys.kpis(scenarioName),
    queryFn: () => apiClient.get<KpiSummaryOut>(`/kpis/${encodeURIComponent(scenarioName)}`),
    retry: (failureCount, error) => {
      // 404 = bu senaryo için henüz sonuç yok (örn. hiç optimizasyon çalıştırılmadı) --
      // tekrar denemek anlamsız, sabit bir hata olarak kalacak.
      if (error instanceof ApiError && error.status === 404) return false
      return failureCount < 2
    },
  })
}
