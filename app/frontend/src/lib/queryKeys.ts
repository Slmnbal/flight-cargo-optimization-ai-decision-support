import type { CargoRequestsQuery, FlightsQuery, KpiTrendGroupBy } from '@/types/api'

export const queryKeys = {
  routes: ['routes'] as const,
  aircraftTypes: ['aircraft-types'] as const,
  flights: (query: FlightsQuery) => ['flights', query] as const,
  cargoRequests: (query: CargoRequestsQuery) => ['cargo-requests', query] as const,
  kpis: (scenarioName: string) => ['kpis', scenarioName] as const,
  kpiTrend: (startDate: string | undefined, endDate: string | undefined, groupBy: KpiTrendGroupBy) =>
    ['kpis-trend', startDate, endDate, groupBy] as const,
  capacityUtilization: (flightId: number) => ['capacity-utilization', flightId] as const,
  results: (scenarioName: string) => ['results', scenarioName] as const,
  prediction: (requestId: number) => ['ml-predict', requestId] as const,
}
