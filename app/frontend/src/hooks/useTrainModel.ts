import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import type { TrainResponse } from '@/types/api'

export function useTrainModel() {
  return useMutation({
    mutationFn: () => apiClient.post<TrainResponse>('/ml/train'),
  })
}
