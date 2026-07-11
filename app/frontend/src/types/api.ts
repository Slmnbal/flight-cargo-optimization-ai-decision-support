// app/backend/app/schemas/schemas.py ile birebir eşleşen tipler. Elle
// senkron tutuluyor (bu ölçekte OpenAPI codegen gereksiz) -- schemas.py
// değiştiğinde burası da güncellenmeli.

export interface AirportOut {
  airport_code: string
  airport_name: string
  country: string
  timezone: string
  customs_available: boolean
}

export interface RouteOut {
  route_id: number
  origin_airport: string
  destination_airport: string
  distance_km: number
  route_type: string
  region: string
  customs_required: boolean
  restricted_cargo_allowed: boolean
  embargo_active: boolean
  embargoed_cargo_types: string | null
  is_active: boolean
}

export type FlightStatus = 'scheduled' | 'completed' | string

export interface FlightOut {
  flight_id: number
  flight_number: string
  route_id: number
  aircraft_type: string
  aircraft_registration: string | null
  departure_scheduled: string
  arrival_scheduled: string
  status: FlightStatus
}

export type CargoStatus = 'pending' | 'accepted' | 'rejected'
export type CargoType = 'general' | 'perishable' | 'dangerous_goods' | 'valuable' | 'live_animal' | 'oversized'
export type PriorityClass = 'contract' | 'spot'

export interface CargoRequestOut {
  request_id: number
  flight_id: number
  cargo_type: CargoType
  weight_kg: number
  volume_m3: number
  requires_temperature_control: boolean
  priority_class: PriorityClass
  revenue: number
  booking_cutoff_hours: number
  status: CargoStatus
}

export interface AircraftTypeOut {
  aircraft_type: string
  max_cargo_weight_kg: number
  max_cargo_volume_m3: number
  temperature_controlled_capacity_kg: number
  is_freighter: boolean
  dangerous_goods_allowed: boolean
}

export interface OptimizationResultOut {
  result_id: number
  scenario_name: string
  request_id: number
  decision: 'accepted' | 'rejected'
  revenue: number
  reason: string | null
  run_at: string
}

export interface KpiSummaryOut {
  scenario_name: string
  total_requests: number
  accepted_count: number
  rejected_count: number
  total_revenue: number
  rejection_reason_breakdown: Record<string, number>
  last_run_at: string
}

export interface OptimizeResponse {
  status: string
  accepted: number[]
  rejected: number[]
  total_revenue: number
}

export interface TrainResponse {
  trained: boolean
  detail: string
  accuracy: number | null
  n_samples: number | null
}

export interface PredictResponse {
  request_id: number
  acceptance_probability: number
}

export interface AgentAskRequest {
  question: string
  session_id: string | null
}

export interface AgentAskResponse {
  answer: string
  session_id: string
}

export interface PaginatedFlightsOut {
  items: FlightOut[]
  total: number
}

export interface PaginatedCargoRequestsOut {
  items: CargoRequestOut[]
  total: number
}

export interface CapacityUtilizationOut {
  flight_id: number
  flight_number: string
  weight_utilization_pct: number
  volume_utilization_pct: number
}

export interface KpiTrendPointOut {
  period: string
  total_requests: number
  accepted_count: number
  rejected_count: number
  total_revenue: number
  acceptance_rate: number
  avg_weight_utilization_pct: number
  avg_volume_utilization_pct: number
}

export type KpiTrendGroupBy = 'day' | 'week' | 'month'

export interface KpiTrendResponse {
  group_by: KpiTrendGroupBy
  points: KpiTrendPointOut[]
}

export interface FlightsQuery {
  date_from?: string
  date_to?: string
  route_id?: number
  status?: string
  limit?: number
  offset?: number
}

export interface CargoRequestsQuery {
  flight_id?: number
  cargo_type?: string
  priority_class?: string
  status?: string
  date_from?: string
  date_to?: string
  limit?: number
  offset?: number
}

export interface ScenarioSummaryOut {
  scenario_name: string
  total_requests: number
  accepted_count: number
  rejected_count: number
  total_revenue: number
  last_run_at: string
}

export interface PaginatedScenariosOut {
  items: ScenarioSummaryOut[]
  total: number
}

export interface ScenariosQuery {
  limit?: number
  offset?: number
}

export interface DatasetSummaryOut {
  airports_count: number
  aircraft_types_count: number
  routes_count: number
  flights_count: number
  cargo_requests_count: number
  optimization_results_count: number
  data_start: string | null
  data_end: string | null
}

export interface GenerateDemandResponse {
  generated_count: number
  flights_count: number
  pending_count: number
}
