import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/apiClient'
import { queryKeys } from '@/lib/queryKeys'
import type { KpiTrendGroupBy, KpiTrendResponse } from '@/types/api'

export function useKpiTrend(startDate?: string, endDate?: string, groupBy: KpiTrendGroupBy = 'day') {
  return useQuery({
    queryKey: queryKeys.kpiTrend(startDate, endDate, groupBy),
    queryFn: () =>
      apiClient.get<KpiTrendResponse>('/kpis/trend', {
        start_date: startDate,
        end_date: endDate,
        group_by: groupBy,
      }),
  })
}
