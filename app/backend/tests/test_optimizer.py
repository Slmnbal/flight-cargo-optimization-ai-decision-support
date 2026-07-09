"""
Optimizasyon motorunun testleri. Amaç sadece "hata vermeden çalışıyor mu" değil,
matematiksel olarak DOĞRU kararı verip vermediğini kontrol etmek — bir solver'ın
en büyük riski, sessizce yanlış (optimal olmayan) bir sonuç üretmesidir.
"""
from datetime import datetime

from app.models import AircraftType, Route, Flight, CargoRequest, OptimizationResult
from app.optimization.optimizer import run_optimization


def _seed_scenario(db, aircraft_kwargs=None, route_kwargs=None, request_specs=None):
    """
    Tek uçuşluk, tüm alanları kontrol edilebilir bir senaryo kurar. aircraft_kwargs /
    route_kwargs ile varsayılanlar üzerine yazılır, request_specs ile istenen sayı ve
    özellikte CargoRequest üretilir. Her yeni kısıt testi kendi senaryosunu, hangi
    alanların önemli olduğunu açıkça göstererek kurabilsin diye bu şekilde genelleştirildi.
    """
    aircraft_defaults = dict(
        aircraft_type="TEST1",
        max_cargo_weight_kg=1000,
        max_cargo_volume_m3=10,
        temperature_controlled_capacity_kg=0,
        is_freighter=False,
        dangerous_goods_allowed=False,
    )
    aircraft_defaults.update(aircraft_kwargs or {})
    aircraft = AircraftType(**aircraft_defaults)
    db.add(aircraft)
    db.commit()

    route_defaults = dict(
        origin_airport="AAA",
        destination_airport="BBB",
        distance_km=100,
        route_type="domestic",
        region="Test",
        customs_required=False,
        restricted_cargo_allowed=True,
        embargo_active=False,
        embargoed_cargo_types=None,
        is_active=True,
    )
    route_defaults.update(route_kwargs or {})
    route = Route(**route_defaults)
    db.add(route)
    db.commit()

    flight = Flight(
        flight_number="TT001",
        route_id=route.route_id,
        aircraft_type=aircraft.aircraft_type,
        aircraft_registration="TEST-REG",
        departure_scheduled=datetime(2026, 1, 1, 10, 0),
        arrival_scheduled=datetime(2026, 1, 1, 12, 0),
        status="scheduled",
    )
    db.add(flight)
    db.commit()

    requests = []
    for spec in request_specs or []:
        defaults = dict(
            flight_id=flight.flight_id,
            cargo_type="general",
            weight_kg=100,
            volume_m3=1,
            requires_temperature_control=False,
            priority_class="spot",
            revenue=100,
            booking_cutoff_hours=24,
            status="pending",
        )
        defaults.update(spec)
        requests.append(CargoRequest(**defaults))
    db.add_all(requests)
    db.commit()
    return flight, requests


def _status_by_revenue(requests, revenue):
    return next(r for r in requests if r.revenue == revenue).status


def test_optimizer_picks_highest_revenue_combination_within_capacity(db_session):
    # Kapasite 1000 kg. Her talep 400 kg -> aynı anda en fazla 2 tanesi kabul edilebilir.
    # Doğru (optimal) karar: en yüksek gelirli iki talebi (1000 ve 800) kabul etmek,
    # en düşük gelirliyi (500) reddetmek. priority_class="contract" veriyoruz ki bu saf
    # ağırlık-kapasitesi testi, reserved-capacity kısıtından (bkz. test_priority_*)
    # etkilenmesin -- ikisi birbirinden bağımsız test edilmeli.
    _, requests = _seed_scenario(
        db_session,
        request_specs=[
            dict(weight_kg=400, volume_m3=4, revenue=1000, priority_class="contract"),
            dict(weight_kg=400, volume_m3=4, revenue=800, priority_class="contract"),
            dict(weight_kg=400, volume_m3=4, revenue=500, priority_class="contract"),
        ],
    )

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


