import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import Route, Flight, CargoRequest
from app.schemas.schemas import (
    RouteOut,
    FlightOut,
    CargoRequestOut,
    OptimizeResponse,
    TrainResponse,
    PredictResponse,
    AgentAskRequest,
    AgentAskResponse,
)
from app.optimization.optimizer import run_optimization
from app.ml.demand_forecast import train_acceptance_model, load_model, predict_acceptance_probability
from app.agents.explainer import ask_agent

logger = logging.getLogger("cargo_api")
router = APIRouter()


@router.get("/routes", response_model=list[RouteOut])
def get_routes(db: Session = Depends(get_db)):
    return db.query(Route).all()


@router.get("/flights", response_model=list[FlightOut])
def get_flights(db: Session = Depends(get_db)):
    return db.query(Flight).all()


@router.get("/cargo-requests", response_model=list[CargoRequestOut])
def get_cargo_requests(db: Session = Depends(get_db)):
    return db.query(CargoRequest).all()


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
def agent_ask(payload: AgentAskRequest):
    try:
        answer = ask_agent(payload.question)
        return {"answer": answer}
    except Exception as exc:
        logger.exception("Agent failed")
        raise HTTPException(status_code=500, detail=str(exc))
