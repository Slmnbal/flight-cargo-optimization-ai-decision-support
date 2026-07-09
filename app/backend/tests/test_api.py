"""
API katmanının (routes.py) CORS yapılandırmasını ve React frontend için eklenen
yeni endpoint'leri (aircraft-types, results, kpis) doğrular. `db_session` fixture'ı
(conftest.py) izole bir in-memory SQLite kullanıyor; FastAPI'nin `get_db`
dependency'sini bu session'ı döndürecek şekilde override ediyoruz ki testler gerçek
cargo.db dosyasına dokunmasın.
"""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.connection import get_db
from app.models import AircraftType, Route, Flight, CargoRequest, OptimizationResult


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_cors_allows_configured_frontend_origin(client):
    response = client.options(
        "/routes",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_get_aircraft_types_returns_seeded_rows(client, db_session):
    db_session.add(AircraftType(
        aircraft_type="TEST1", max_cargo_weight_kg=1000, max_cargo_volume_m3=10,
        temperature_controlled_capacity_kg=100, is_freighter=False, dangerous_goods_allowed=False,
    ))
    db_session.commit()

    response = client.get("/aircraft-types")

    assert response.status_code == 200
    assert response.json() == [{
        "aircraft_type": "TEST1",
        "max_cargo_weight_kg": 1000.0,
        "max_cargo_volume_m3": 10.0,
        "temperature_controlled_capacity_kg": 100.0,
        "is_freighter": False,
        "dangerous_goods_allowed": False,
    }]


def _seed_flight_with_requests(db):
    aircraft = AircraftType(
        aircraft_type="TEST1", max_cargo_weight_kg=1000, max_cargo_volume_m3=10,
        temperature_controlled_capacity_kg=0, is_freighter=False, dangerous_goods_allowed=False,
    )
    db.add(aircraft)
    db.commit()

    route = Route(
        origin_airport="AAA", destination_airport="BBB", distance_km=100,
        route_type="domestic", region="Test", customs_required=False,
        restricted_cargo_allowed=True, embargo_active=False, is_active=True,
    )
    db.add(route)
    db.commit()

    flight = Flight(
        flight_number="TT001", route_id=route.route_id, aircraft_type="TEST1",
        aircraft_registration="TEST-REG",
        departure_scheduled=datetime(2026, 1, 1, 10, 0), arrival_scheduled=datetime(2026, 1, 1, 12, 0),
        status="scheduled",
    )
    db.add(flight)
    db.commit()

    requests = [
        CargoRequest(flight_id=flight.flight_id, cargo_type="general", weight_kg=100, volume_m3=1, revenue=500, status="accepted"),
        CargoRequest(flight_id=flight.flight_id, cargo_type="dangerous_goods", weight_kg=100, volume_m3=1, revenue=300, status="rejected"),
    ]
    db.add_all(requests)
    db.commit()
    return requests


def test_get_results_returns_rows_for_scenario(client, db_session):
    requests = _seed_flight_with_requests(db_session)
    db_session.add_all([
        OptimizationResult(scenario_name="s1", request_id=requests[0].request_id, decision="accepted", revenue=500, reason=None),
        OptimizationResult(scenario_name="s1", request_id=requests[1].request_id, decision="rejected", revenue=0, reason="dangerous_goods_restricted"),
        OptimizationResult(scenario_name="other", request_id=requests[0].request_id, decision="accepted", revenue=500, reason=None),
    ])
    db_session.commit()

    response = client.get("/results/s1")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {r["decision"] for r in body} == {"accepted", "rejected"}


def test_get_kpis_returns_aggregated_summary(client, db_session):
    requests = _seed_flight_with_requests(db_session)
    db_session.add_all([
        OptimizationResult(scenario_name="s1", request_id=requests[0].request_id, decision="accepted", revenue=500, reason=None),
        OptimizationResult(scenario_name="s1", request_id=requests[1].request_id, decision="rejected", revenue=0, reason="dangerous_goods_restricted"),
    ])
    db_session.commit()

    response = client.get("/kpis/s1")

    assert response.status_code == 200
    body = response.json()
    assert body["total_requests"] == 2
    assert body["accepted_count"] == 1
    assert body["rejected_count"] == 1
    assert body["total_revenue"] == 500
    assert body["rejection_reason_breakdown"] == {"dangerous_goods_restricted": 1}


def test_get_kpis_404_for_unknown_scenario(client):
    response = client.get("/kpis/does-not-exist")
    assert response.status_code == 404
