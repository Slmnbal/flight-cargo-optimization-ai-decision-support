"""
seed_data.py'nin ürettiği verinin referans bütünlüğünü (her flight'ın gerçek bir
route/aircraft_type'a işaret etmesi) ve Paket B'nin kısıtlarını test edebilecek
kadar hacimli/senaryolu olduğunu doğrular.
"""
from collections import defaultdict

from app.models import Airport, AircraftType, Route, Flight, CargoRequest
from app.seed_data import seed, WINDOW_END


def test_seed_produces_consistent_and_scenario_rich_data(db_session):
    # window_days=14: tam 12 aylık pencere testte gereksiz yavaş olurdu (~100k+
    # satır); 14 günlük pencere, haftalık tekrar pattern'leri (freighter'lar
    # dahil) ve haftada-bir enjekte edilen embargo/kısıtlı-kargo senaryoları
    # için yeterli, aşağıdaki tüm eşikleri hâlâ rahatça karşılıyor.
    seed(db=db_session, window_days=14)

    aircraft_types = {a.aircraft_type for a in db_session.query(AircraftType).all()}
    routes = {r.route_id: r for r in db_session.query(Route).all()}
    flights = db_session.query(Flight).all()
    requests = db_session.query(CargoRequest).all()

    assert len(db_session.query(Airport).all()) >= 18
    assert len(aircraft_types) == 7
    assert len(flights) >= 25

    # Freighter tiplerinin (A330-200F, B777F) operasyonel hacmi, sadece bir-iki
    # örnek uçuşla değil, filo büyüklüğünü (gerçekte ~19-20 uçak) makul yansıtacak
    # sayıda uçuşla temsil edilmeli.
    freighter_flights = [f for f in flights if f.aircraft_type in ("A330-200F", "B777F")]
    assert len(freighter_flights) >= 12

    # Gelir, sadece rastgele bir sayı değil -- aynı ağırlıktaki bir talep, kısa bir
    # iç hat rotasında (düşük $/kg) uzun menzilli bir kargo rotasından (yüksek $/kg)
    # belirgin şekilde daha az gelir getirmeli.
    domestic_route_ids = {r.route_id for r in routes.values() if r.region == "Turkey"}
    long_haul_route_ids = {r.route_id for r in routes.values() if r.region in ("Asia", "South America")}
    domestic_flight_ids = {f.flight_id for f in flights if f.route_id in domestic_route_ids}
    long_haul_flight_ids = {f.flight_id for f in flights if f.route_id in long_haul_route_ids}
    domestic_rate = max(
        req.revenue / req.weight_kg for req in requests if req.flight_id in domestic_flight_ids
    )
    long_haul_rate = min(
        req.revenue / req.weight_kg for req in requests if req.flight_id in long_haul_flight_ids
    )
    assert long_haul_rate > domestic_rate

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

    # 12 aylık zaman serisi modeli: aynı flight_number, pencere boyunca birden
    # fazla tarihli Flight satırında tekrar kullanılmalı (recurrence yerine).
    flights_by_number = defaultdict(set)
    for flight in flights:
        flights_by_number[flight.flight_number].add(flight.departure_scheduled.date())
    assert any(len(dates) >= 2 for dates in flights_by_number.values())

    # Pencerenin son "gün-çapası" (anchor) hariç tüm uçuşlar "completed" olmalı
    # -- son gün (backfill_history.py'nin kasıtlı olarak dokunmadığı "bugün")
    # "scheduled" kalır, ki dashboard'daki "Optimizasyonu Çalıştır" aksiyonunun
    # her zaman no-op olmaması sağlanır. Not: bazı geç saatli uçuşlar (örn.
    # 23:00 offset) gece yarısını geçip ertesi takvim gününe düşebiliyor, bu
    # yüzden karşılaştırma .date() yerine WINDOW_END zaman damgasına göre
    # yapılıyor -- departure_scheduled >= WINDOW_END <=> anchor günü ==
    # pencerenin son günü (seed_data.py'deki generate_flight_instances'ın
    # is_last_day mantığıyla birebir eşleşir).
    scheduled_flights = [f for f in flights if f.status == "scheduled"]
    completed_flights = [f for f in flights if f.status == "completed"]
    assert all(f.departure_scheduled >= WINDOW_END for f in scheduled_flights)
    assert all(f.departure_scheduled < WINDOW_END for f in completed_flights)
    assert len(scheduled_flights) >= 1
