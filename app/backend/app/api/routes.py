import logging
from collections import Counter
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import Route, Flight, CargoRequest, AircraftType, OptimizationResult
from app.schemas.schemas import (
    RouteOut,
    FlightOut,
    CargoRequestOut,
    AircraftTypeOut,
    OptimizationResultOut,
    KpiSummaryOut,
    OptimizeResponse,
    TrainResponse,
    PredictResponse,
    AgentAskRequest,
    AgentAskResponse,
    PaginatedFlightsOut,
    PaginatedCargoRequestsOut,
    CapacityUtilizationOut,
    KpiTrendResponse,
)
from app.optimization.optimizer import run_optimization
from app.ml.demand_forecast import train_acceptance_model, load_model, predict_acceptance_probability
from app.agents.explainer import ask_agent
from app.agents.tools import _capacity_utilization

logger = logging.getLogger("cargo_api")
router = APIRouter()


@router.get("/routes", response_model=list[RouteOut])
def get_routes(db: Session = Depends(get_db)):
    return db.query(Route).all()


@router.get("/flights", response_model=PaginatedFlightsOut)
def get_flights(
    date_from: date | None = None,
    date_to: date | None = None,
    route_id: int | None = None,
    status: str | None = None,
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Flight)
    if date_from is not None:
        query = query.filter(Flight.departure_scheduled >= datetime.combine(date_from, time.min))
    if date_to is not None:
        query = query.filter(Flight.departure_scheduled < datetime.combine(date_to, time.min) + timedelta(days=1))
    if route_id is not None:
        query = query.filter(Flight.route_id == route_id)
    if status is not None:
        query = query.filter(Flight.status == status)

    total = query.count()
    items = query.order_by(Flight.departure_scheduled.desc()).offset(offset).limit(limit).all()
    return {"items": items, "total": total}


