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
from app.models import AircraftType, Airport, Route, Flight, CargoRequest, OptimizationResult
from app.seed_data import WINDOW_END


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


def test_get_airports_returns_seeded_rows(client, db_session):
    db_session.add(Airport(
        airport_code="TST", airport_name="Test Airport", country="Testland",
        timezone="UTC", customs_available=True,
    ))
    db_session.commit()

    response = client.get("/airports")

    assert response.status_code == 200
    assert response.json() == [{
        "airport_code": "TST",
        "airport_name": "Test Airport",
        "country": "Testland",
        "timezone": "UTC",
        "customs_available": True,
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


def test_get_flights_returns_paginated_shape_and_respects_filters(client, db_session):
    _seed_flight_with_requests(db_session)

    response = client.get("/flights?limit=1")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"items", "total"}
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["flight_number"] == "TT001"

    # date_from/date_to filtresi: seed edilen uçuş 2026-01-01'de -- pencere
    # dışına düşen bir aralık boş sonuç döndürmeli.
    response = client.get("/flights?date_from=2027-01-01")
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_get_cargo_requests_returns_paginated_shape_and_respects_status_filter(client, db_session):
    _seed_flight_with_requests(db_session)

    response = client.get("/cargo-requests?status=accepted")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"items", "total"}
    assert body["total"] == 1
    assert body["items"][0]["status"] == "accepted"


def test_get_flight_capacity_utilization_returns_computed_percentages(client, db_session):
    requests = _seed_flight_with_requests(db_session)
    flight_id = requests[0].flight_id

    response = client.get(f"/flights/{flight_id}/capacity-utilization")

    assert response.status_code == 200
    body = response.json()
    # aircraft max_cargo_weight_kg=1000, tek accepted talep weight_kg=100 -> %10
    assert body["weight_utilization_pct"] == 10.0
    assert body["volume_utilization_pct"] == 10.0


def test_get_flight_capacity_utilization_404_for_unknown_flight(client):
    response = client.get("/flights/999999/capacity-utilization")
    assert response.status_code == 404


def test_get_kpi_trend_groups_by_day_and_computes_aggregates(client, db_session):
    requests = _seed_flight_with_requests(db_session)
    db_session.add_all([
        OptimizationResult(scenario_name="daily-2026-01-01", request_id=requests[0].request_id, decision="accepted", revenue=500, reason=None),
        OptimizationResult(scenario_name="daily-2026-01-01", request_id=requests[1].request_id, decision="rejected", revenue=0, reason="dangerous_goods_restricted"),
    ])
    db_session.commit()

    response = client.get("/kpis/trend?group_by=day")

    assert response.status_code == 200
    body = response.json()
    assert body["group_by"] == "day"
    assert len(body["points"]) == 1
    point = body["points"][0]
    assert point["period"] == "2026-01-01"
    assert point["total_requests"] == 2
    assert point["accepted_count"] == 1
    assert point["rejected_count"] == 1
    assert point["total_revenue"] == 500
    assert point["acceptance_rate"] == 0.5


def test_get_kpi_trend_route_not_shadowed_by_scenario_name_path(client):
    # /kpis/trend, /kpis/{scenario_name}'den ÖNCE eşleşmeli -- aksi halde
    # "trend" bir scenario_name olarak yorumlanır ve 404 döner.
    response = client.get("/kpis/trend")
    assert response.status_code == 200
    assert response.json() == {"group_by": "day", "points": []}


