"""
AI Agent'a yeni eklenen tool'ların GERÇEK mantığını test eder -- Gemini
çağrısı yapılmıyor (mevcut test felsefesiyle tutarlı, bkz. test_agent_memory.py).
Tool'ların çoğu kendi SessionLocal()'ını açtığı için (gerçek cargo.db'ye bağlı,
testte izole edilemez), test edilebilirlik için db/model enjekte edilebilen
private yardımcılar (_capacity_utilization'daki gibi) üzerinden test ediliyor:
analytics_service.* fonksiyonları ve agents.tools._aircraft_type_specs /
_restricted_routes / _predict_for_request.
"""
from datetime import datetime

from app.agents.tools import _aircraft_type_specs, _predict_for_request, _restricted_routes
from app.models import AircraftType, CargoRequest, Flight, OptimizationResult, Route
from app.services import analytics_service


def _seed_route_with_history(db, *, embargo_active=False, restricted_cargo_allowed=True):
    aircraft = AircraftType(
        aircraft_type="TEST1", max_cargo_weight_kg=1000, max_cargo_volume_m3=10,
        temperature_controlled_capacity_kg=0, is_freighter=False, dangerous_goods_allowed=False,
    )
    db.add(aircraft)
    db.commit()

    route = Route(
        origin_airport="AAA", destination_airport="BBB", distance_km=100,
        route_type="domestic", region="Test", customs_required=False,
        restricted_cargo_allowed=restricted_cargo_allowed, embargo_active=embargo_active,
        embargoed_cargo_types="live_animal" if embargo_active else None, is_active=True,
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

    db.add_all([
        OptimizationResult(scenario_name="s1", request_id=requests[0].request_id, decision="accepted", revenue=500, reason=None),
        OptimizationResult(scenario_name="s1", request_id=requests[1].request_id, decision="rejected", revenue=0, reason="dangerous_goods_restricted"),
    ])
    db.commit()

    return route, flight, requests


def test_get_route_statistics_aggregates_history_for_matching_route(db_session):
    _seed_route_with_history(db_session)

    stats = analytics_service.get_route_statistics(db_session, "AAA", "BBB")

    assert stats is not None
    assert stats["origin_airport"] == "AAA"
    assert stats["total_requests"] == 2
    assert stats["accepted_count"] == 1
    assert stats["rejected_count"] == 1
    assert stats["total_revenue"] == 500
    assert stats["rejection_reason_breakdown"] == {"dangerous_goods_restricted": 1}


def test_get_route_statistics_is_case_insensitive_and_none_for_unknown_route(db_session):
    _seed_route_with_history(db_session)

    assert analytics_service.get_route_statistics(db_session, "aaa", "bbb") is not None
    assert analytics_service.get_route_statistics(db_session, "ZZZ", "YYY") is None


def test_get_top_routes_by_revenue_ranks_descending(db_session):
    _seed_route_with_history(db_session)  # AAA->BBB: 500 kabul edilen gelir

    aircraft = AircraftType(
        aircraft_type="TEST2", max_cargo_weight_kg=1000, max_cargo_volume_m3=10,
        temperature_controlled_capacity_kg=0, is_freighter=False, dangerous_goods_allowed=False,
    )
    db_session.add(aircraft)
    db_session.commit()
    route2 = Route(
        origin_airport="CCC", destination_airport="DDD", distance_km=200,
        route_type="domestic", region="Test", customs_required=False,
        restricted_cargo_allowed=True, embargo_active=False, is_active=True,
    )
    db_session.add(route2)
    db_session.commit()
    flight2 = Flight(
        flight_number="TT002", route_id=route2.route_id, aircraft_type="TEST2",
        departure_scheduled=datetime(2026, 1, 1, 10, 0), arrival_scheduled=datetime(2026, 1, 1, 12, 0),
        status="scheduled",
    )
    db_session.add(flight2)
    db_session.commit()
    req2 = CargoRequest(flight_id=flight2.flight_id, cargo_type="general", weight_kg=100, volume_m3=1, revenue=9000, status="accepted")
    db_session.add(req2)
    db_session.commit()
    db_session.add(OptimizationResult(scenario_name="s1", request_id=req2.request_id, decision="accepted", revenue=9000, reason=None))
    db_session.commit()

    ranked = analytics_service.get_top_routes_by_revenue(db_session, limit=5)

    assert [r["origin_airport"] for r in ranked[:2]] == ["CCC", "AAA"]
    assert ranked[0]["total_revenue"] == 9000
    assert ranked[1]["total_revenue"] == 500


def test_aircraft_type_specs_found_and_not_found(db_session):
    db_session.add(AircraftType(
        aircraft_type="A330-200F", max_cargo_weight_kg=70000, max_cargo_volume_m3=470,
        temperature_controlled_capacity_kg=15000, is_freighter=True, dangerous_goods_allowed=True,
    ))
    db_session.commit()

    specs = _aircraft_type_specs(db_session, "A330-200F")
    assert specs["max_cargo_weight_kg"] == 70000
    assert specs["is_freighter"] is True

    assert "error" in _aircraft_type_specs(db_session, "NOPE")


def test_restricted_routes_returns_only_embargoed_or_restricted(db_session):
    db_session.add_all([
        Route(origin_airport="A1", destination_airport="A2", distance_km=1, route_type="d", region="r",
              customs_required=False, restricted_cargo_allowed=True, embargo_active=True, embargoed_cargo_types="live_animal", is_active=True),
        Route(origin_airport="B1", destination_airport="B2", distance_km=1, route_type="d", region="r",
              customs_required=False, restricted_cargo_allowed=False, embargo_active=False, is_active=True),
        Route(origin_airport="C1", destination_airport="C2", distance_km=1, route_type="d", region="r",
              customs_required=False, restricted_cargo_allowed=True, embargo_active=False, is_active=True),
    ])
    db_session.commit()

    restricted = _restricted_routes(db_session)

    assert {r["origin_airport"] for r in restricted} == {"A1", "B1"}


class _FakeModel:
    """predict_proba, gerçek sklearn modeliyle aynı şekli (2 sınıflı olasılık
    matrisi) döndüren sahte bir model -- testte gerçek bir model eğitmeye
    gerek kalmadan _predict_for_request'in davranışını doğrular."""

    def predict_proba(self, df):
        return [[0.35, 0.65] for _ in range(len(df))]


def test_predict_for_request_returns_probability(db_session):
    _, _, requests = _seed_route_with_history(db_session)

    result = _predict_for_request(db_session, _FakeModel(), requests[0].request_id)

    assert result["request_id"] == requests[0].request_id
    assert result["acceptance_probability"] == 0.65


def test_predict_for_request_unknown_request_id(db_session):
    result = _predict_for_request(db_session, _FakeModel(), 999999)
    assert "error" in result