def test_cold_chain_capacity_forces_reject(db_session):
    # Genel ağırlık kapasitesi bol (10000 kg) ama soğuk zincir kapasitesi dar (500 kg).
    # İki soğuk-zincir talebi birlikte (300+300=600) soğuk zincir kapasitesini aşıyor,
    # oysa genel ağırlık kapasitesi ikisine de rahatça yeter -- bu, soğuk zincir
    # kısıtının genel ağırlık kısıtından BAĞIMSIZ çalıştığını izole eden bir senaryo.
    _, requests = _seed_scenario(
        db_session,
        aircraft_kwargs=dict(max_cargo_weight_kg=10000, temperature_controlled_capacity_kg=500),
        request_specs=[
            dict(weight_kg=300, requires_temperature_control=True, revenue=1000),
            dict(weight_kg=300, requires_temperature_control=True, revenue=800),
        ],
    )

    result = run_optimization(db_session, scenario_name="cold_chain_test")

    assert len(result["accepted"]) == 1
    assert _status_by_revenue(requests, 1000) == "accepted"
    assert _status_by_revenue(requests, 800) == "rejected"


def test_embargo_cargo_type_specific_rejects_only_that_type(db_session):
    _, requests = _seed_scenario(
        db_session,
        route_kwargs=dict(embargo_active=True, embargoed_cargo_types="live_animal"),
        request_specs=[
            dict(cargo_type="live_animal", weight_kg=100, revenue=1000),
            dict(cargo_type="general", weight_kg=100, revenue=500),
        ],
    )

    result = run_optimization(db_session, scenario_name="embargo_specific_test")

    assert _status_by_revenue(requests, 1000) == "rejected"
    assert _status_by_revenue(requests, 500) == "accepted"

    reason = (
        db_session.query(OptimizationResult)
        .filter(OptimizationResult.request_id == requests[0].request_id)
        .first()
        .reason
    )
    assert reason == "embargo"


def test_embargo_blanket_rejects_all_cargo_types(db_session):
    # embargoed_cargo_types boş/None -> embargo_active=True TÜM kargo tiplerini kapsar.
    _, requests = _seed_scenario(
        db_session,
        route_kwargs=dict(embargo_active=True, embargoed_cargo_types=None),
        request_specs=[
            dict(cargo_type="live_animal", weight_kg=100, revenue=1000),
            dict(cargo_type="general", weight_kg=100, revenue=500),
        ],
    )

    run_optimization(db_session, scenario_name="embargo_blanket_test")

    assert _status_by_revenue(requests, 1000) == "rejected"
    assert _status_by_revenue(requests, 500) == "rejected"


def test_dangerous_goods_blocked_by_route_restriction(db_session):
    _, requests = _seed_scenario(
        db_session,
        aircraft_kwargs=dict(dangerous_goods_allowed=True),
        route_kwargs=dict(restricted_cargo_allowed=False),
        request_specs=[dict(cargo_type="dangerous_goods", weight_kg=100, revenue=1000)],
    )

    run_optimization(db_session, scenario_name="dg_route_test")

    assert requests[0].status == "rejected"
    reason = db_session.query(OptimizationResult).filter(
        OptimizationResult.request_id == requests[0].request_id
    ).first().reason
    assert reason == "dangerous_goods_restricted"


def test_dangerous_goods_blocked_by_aircraft_incapability(db_session):
    _, requests = _seed_scenario(
        db_session,
        aircraft_kwargs=dict(dangerous_goods_allowed=False),
        route_kwargs=dict(restricted_cargo_allowed=True),
        request_specs=[dict(cargo_type="dangerous_goods", weight_kg=100, revenue=1000)],
    )

    run_optimization(db_session, scenario_name="dg_aircraft_test")

    assert requests[0].status == "rejected"


def test_priority_reserved_capacity_protects_contract_cargo(db_session):
    # Kapasite 1000 kg, RESERVE_PCT=0.30 -> spot talepler tek başına en fazla 700 kg
    # taşıyabilir. Tek bir spot talebi 800 kg -> weight kapasitesine (1000) rahatça
    # sığar ama reserved-capacity kısıtına (700) sığmaz -> sadece bu kısıt yüzünden
    # reddedilir. Bu, reserved-capacity kısıtının genel ağırlık kısıtından bağımsız
    # çalıştığını izole eden bir senaryo. Contract talebi (200 kg) her koşulda sığar.
    _, requests = _seed_scenario(
        db_session,
        request_specs=[
            dict(priority_class="spot", weight_kg=800, revenue=5000),
            dict(priority_class="contract", weight_kg=200, revenue=100),
        ],
    )

    result = run_optimization(db_session, scenario_name="priority_reserve_test")

    assert _status_by_revenue(requests, 5000) == "rejected"
    assert _status_by_revenue(requests, 100) == "accepted"
