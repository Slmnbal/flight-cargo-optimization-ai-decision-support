"""
Örnek veri üretir: havalimanları, uçak tipleri, rotalar, uçuşlar, kargo talepleri.

Filo ve kapasite rakamları gerçek THY / Turkish Cargo filosundan (2026) esinlenilmiş,
simülasyon için yuvarlanmış değerlerdir — operasyonel hassasiyette değil, ama
"generic PlaneA/PlaneB" yerine gerçek uçak tiplerinin gerçek kapasite mertebesini
yansıtıyor. Rota ağı IST hub-and-spoke yapısını taklit ediyor.

Not: Turkish Cargo'nun gerçekte sadece 2 freighter TİPİ var (B777F, A330-200F,
toplam ~19-20 kuyruk numarası); "25 kargo uçağı" gibi bir rakam bireysel uçaklara
(tail) işaret eder, tiplere değil. Burada modellenen 2 freighter tipi bu açıdan
gerçekçi -- ama önceki sürümde bu 2 tipin operasyonel hacmi sadece 6 uçuşla temsil
ediliyordu, ki bu ~19-20 uçaklık bir filo için yetersizdi. Bu sürümde freighter
uçuş sayısı 15'e çıkarıldı (daha fazla rota + mevcut rotalara ikinci frekans).

Çalıştırmak için (app/backend klasöründeyken, venv aktifken): python -m app.seed_data
"""
import random
from datetime import datetime, timedelta

from app.database.connection import SessionLocal
from app.models import Airport, AircraftType, Route, Flight, CargoRequest

random.seed(42)

# --- Gelir modeli: rota bölgesine, kargo tipine ve priority sınıfına bağlı kaba bir
# fiyatlandırma. Gerçek IATA kargo tarifelerinin ÇOK basitleştirilmiş bir yansıması --
# gerçek bir tarife tablosu değil, "gelir sadece ağırlık*rastgele sayı değil, rotaya ve
# kargo tipine göre anlamlı şekilde değişmeli" ilkesini kodluyor. Mesafe arttıkça $/kg
# genelde artar (uzun menzilde sabit maliyetlerin amortismanı + arz/talep dengesi).
REGION_BASE_RATE_PER_KG = {
    "Turkey": 1.0,
    "Europe": 2.0,
    "Middle East": 2.5,
    "Africa": 3.5,
    "North America": 3.5,
    "Asia": 4.0,
    "South America": 4.5,
}
CARGO_TYPE_RATE_MULTIPLIER = {
    "general": 1.0,
    "oversized": 1.3,
    "perishable": 1.3,
    "valuable": 1.6,
    "dangerous_goods": 1.5,
    "live_animal": 1.8,
}
# Contract kargo, hacim karşılığında sabit/indirimli bir birim fiyata bağlıdır;
# spot kargo o anki piyasa fiyatını (ve dalgalanmasını) yansıtır.
PRIORITY_RATE_MULTIPLIER = {"contract": 0.9, "spot": 1.0}