def test_get_scenarios_returns_paginated_summaries_sorted_by_most_recent(client, db_session):
    requests = _seed_flight_with_requests(db_session)
    db_session.add_all([
        OptimizationResult(
            scenario_name="daily-2026-01-01", request_id=requests[0].request_id, decision="accepted",
            revenue=500, reason=None, run_at=datetime(2026, 1, 1, 23, 0),
        ),
        OptimizationResult(
            scenario_name="daily-2026-01-01", request_id=requests[1].request_id, decision="rejected",
            revenue=0, reason="dangerous_goods_restricted", run_at=datetime(2026, 1, 1, 23, 0),
        ),
        OptimizationResult(
            scenario_name="daily-2026-01-02", request_id=requests[0].request_id, decision="accepted",
            revenue=500, reason=None, run_at=datetime(2026, 1, 2, 23, 0),
        ),
    ])
    db_session.commit()

    response = client.get("/scenarios")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    # en son çalışan senaryo (daily-2026-01-02) ilk sırada olmalı
    assert [item["scenario_name"] for item in body["items"]] == ["daily-2026-01-02", "daily-2026-01-01"]
    first = body["items"][0]
    assert first["total_requests"] == 1
    assert first["accepted_count"] == 1
    assert first["total_revenue"] == 500

    second = body["items"][1]
    assert second["total_requests"] == 2
    assert second["accepted_count"] == 1
    assert second["rejected_count"] == 1


def test_get_scenarios_respects_limit_and_offset(client, db_session):
    requests = _seed_flight_with_requests(db_session)
    db_session.add_all([
        OptimizationResult(
            scenario_name=f"daily-2026-01-{day:02d}", request_id=requests[0].request_id, decision="accepted",
            revenue=100, reason=None, run_at=datetime(2026, 1, day, 23, 0),
        )
        for day in range(1, 6)
    ])
    db_session.commit()

    response = client.get("/scenarios?limit=2&offset=1")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert [item["scenario_name"] for item in body["items"]] == ["daily-2026-01-04", "daily-2026-01-03"]


def test_get_dataset_summary_returns_counts_and_date_range(client, db_session):
    _seed_flight_with_requests(db_session)

    response = client.get("/dataset/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["aircraft_types_count"] == 1
    assert body["routes_count"] == 1
    assert body["flights_count"] == 1
    assert body["cargo_requests_count"] == 2
    assert body["data_start"] == "2026-01-01"
    assert body["data_end"] == "2026-01-01"


def test_get_dataset_summary_handles_empty_database(client):
    response = client.get("/dataset/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["flights_count"] == 0
    assert body["data_start"] is None
    assert body["data_end"] is None


def test_generate_demand_adds_pending_requests_for_last_day_flights(client, db_session):
    aircraft = AircraftType(
        aircraft_type="TEST1", max_cargo_weight_kg=1000, max_cargo_volume_m3=10,
        temperature_controlled_capacity_kg=0, is_freighter=False, dangerous_goods_allowed=False,
    )
    db_session.add(aircraft)
    db_session.commit()
    route = Route(
        origin_airport="AAA", destination_airport="BBB", distance_km=100,
        route_type="domestic", region="Turkey", customs_required=False,
        restricted_cargo_allowed=True, embargo_active=False, is_active=True,
    )
    db_session.add(route)
    db_session.commit()
    # WINDOW_END'den ÖNCEKİ bir uçuş -- "bugün" sayılmamalı, generate-demand'a dahil edilmemeli.
    old_flight = Flight(
        flight_number="OLD1", route_id=route.route_id, aircraft_type="TEST1",
        departure_scheduled=WINDOW_END.replace(year=WINDOW_END.year - 1),
        arrival_scheduled=WINDOW_END.replace(year=WINDOW_END.year - 1),
        status="completed",
    )
    # WINDOW_END'e eşit/sonraki bir uçuş -- "bugün" sayılmalı.
    today_flight = Flight(
        flight_number="NEW1", route_id=route.route_id, aircraft_type="TEST1",
        departure_scheduled=WINDOW_END, arrival_scheduled=WINDOW_END,
        status="scheduled",
    )
    db_session.add_all([old_flight, today_flight])
    db_session.commit()

    response = client.post("/dataset/generate-demand")

    assert response.status_code == 200
    body = response.json()
    assert body["flights_count"] == 1  # sadece today_flight
    assert body["generated_count"] >= 10  # random_request 10-18 arası üretir
    assert body["pending_count"] == body["generated_count"]

    generated = db_session.query(CargoRequest).filter(CargoRequest.flight_id == today_flight.flight_id).all()
    assert len(generated) == body["generated_count"]
    assert all(r.status == "pending" for r in generated)


def test_generate_demand_404_when_no_flights_in_window(client):
    response = client.post("/dataset/generate-demand")
    assert response.status_code == 404
