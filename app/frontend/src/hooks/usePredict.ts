import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { queryKeys } from '@/lib/queryKeys'
import type { PredictResponse } from '@/types/api'

/**
 * "Tahmin Et" aksiyonuyla elle tetiklenir (enabled: false + refetch) -- her
 * kargo talebi satırı için otomatik tahmin çağırmak, tablo yüklenir yüklenmez
 * yüzlerce istek atmak demek olurdu.
 */
export function usePredict(requestId: number) {
  return useQuery({
    queryKey: queryKeys.prediction(requestId),
    queryFn: () => apiClient.get<PredictResponse>(`/ml/predict/${requestId}`),
    enabled: false,
    retry: false,
  })
}