def seed(db=None):
    """
    db verilmezse gerçek (cargo.db) veritabanına yazar; verilirse (örn. testlerde
    izole bir in-memory session) o session üzerinde çalışır ve session'ı kapatmaz —
    kapatma sorumluluğu çağırana ait.
    """
    owns_session = db is None
    if owns_session:
        # Şema artık Alembic tarafından yönetiliyor -- burada tablo oluşturmuyoruz.
        # `alembic upgrade head` çalıştırılmadan seed() çağrılırsa, tablo yok hatası
        # alınır; bu kasıtlı, kurulum sırasının (migration önce, seed sonra) açıkça
        # görünmesini sağlıyor.
        db = SessionLocal()

    for model in [CargoRequest, Flight, Route, AircraftType, Airport]:
        db.query(model).delete()
    db.commit()

    # --- Havalimanları: IST hub + gerçek THY/Turkish Cargo uzun/orta/kısa menzil noktaları ---
    airports = [
        Airport(airport_code="IST", airport_name="Istanbul Airport", country="Turkey", timezone="Europe/Istanbul", customs_available=True),
        Airport(airport_code="ESB", airport_name="Ankara Esenboga", country="Turkey", timezone="Europe/Istanbul", customs_available=False),
        Airport(airport_code="ADB", airport_name="Izmir Adnan Menderes", country="Turkey", timezone="Europe/Istanbul", customs_available=True),
        Airport(airport_code="AYT", airport_name="Antalya Airport", country="Turkey", timezone="Europe/Istanbul", customs_available=True),
        Airport(airport_code="GZT", airport_name="Gaziantep Oguzeli", country="Turkey", timezone="Europe/Istanbul", customs_available=False),
        Airport(airport_code="FRA", airport_name="Frankfurt Airport", country="Germany", timezone="Europe/Berlin", customs_available=True),
        Airport(airport_code="LHR", airport_name="London Heathrow", country="United Kingdom", timezone="Europe/London", customs_available=True),
        Airport(airport_code="CDG", airport_name="Paris Charles de Gaulle", country="France", timezone="Europe/Paris", customs_available=True),
        Airport(airport_code="AMS", airport_name="Amsterdam Schiphol", country="Netherlands", timezone="Europe/Amsterdam", customs_available=True),
        Airport(airport_code="JFK", airport_name="John F. Kennedy Intl", country="USA", timezone="America/New_York", customs_available=True),
        Airport(airport_code="ORD", airport_name="Chicago O'Hare", country="USA", timezone="America/Chicago", customs_available=True),
        Airport(airport_code="MIA", airport_name="Miami Intl", country="USA", timezone="America/New_York", customs_available=True),
        Airport(airport_code="DXB", airport_name="Dubai Intl", country="UAE", timezone="Asia/Dubai", customs_available=True),
        Airport(airport_code="JNB", airport_name="OR Tambo Intl", country="South Africa", timezone="Africa/Johannesburg", customs_available=True),
        Airport(airport_code="NBO", airport_name="Jomo Kenyatta Intl", country="Kenya", timezone="Africa/Nairobi", customs_available=True),
        Airport(airport_code="LOS", airport_name="Murtala Muhammed Intl", country="Nigeria", timezone="Africa/Lagos", customs_available=True),
        Airport(airport_code="PVG", airport_name="Shanghai Pudong Intl", country="China", timezone="Asia/Shanghai", customs_available=True),
        Airport(airport_code="NRT", airport_name="Tokyo Narita Intl", country="Japan", timezone="Asia/Tokyo", customs_available=True),
        Airport(airport_code="HKG", airport_name="Hong Kong Intl", country="China", timezone="Asia/Hong_Kong", customs_available=True),
        Airport(airport_code="ICN", airport_name="Incheon Intl", country="South Korea", timezone="Asia/Seoul", customs_available=True),
        Airport(airport_code="GRU", airport_name="Sao Paulo Guarulhos Intl", country="Brazil", timezone="America/Sao_Paulo", customs_available=True),
    ]
    db.add_all(airports)

    # --- Uçak tipleri: gerçek THY yolcu filosu (gövde altı kargo) + Turkish Cargo freighter filosu ---
    # Kapasiteler yayınlanmış teknik özelliklerden yuvarlanmıştır:
    #   A321NEO: dar gövde, sadece gövde altı kargo (~52 m3 LD3 kapasitesi mertebesinde)
    #   A330-200 / A330-300: orta-geniş gövde, alt güverte kargo hacmi ~90-135 m3 mertebesinde
    #   B777-300ER: büyük geniş gövde, alt güverte kargo hacmi ~160-200 m3 mertebesinde
    #   A350-900: geniş gövde, alt güverte kargo hacmi ~110-150 m3 mertebesinde
    #   A330-200F: adanmış freighter, yayınlanmış payload ~70t / hacim ~467-475 m3
    #   B777F: adanmış freighter, yayınlanmış yapısal payload ~102t (hacim genelde
    #          ağırlıktan önce dolar -> ~95t pratik kapasite kullanıldı) / hacim 653 m3
    aircraft_types = [
        AircraftType(aircraft_type="A321NEO", max_cargo_weight_kg=12000, max_cargo_volume_m3=52, temperature_controlled_capacity_kg=500, is_freighter=False, dangerous_goods_allowed=False),
        AircraftType(aircraft_type="A330-200", max_cargo_weight_kg=14000, max_cargo_volume_m3=88, temperature_controlled_capacity_kg=2800, is_freighter=False, dangerous_goods_allowed=True),
        AircraftType(aircraft_type="A330-300", max_cargo_weight_kg=16000, max_cargo_volume_m3=94, temperature_controlled_capacity_kg=3000, is_freighter=False, dangerous_goods_allowed=True),
        AircraftType(aircraft_type="B777-300ER", max_cargo_weight_kg=24000, max_cargo_volume_m3=160, temperature_controlled_capacity_kg=4500, is_freighter=False, dangerous_goods_allowed=True),
        AircraftType(aircraft_type="A350-900", max_cargo_weight_kg=20000, max_cargo_volume_m3=120, temperature_controlled_capacity_kg=4000, is_freighter=False, dangerous_goods_allowed=True),
        AircraftType(aircraft_type="A330-200F", max_cargo_weight_kg=70000, max_cargo_volume_m3=470, temperature_controlled_capacity_kg=15000, is_freighter=True, dangerous_goods_allowed=True),
        AircraftType(aircraft_type="B777F", max_cargo_weight_kg=95000, max_cargo_volume_m3=653, temperature_controlled_capacity_kg=20000, is_freighter=True, dangerous_goods_allowed=True),
    ]
    db.add_all(aircraft_types)
    db.commit()

    # --- Rotalar: hepsi IST merkezli (hub-and-spoke), iç hat / Avrupa / uzun menzil / kargo ağırlıklı karışım ---
    # embargo_active / restricted_cargo_allowed=False senaryoları bilinçli seçildi:
    #   IST-JNB: bölgesel bir hayvan hastalığı salgını nedeniyle canlı hayvan (live_animal)
    #            kargosu geçici olarak durduruldu (gerçek dünyada kuş gribi vb. kaynaklı
    #            canlı hayvan embargoları sık yaşanır). embargoed_cargo_types="live_animal"
    #            ile kapsam daraltılmış durumda.
    #   IST-NRT: Japonya'nın tehlikeli madde (özellikle lityum pil) ithalatına yönelik sıkı
    #            gümrük kuralları nedeniyle bu rotada dangerous_goods kargo hiç kabul edilmiyor.
    # GRU, MIA, HKG, ICN: Turkish Cargo'nun gerçek freighter ağının Amerika/Asya ayağını
    # temsil eden ek rotalar -- önceki sürümde freighter operasyonu sadece Afrika/Asya'nın
    # 3 noktasıyla (JNB, NBO, LOS, PVG, NRT) temsil ediliyordu, bu dar bir kesitti.
    route_defs = [
        # (origin, dest, distance_km, route_type, region, customs_required, restricted_cargo_allowed, embargo_active, embargoed_cargo_types)
        ("IST", "ESB", 350, "domestic", "Turkey", False, True, False, None),
        ("IST", "ADB", 330, "domestic", "Turkey", False, True, False, None),
        ("IST", "AYT", 440, "domestic", "Turkey", False, True, False, None),
        ("IST", "GZT", 900, "domestic", "Turkey", False, True, False, None),
        ("IST", "FRA", 1860, "international", "Europe", True, True, False, None),
        ("IST", "LHR", 2500, "international", "Europe", True, True, False, None),
        ("IST", "CDG", 2250, "international", "Europe", True, True, False, None),
        ("IST", "AMS", 2200, "international", "Europe", True, True, False, None),
        ("IST", "JFK", 8060, "international", "North America", True, True, False, None),
        ("IST", "ORD", 8990, "international", "North America", True, True, False, None),
        ("IST", "MIA", 9700, "international", "North America", True, True, False, None),
        ("IST", "DXB", 3000, "international", "Middle East", True, True, False, None),
        ("IST", "JNB", 7700, "international", "Africa", True, True, True, "live_animal"),
        ("IST", "NBO", 4900, "international", "Africa", True, True, False, None),
        ("IST", "LOS", 5200, "international", "Africa", True, True, False, None),
        ("IST", "PVG", 7500, "international", "Asia", True, True, False, None),
        ("IST", "NRT", 8950, "international", "Asia", True, False, False, None),
        ("IST", "HKG", 8200, "international", "Asia", True, True, False, None),
        ("IST", "ICN", 8300, "international", "Asia", True, True, False, None),
        ("IST", "GRU", 10700, "international", "South America", True, True, False, None),
    ]
    routes = [
        Route(
            origin_airport=origin, destination_airport=dest, distance_km=distance,
            route_type=route_type, region=region, customs_required=customs_required,
            restricted_cargo_allowed=restricted_cargo_allowed, embargo_active=embargo_active,
            embargoed_cargo_types=embargoed_cargo_types, is_active=True,
        )
        for origin, dest, distance, route_type, region, customs_required, restricted_cargo_allowed, embargo_active, embargoed_cargo_types in route_defs
    ]
    db.add_all(routes)
    db.commit()

    # route_id'leri (origin, dest) çiftinden bulmak için: flights tanımında sabit
    # sayısal id yerine okunabilir bir anahtar kullanmamızı sağlıyor.
    route_id_by_pair = {(r.origin_airport, r.destination_airport): r.route_id for r in routes}
    route_by_id = {r.route_id: r for r in routes}

    base_date = datetime(2026, 7, 15, 6, 0)
    flight_defs = [
        # (flight_number, (origin, dest), aircraft_type, tail, dep_offset_h, duration_h)
        ("TK2010", ("IST", "ESB"), "A321NEO", "TC-JSA", 0.0, 1.25),
        ("TK2032", ("IST", "ADB"), "A321NEO", "TC-JSB", 0.5, 1.33),
        ("TK2124", ("IST", "AYT"), "A321NEO", "TC-JSC", 1.0, 1.5),
        ("TK2258", ("IST", "GZT"), "A321NEO", "TC-JSD", 1.5, 2.0),
        ("TK2011", ("IST", "ESB"), "A321NEO", "TC-JSA", 8.0, 1.25),
        ("TK1621", ("IST", "FRA"), "A330-300", "TC-LGB", 2.0, 3.5),
        ("TK1979", ("IST", "LHR"), "A330-200", "TC-LGC", 2.5, 4.0),
        ("TK1823", ("IST", "CDG"), "A330-300", "TC-LGD", 3.0, 3.75),
        ("TK1943", ("IST", "AMS"), "A330-200", "TC-LGE", 3.5, 3.5),
        ("TK1622", ("IST", "FRA"), "A330-300", "TC-LGB", 14.0, 3.5),
        ("TK001", ("IST", "JFK"), "A350-900", "TC-LGF", 4.0, 11.0),
        ("TK005", ("IST", "ORD"), "B777-300ER", "TC-LGG", 4.5, 11.5),
        ("TK002", ("IST", "JFK"), "A350-900", "TC-LGF", 16.0, 11.0),
        ("TK015", ("IST", "MIA"), "B777-300ER", "TC-LGI", 5.5, 12.5),
        ("TK762", ("IST", "DXB"), "A330-300", "TC-LGH", 5.0, 4.0),
        ("TK6131", ("IST", "JNB"), "B777F", "TC-CFA", 6.0, 10.0),
        ("TK6132", ("IST", "JNB"), "B777F", "TC-CFA", 18.0, 10.0),
        ("TK6255", ("IST", "NBO"), "A330-200F", "TC-CFB", 6.5, 6.0),
        ("TK6256", ("IST", "NBO"), "A330-200F", "TC-CFB", 19.0, 6.0),
        ("TK6287", ("IST", "LOS"), "A330-200F", "TC-CFC", 7.0, 7.0),
        ("TK6288", ("IST", "LOS"), "A330-200F", "TC-CFC", 20.0, 7.0),
        ("TK6070", ("IST", "PVG"), "A330-200F", "TC-CFD", 7.5, 9.0),
        ("TK6071", ("IST", "PVG"), "A330-200F", "TC-CFD", 21.0, 9.0),
        ("TK6072", ("IST", "NRT"), "B777F", "TC-CFE", 8.0, 11.0),
        ("TK6073", ("IST", "NRT"), "B777F", "TC-CFE", 22.0, 11.0),
        ("TK6501", ("IST", "HKG"), "B777F", "TC-CFF", 9.0, 10.5),
        ("TK6601", ("IST", "ICN"), "A330-200F", "TC-CFG", 9.5, 9.5),
        ("TK6301", ("IST", "GRU"), "B777F", "TC-CFH", 10.0, 13.0),
        ("TK6302", ("IST", "GRU"), "B777F", "TC-CFH", 23.0, 13.0),
    ]
    flights = [
        Flight(
            flight_number=flight_number,
            route_id=route_id_by_pair[pair],
            aircraft_type=aircraft_type,
            aircraft_registration=tail,
            departure_scheduled=base_date + timedelta(hours=dep_offset_h),
            arrival_scheduled=base_date + timedelta(hours=dep_offset_h + duration_h),
            status="scheduled",
        )
        for flight_number, pair, aircraft_type, tail, dep_offset_h, duration_h in flight_defs
    ]
    db.add_all(flights)
    db.commit()

    flight_by_number = {f.flight_number: f for f in flights}

    cargo_types = ["general", "perishable", "dangerous_goods", "valuable", "live_animal", "oversized"]
    priority_classes = ["contract", "spot"]

    def calculate_revenue(route, cargo_type, priority_class, weight_kg):
        """
        Rota bölgesine, kargo tipine ve priority sınıfına bağlı kaba bir fiyatlandırma
        (gerçek IATA tarifelerinin çok basitleştirilmiş bir yansıması, bkz. modül başı
        docstring). Saf "ağırlık * rastgele sayı" yerine, gelirin rotaya ve kargo tipine
        göre anlamlı şekilde değişmesini sağlıyor -- örn. IST-GRU'daki bir dangerous_goods
        spot talebi, IST-ESB'deki bir general contract talebinden çok daha yüksek birim
        fiyata sahip olacak.
        """
        rate_per_kg = (
            REGION_BASE_RATE_PER_KG[route.region]
            * CARGO_TYPE_RATE_MULTIPLIER[cargo_type]
            * PRIORITY_RATE_MULTIPLIER[priority_class]
            * random.uniform(0.85, 1.15)  # günlük talep/arz dalgalanması
        )
        return round(weight_kg * rate_per_kg, 2)

    def random_request(flight, cargo_type=None, priority_class=None):
        route = route_by_id[flight.route_id]
        weight = round(random.uniform(50, 3000), 1)
        volume = round(weight / random.uniform(150, 250), 2)
        cargo_type = cargo_type or random.choice(cargo_types)
        priority_class = priority_class or random.choice(priority_classes)
        revenue = calculate_revenue(route, cargo_type, priority_class, weight)
        return CargoRequest(
            flight_id=flight.flight_id,
            cargo_type=cargo_type,
            weight_kg=weight,
            volume_m3=volume,
            requires_temperature_control=random.random() < 0.15,
            priority_class=priority_class,
            revenue=revenue,
            booking_cutoff_hours=random.choice([12, 24, 48]),
            status="pending",
        )

    requests = []
    for flight in flights:
        n_requests = random.randint(10, 18)
        for _ in range(n_requests):
            requests.append(random_request(flight))

    # Embargo (IST-JNB) ve kısıtlı-kargo (IST-NRT) senaryolarının rastgelelikten
    # bağımsız, her seed çalıştığında garanti test edilebilir olması için: bu iki
    # rotanın uçuşlarına elle en az birkaç "çakışan" talep ekliyoruz.
    for flight_number in ("TK6131", "TK6132"):
        flight = flight_by_number[flight_number]
        requests.append(random_request(flight, cargo_type="live_animal"))
        requests.append(random_request(flight, cargo_type="live_animal"))

    nrt_flight = flight_by_number["TK6072"]
    requests.append(random_request(nrt_flight, cargo_type="dangerous_goods"))
    requests.append(random_request(nrt_flight, cargo_type="dangerous_goods"))

    db.add_all(requests)
    db.commit()

    if owns_session:
        db.close()

    n_freighter_flights = sum(1 for _, _, ac, *_ in flight_defs if ac in ("A330-200F", "B777F"))
    print(f"Seed tamamlandı: {len(airports)} airport, {len(aircraft_types)} aircraft_type, "
          f"{len(routes)} route, {len(flights)} flight ({n_freighter_flights} freighter), "
          f"{len(requests)} cargo_request.")


if __name__ == "__main__":
    seed()
