"""
Örnek veri üretir: havalimanları, uçak tipleri, rotalar, uçuşlar, kargo talepleri.
Çalıştırmak için (app/backend klasöründeyken, venv aktifken): python -m app.seed_data
"""
import random
from datetime import datetime, timedelta

from app.database.connection import Base, engine, SessionLocal
from app.models.airport import Airport
from app.models.aircraft_type import AircraftType
from app.models.route import Route
from app.models.flight import Flight
from app.models.cargo_request import CargoRequest

random.seed(42)


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    for model in [CargoRequest, Flight, Route, AircraftType, Airport]:
        db.query(model).delete()
    db.commit()

    airports = [
        Airport(airport_code="IST", airport_name="Istanbul Airport", country="Turkey", timezone="Europe/Istanbul", customs_available=True),
        Airport(airport_code="JFK", airport_name="John F. Kennedy Intl", country="USA", timezone="America/New_York", customs_available=True),
        Airport(airport_code="FRA", airport_name="Frankfurt Airport", country="Germany", timezone="Europe/Berlin", customs_available=True),
        Airport(airport_code="DXB", airport_name="Dubai Intl", country="UAE", timezone="Asia/Dubai", customs_available=True),
        Airport(airport_code="ESB", airport_name="Ankara Esenboga", country="Turkey", timezone="Europe/Istanbul", customs_available=False),
    ]
    db.add_all(airports)

    aircraft_types = [
        AircraftType(aircraft_type="A350", max_cargo_weight_kg=15000, max_cargo_volume_m3=90, temperature_controlled_capacity_kg=2000, is_freighter=False, dangerous_goods_allowed=True),
        AircraftType(aircraft_type="B777F", max_cargo_weight_kg=100000, max_cargo_volume_m3=650, temperature_controlled_capacity_kg=15000, is_freighter=True, dangerous_goods_allowed=True),
        AircraftType(aircraft_type="A321", max_cargo_weight_kg=3000, max_cargo_volume_m3=20, temperature_controlled_capacity_kg=0, is_freighter=False, dangerous_goods_allowed=False),
    ]
    db.add_all(aircraft_types)
    db.commit()

    routes = [
        Route(origin_airport="IST", destination_airport="JFK", distance_km=8060, route_type="international", region="North America", customs_required=True, restricted_cargo_allowed=True, is_active=True),
        Route(origin_airport="IST", destination_airport="FRA", distance_km=1860, route_type="international", region="Europe", customs_required=True, restricted_cargo_allowed=True, is_active=True),
        Route(origin_airport="IST", destination_airport="DXB", distance_km=3000, route_type="international", region="Middle East", customs_required=True, restricted_cargo_allowed=True, is_active=True),
        Route(origin_airport="IST", destination_airport="ESB", distance_km=350, route_type="domestic", region="Turkey", customs_required=False, restricted_cargo_allowed=True, is_active=True),
    ]
    db.add_all(routes)
    db.commit()

    base_date = datetime(2026, 7, 15, 10, 0)
    flights = [
        Flight(flight_number="TK001", route_id=1, aircraft_type="B777F", aircraft_registration="TC-CFA", departure_scheduled=base_date, arrival_scheduled=base_date + timedelta(hours=11), status="scheduled"),
        Flight(flight_number="TK011", route_id=2, aircraft_type="A350", aircraft_registration="TC-LGB", departure_scheduled=base_date + timedelta(hours=2), arrival_scheduled=base_date + timedelta(hours=5), status="scheduled"),
        Flight(flight_number="TK093", route_id=3, aircraft_type="A350", aircraft_registration="TC-LGC", departure_scheduled=base_date + timedelta(hours=3), arrival_scheduled=base_date + timedelta(hours=7), status="scheduled"),
        Flight(flight_number="TK2010", route_id=4, aircraft_type="A321", aircraft_registration="TC-JSA", departure_scheduled=base_date + timedelta(hours=1), arrival_scheduled=base_date + timedelta(hours=2), status="scheduled"),
    ]
    db.add_all(flights)
    db.commit()

    cargo_types = ["general", "perishable", "dangerous_goods", "valuable"]
    priority_classes = ["contract", "spot"]

    requests = []
    for flight in flights:
        n_requests = random.randint(6, 10)
        for _ in range(n_requests):
            weight = round(random.uniform(50, 3000), 1)
            volume = round(weight / random.uniform(150, 250), 2)
            revenue = round(weight * random.uniform(1.5, 4.0), 2)
            requests.append(
                CargoRequest(
                    flight_id=flight.flight_id,
                    cargo_type=random.choice(cargo_types),
                    weight_kg=weight,
                    volume_m3=volume,
                    requires_temperature_control=random.random() < 0.15,
                    priority_class=random.choice(priority_classes),
                    revenue=revenue,
                    booking_cutoff_hours=random.choice([12, 24, 48]),
                    status="pending",
                )
            )
    db.add_all(requests)
    db.commit()
    db.close()
    print(f"Seed tamamlandı: {len(airports)} airport, {len(aircraft_types)} aircraft_type, "
          f"{len(routes)} route, {len(flights)} flight, {len(requests)} cargo_request.")


if __name__ == "__main__":
    seed()
