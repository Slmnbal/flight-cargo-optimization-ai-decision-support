import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import Route, Flight, CargoRequest
from app.schemas.schemas import RouteOut, FlightOut, CargoRequestOut, OptimizeResponse
from app.optimization.optimizer import run_optimization

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
