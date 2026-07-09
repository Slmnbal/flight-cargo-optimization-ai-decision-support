"""
Optimizasyon motorunun testleri. Amaç sadece "hata vermeden çalışıyor mu" değil,
matematiksel olarak DOĞRU kararı verip vermediğini kontrol etmek — bir solver'ın
en büyük riski, sessizce yanlış (optimal olmayan) bir sonuç üretmesidir.
"""
from datetime import datetime

from app.models import AircraftType, Route, Flight, CargoRequest
from app.optimization.optimizer import run_optimization


def _seed_minimal_scenario(db):
    """3 kargo talebi olan, kapasitesi kasıtlı olarak dar tutulmuş tek uçuşluk basit bir senaryo kurar."""
    aircraft = AircraftType(
        aircraft_type="TEST1",
        max_cargo_weight_kg=1000,
        max_cargo_volume_m3=10,
        temperature_controlled_capacity_kg=0,
        is_freighter=False,
        dangerous_goods_allowed=False,
    )
    db.add(aircraft)
    db.commit()

    route = Route(
        origin_airport="AAA",
        destination_airport="BBB",
        distance_km=100,
        route_type="domestic",
        region="Test",
        customs_required=False,
        restricted_cargo_allowed=True,
        embargo_active=False,
        is_active=True,
    )
    db.add(route)
    db.commit()

    flight = Flight(
        flight_number="TT001",
        route_id=route.route_id,
        aircraft_type="TEST1",
        aircraft_registration="TEST-REG",
        departure_scheduled=datetime(2026, 1, 1, 10, 0),
        arrival_scheduled=datetime(2026, 1, 1, 12, 0),
        status="scheduled",
    )
    db.add(flight)
    db.commit()

    # Kapasite 1000 kg. Her talep 400 kg -> aynı anda en fazla 2 tanesi kabul edilebilir.
    # Doğru (optimal) karar: en yüksek gelirli iki talebi (1000 ve 800) kabul etmek,
    # en düşük gelirliyi (500) reddetmek.
    requests = [
        CargoRequest(flight_id=flight.flight_id, cargo_type="general", weight_kg=400, volume_m3=4, revenue=1000, status="pending"),
        CargoRequest(flight_id=flight.flight_id, cargo_type="general", weight_kg=400, volume_m3=4, revenue=800, status="pending"),
        CargoRequest(flight_id=flight.flight_id, cargo_type="general", weight_kg=400, volume_m3=4, revenue=500, status="pending"),
    ]
    db.add_all(requests)
    db.commit()
    return requests


def test_optimizer_picks_highest_revenue_combination_within_capacity(db_session):
    requests = _seed_minimal_scenario(db_session)

    result = run_optimization(db_session, scenario_name="pytest_scenario")

    assert result["status"] == "Optimal"
    assert len(result["accepted"]) == 2

    accepted_revenues = sorted(r.revenue for r in requests if r.request_id in result["accepted"])
    assert accepted_revenues == [800, 1000]
    assert result["total_revenue"] == 1800


def test_optimizer_handles_no_pending_requests(db_session):
    result = run_optimization(db_session, scenario_name="empty_scenario")
    assert result["status"] == "no_pending_requests"
    assert result["accepted"] == []