@router.get("/flights/{flight_id}/capacity-utilization", response_model=CapacityUtilizationOut)
def get_flight_capacity_utilization(flight_id: int, db: Session = Depends(get_db)):
    result = _capacity_utilization(db, flight_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/cargo-requests", response_model=PaginatedCargoRequestsOut)
def get_cargo_requests(
    flight_id: int | None = None,
    cargo_type: str | None = None,
    priority_class: str | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(CargoRequest)
    if flight_id is not None:
        query = query.filter(CargoRequest.flight_id == flight_id)
    if cargo_type is not None:
        query = query.filter(CargoRequest.cargo_type == cargo_type)
    if priority_class is not None:
        query = query.filter(CargoRequest.priority_class == priority_class)
    if status is not None:
        query = query.filter(CargoRequest.status == status)
    if date_from is not None or date_to is not None:
        query = query.join(Flight, Flight.flight_id == CargoRequest.flight_id)
        if date_from is not None:
            query = query.filter(Flight.departure_scheduled >= datetime.combine(date_from, time.min))
        if date_to is not None:
            query = query.filter(Flight.departure_scheduled < datetime.combine(date_to, time.min) + timedelta(days=1))

    total = query.count()
    items = query.order_by(CargoRequest.request_id.desc()).offset(offset).limit(limit).all()
    return {"items": items, "total": total}


@router.get("/aircraft-types", response_model=list[AircraftTypeOut])
def get_aircraft_types(db: Session = Depends(get_db)):
    return db.query(AircraftType).all()


@router.get("/results/{scenario_name}", response_model=list[OptimizationResultOut])
def get_results(scenario_name: str, db: Session = Depends(get_db)):
    return (
        db.query(OptimizationResult)
        .filter(OptimizationResult.scenario_name == scenario_name)
        .order_by(OptimizationResult.run_at.desc())
        .all()
    )


@router.get("/kpis/trend", response_model=KpiTrendResponse)
def get_kpi_trend(
    start_date: date | None = None,
    end_date: date | None = None,
    group_by: str = Query("day", pattern="^(day|week|month)$"),
    db: Session = Depends(get_db),
):
    """
    Dönem bazlı (gün/hafta/ay) gelir, kabul/red ve ortalama kapasite kullanım
    trendini döndürür -- OverviewPage'in trend grafiği için. Not: bu endpoint
    /kpis/{scenario_name}'den ÖNCE tanımlanmalı, aksi halde FastAPI "trend"i
    bir scenario_name olarak eşleştirir (path parametreli route'lar ilk eşleşen
    kazanır).
    """
    query = (
        db.query(OptimizationResult, CargoRequest, Flight, AircraftType)
        .join(CargoRequest, OptimizationResult.request_id == CargoRequest.request_id)
        .join(Flight, CargoRequest.flight_id == Flight.flight_id)
        .join(AircraftType, Flight.aircraft_type == AircraftType.aircraft_type)
    )
    if start_date is not None:
        query = query.filter(Flight.departure_scheduled >= datetime.combine(start_date, time.min))
    if end_date is not None:
        query = query.filter(Flight.departure_scheduled < datetime.combine(end_date, time.min) + timedelta(days=1))

    def period_key(dep: datetime) -> str:
        if group_by == "day":
            return dep.date().isoformat()
        if group_by == "week":
            iso_year, iso_week, _ = dep.isocalendar()
            return f"{iso_year}-W{iso_week:02d}"
        return f"{dep.year}-{dep.month:02d}"

    buckets: dict[str, dict] = {}
    for result, cargo_request, flight, aircraft in query.all():
        key = period_key(flight.departure_scheduled)
        bucket = buckets.setdefault(key, {
            "total_requests": 0, "accepted_count": 0, "rejected_count": 0,
            "total_revenue": 0.0, "accepted_weight_kg": 0.0, "accepted_volume_m3": 0.0,
            "capacity_weight_kg": 0.0, "capacity_volume_m3": 0.0, "seen_flight_ids": set(),
        })
        bucket["total_requests"] += 1
        if result.decision == "accepted":
            bucket["accepted_count"] += 1
            bucket["total_revenue"] += result.revenue
            bucket["accepted_weight_kg"] += cargo_request.weight_kg
            bucket["accepted_volume_m3"] += cargo_request.volume_m3
        else:
            bucket["rejected_count"] += 1
        if flight.flight_id not in bucket["seen_flight_ids"]:
            bucket["seen_flight_ids"].add(flight.flight_id)
            bucket["capacity_weight_kg"] += aircraft.max_cargo_weight_kg
            bucket["capacity_volume_m3"] += aircraft.max_cargo_volume_m3

    points = []
    for period in sorted(buckets):
        b = buckets[period]
        total = b["total_requests"]
        points.append({
            "period": period,
            "total_requests": total,
            "accepted_count": b["accepted_count"],
            "rejected_count": b["rejected_count"],
            "total_revenue": round(b["total_revenue"], 2),
            "acceptance_rate": round(b["accepted_count"] / total, 4) if total else 0.0,
            "avg_weight_utilization_pct": round(100 * b["accepted_weight_kg"] / b["capacity_weight_kg"], 1) if b["capacity_weight_kg"] else 0.0,
            "avg_volume_utilization_pct": round(100 * b["accepted_volume_m3"] / b["capacity_volume_m3"], 1) if b["capacity_volume_m3"] else 0.0,
        })

    return {"group_by": group_by, "points": points}


@router.get("/kpis/{scenario_name}", response_model=KpiSummaryOut)
def get_kpis(scenario_name: str, db: Session = Depends(get_db)):
    rows = db.query(OptimizationResult).filter(OptimizationResult.scenario_name == scenario_name).all()
    if not rows:
        raise HTTPException(status_code=404, detail="Bu senaryo için sonuç bulunamadı.")

    accepted = [r for r in rows if r.decision == "accepted"]
    rejected = [r for r in rows if r.decision == "rejected"]
    reason_breakdown = Counter(r.reason for r in rejected if r.reason)

    return {
        "scenario_name": scenario_name,
        "total_requests": len(rows),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "total_revenue": sum(r.revenue for r in accepted),
        "rejection_reason_breakdown": dict(reason_breakdown),
        "last_run_at": max(r.run_at for r in rows),
    }


@router.post("/optimize", response_model=OptimizeResponse)
def optimize(scenario_name: str = "default", db: Session = Depends(get_db)):
    try:
        result = run_optimization(db, scenario_name=scenario_name)
        logger.info("Optimization run '%s': %s", scenario_name, result["status"])
        return result
    except Exception as exc:
        logger.exception("Optimization failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ml/train", response_model=TrainResponse)
def train_ml_model(db: Session = Depends(get_db)):
    model, info = train_acceptance_model(db)
    if model is None:
        # info burada bir hata mesajı (string) - yeterli veri yoktu
        return {"trained": False, "detail": info}
    return {"trained": True, "detail": "Model başarıyla eğitildi.", **info}


@router.get("/ml/predict/{request_id}", response_model=PredictResponse)
def predict_ml(request_id: int, db: Session = Depends(get_db)):
    model = load_model()
    if model is None:
        raise HTTPException(status_code=400, detail="Model henüz eğitilmedi. Önce /ml/train çağır.")

    request = db.query(CargoRequest).filter(CargoRequest.request_id == request_id).first()
    if request is None:
        raise HTTPException(status_code=404, detail="Bu request_id bulunamadı.")

    probability = predict_acceptance_probability(
        model, request.weight_kg, request.volume_m3, request.revenue
    )
    return {"request_id": request_id, "acceptance_probability": probability}


@router.post("/agent/ask", response_model=AgentAskResponse)
def agent_ask(payload: AgentAskRequest, db: Session = Depends(get_db)):
    try:
        answer, session_id = ask_agent(db, payload.question, payload.session_id)
        return {"answer": answer, "session_id": session_id}
    except Exception as exc:
        logger.exception("Agent failed")
        raise HTTPException(status_code=500, detail=str(exc))
