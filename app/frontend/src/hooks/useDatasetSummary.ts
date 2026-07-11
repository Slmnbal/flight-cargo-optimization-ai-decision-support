import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { queryKeys } from '@/lib/queryKeys'
import type { DatasetSummaryOut } from '@/types/api'

export function useDatasetSummary() {
  return useQuery({
    queryKey: queryKeys.datasetSummary,
    queryFn: () => apiClient.get<DatasetSummaryOut>('/dataset/summary'),
  })
}
