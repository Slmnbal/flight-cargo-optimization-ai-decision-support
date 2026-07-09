"""
Cargo kabul/red kararı veren optimizasyon motoru.

Karar değişkeni: x_i = 1 ise talep kabul edilir, 0 ise reddedilir.
Amaç fonksiyonu: maximize sum(revenue_i * x_i)
Kısıtlar: her uçuş için toplam ağırlık ve hacim, o uçağın kapasitesini aşamaz.
"""
import shutil
from collections import defaultdict

import pulp
from sqlalchemy.orm import Session

from app.models import CargoRequest, Flight, AircraftType, OptimizationResult


def run_optimization(db: Session, scenario_name: str = "default") -> dict:
    requests = db.query(CargoRequest).filter(CargoRequest.status == "pending").all()

    if not requests:
        return {"status": "no_pending_requests", "accepted": [], "rejected": [], "total_revenue": 0.0}

    # N+1 query'den kaçınmak için: önce bu taleplerin kapsadığı benzersiz uçuş id'lerini
    # bul, her uçuş için TEK sorgu at (talep sayısı kadar değil).
    unique_flight_ids = {req.flight_id for req in requests}
    flight_capacity = {}
    for flight_id in unique_flight_ids:
        flight = db.query(Flight).filter(Flight.flight_id == flight_id).first()
        aircraft = (
            db.query(AircraftType)
            .filter(AircraftType.aircraft_type == flight.aircraft_type)
            .first()
        )
        flight_capacity[flight_id] = {
            "max_weight": aircraft.max_cargo_weight_kg,
            "max_volume": aircraft.max_cargo_volume_m3,
        }

    problem = pulp.LpProblem("cargo_acceptance", pulp.LpMaximize)

    x = {req.request_id: pulp.LpVariable(f"x_{req.request_id}", cat="Binary") for req in requests}

    problem += pulp.lpSum(req.revenue * x[req.request_id] for req in requests)

    by_flight = defaultdict(list)
    for req in requests:
        by_flight[req.flight_id].append(req)

    for flight_id, reqs in by_flight.items():
        cap = flight_capacity[flight_id]
        problem += pulp.lpSum(r.weight_kg * x[r.request_id] for r in reqs) <= cap["max_weight"]
        problem += pulp.lpSum(r.volume_m3 * x[r.request_id] for r in reqs) <= cap["max_volume"]

    # Bazı mimarilerde (özellikle Apple Silicon Mac) PuLP'nin paket içine gömülü CBC
    # ikili dosyası çalışmayabilir ("Bad CPU type"). Önce sistemde kurulu bir CBC var mı
    # diye bakıyoruz (örn. `brew install cbc`), varsa onu kullanıyoruz; yoksa PuLP'nin
    # kendi bundled sürümüne düşüyoruz. Bu, kodun farklı işletim sistemi/mimarilerde
    # değişiklik yapmadan çalışmasını sağlıyor.
    system_cbc_path = shutil.which("cbc")
    solver = pulp.COIN_CMD(msg=False, path=system_cbc_path) if system_cbc_path else pulp.PULP_CBC_CMD(msg=False)
    problem.solve(solver)

    accepted, rejected = [], []
    for req in requests:
        decision = "accepted" if x[req.request_id].value() == 1 else "rejected"
        req.status = decision
        (accepted if decision == "accepted" else rejected).append(req.request_id)

        db.add(
            OptimizationResult(
                scenario_name=scenario_name,
                request_id=req.request_id,
                decision=decision,
                revenue=req.revenue if decision == "accepted" else 0.0,
            )
        )

    db.commit()

    total_revenue = sum(r.revenue for r in requests if r.status == "accepted")

    return {
        "status": pulp.LpStatus[problem.status],
        "accepted": accepted,
        "rejected": rejected,
        "total_revenue": total_revenue,
    }
