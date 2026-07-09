"""
seed_data.py'nin ürettiği verinin referans bütünlüğünü (her flight'ın gerçek bir
route/aircraft_type'a işaret etmesi) ve Paket B'nin kısıtlarını test edebilecek
kadar hacimli/senaryolu olduğunu doğrular.
"""
from app.models import Airport, AircraftType, Route, Flight, CargoRequest
from app.seed_data import seed


def test_seed_produces_consistent_and_scenario_rich_data(db_session):
    seed(db=db_session)

    aircraft_types = {a.aircraft_type for a in db_session.query(AircraftType).all()}
    routes = {r.route_id: r for r in db_session.query(Route).all()}
    flights = db_session.query(Flight).all()
    requests = db_session.query(CargoRequest).all()

    assert len(db_session.query(Airport).all()) >= 15
    assert len(aircraft_types) == 5
    assert len(flights) >= 18

    # Referans bütünlüğü: her flight, var olan bir route/aircraft_type'a işaret etmeli.
    for flight in flights:
        assert flight.route_id in routes
        assert flight.aircraft_type in aircraft_types

    # Paket B'nin kısıtlarının test edilebilmesi için gereken senaryolar mevcut mu?
    embargoed_routes = [r for r in routes.values() if r.embargo_active]
    restricted_routes = [r for r in routes.values() if not r.restricted_cargo_allowed]
    assert len(embargoed_routes) >= 1
    assert len(restricted_routes) >= 1

    embargoed_flight_ids = {f.flight_id for f in flights if f.route_id in {r.route_id for r in embargoed_routes}}
    restricted_flight_ids = {f.flight_id for f in flights if f.route_id in {r.route_id for r in restricted_routes}}

    live_animal_on_embargoed_route = [
        req for req in requests if req.flight_id in embargoed_flight_ids and req.cargo_type == "live_animal"
    ]
    dangerous_goods_on_restricted_route = [
        req for req in requests if req.flight_id in restricted_flight_ids and req.cargo_type == "dangerous_goods"
    ]
    assert len(live_animal_on_embargoed_route) >= 2
    assert len(dangerous_goods_on_restricted_route) >= 2

    assert len(requests) > 150
