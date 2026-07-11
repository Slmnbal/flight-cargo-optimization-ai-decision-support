from datetime import date, datetime
from pydantic import BaseModel


class AirportOut(BaseModel):
    airport_code: str
    airport_name: str
    country: str
    timezone: str
    customs_available: bool

    class Config:
        from_attributes = True


class RouteOut(BaseModel):
    route_id: int
    origin_airport: str
    destination_airport: str
    distance_km: float
    route_type: str
    region: str
    customs_required: bool
    restricted_cargo_allowed: bool
    embargo_active: bool
    embargoed_cargo_types: str | None
    is_active: bool

    class Config:
        from_attributes = True


class FlightOut(BaseModel):
    flight_id: int
    flight_number: str
    route_id: int
    aircraft_type: str
    aircraft_registration: str | None
    departure_scheduled: datetime
    arrival_scheduled: datetime
    status: str

    class Config:
        from_attributes = True


class CargoRequestOut(BaseModel):
    request_id: int
    flight_id: int
    cargo_type: str
    weight_kg: float
    volume_m3: float
    requires_temperature_control: bool
    priority_class: str
    revenue: float
    booking_cutoff_hours: int
    status: str

    class Config:
        from_attributes = True


class AircraftTypeOut(BaseModel):
    aircraft_type: str
    max_cargo_weight_kg: float
    max_cargo_volume_m3: float
    temperature_controlled_capacity_kg: float
    is_freighter: bool
    dangerous_goods_allowed: bool

    class Config:
        from_attributes = True


class OptimizationResultOut(BaseModel):
    result_id: int
    scenario_name: str
    request_id: int
    decision: str
    revenue: float
    reason: str | None
    run_at: datetime

    class Config:
        from_attributes = True


class KpiSummaryOut(BaseModel):
    scenario_name: str
    total_requests: int
    accepted_count: int
    rejected_count: int
    total_revenue: float
    rejection_reason_breakdown: dict[str, int]
    last_run_at: datetime


class OptimizeResponse(BaseModel):
    status: str
    accepted: list[int]
    rejected: list[int]
    total_revenue: float


class TrainResponse(BaseModel):
    trained: bool
    detail: str
    accuracy: float | None = None
    n_samples: int | None = None


class PredictResponse(BaseModel):
    request_id: int
    acceptance_probability: float


class AgentAskRequest(BaseModel):
    question: str
    # İlk soruda boş bırakılır (yeni konuşma), agent bir session_id üretir ve
    # cevapla birlikte döner. Sonraki sorularda aynı session_id gönderilirse,
    # agent önceki turları hafızasında tutar.
    session_id: str | None = None


class AgentAskResponse(BaseModel):
    answer: str
    session_id: str


class PaginatedFlightsOut(BaseModel):
    items: list[FlightOut]
    total: int


class PaginatedCargoRequestsOut(BaseModel):
    items: list[CargoRequestOut]
    total: int


class CapacityUtilizationOut(BaseModel):
    flight_id: int
    flight_number: str
    weight_utilization_pct: float
    volume_utilization_pct: float


class KpiTrendPointOut(BaseModel):
    period: str
    total_requests: int
    accepted_count: int
    rejected_count: int
    total_revenue: float
    acceptance_rate: float
    avg_weight_utilization_pct: float
    avg_volume_utilization_pct: float


class KpiTrendResponse(BaseModel):
    group_by: str
    points: list[KpiTrendPointOut]


class ScenarioSummaryOut(BaseModel):
    scenario_name: str
    total_requests: int
    accepted_count: int
    rejected_count: int
    total_revenue: float
    last_run_at: datetime


class PaginatedScenariosOut(BaseModel):
    items: list[ScenarioSummaryOut]
    total: int


class DatasetSummaryOut(BaseModel):
    airports_count: int
    aircraft_types_count: int
    routes_count: int
    flights_count: int
    cargo_requests_count: int
    optimization_results_count: int
    data_start: date | None
    data_end: date | None


class GenerateDemandResponse(BaseModel):
    generated_count: int
    flights_count: int
    pending_count: int
