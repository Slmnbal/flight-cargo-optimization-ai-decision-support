from datetime import datetime
from pydantic import BaseModel


class RouteOut(BaseModel):
    route_id: int
    origin_airport: str
    destination_airport: str
    distance_km: float
    route_type: str
    region: str
    is_active: bool

    class Config:
        from_attributes = True


class FlightOut(BaseModel):
    flight_id: int
    flight_number: str
    route_id: int
    aircraft_type: str
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
    priority_class: str
    revenue: float
    status: str

    class Config:
        from_attributes = True


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
