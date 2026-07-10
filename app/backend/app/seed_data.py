"""
Örnek veri üretir: havalimanları, uçak tipleri, rotalar, ve bunların üzerine
kurulu 12 aylık tekrarlayan bir uçuş takvimi + kargo talepleri.

Filo ve kapasite rakamları gerçek THY / Turkish Cargo filosundan (2026) esinlenilmiş,
simülasyon için yuvarlanmış değerlerdir — operasyonel hassasiyette değil, ama
"generic PlaneA/PlaneB" yerine gerçek uçak tiplerinin gerçek kapasite mertebesini
yansıtıyor. Rota ağı IST hub-and-spoke yapısını taklit ediyor.

Uçuş takvimi modeli: her uçuş numarası (`FlightScheduleDef`) haftanın hangi
günlerinde uçtuğunu (`weekdays`) taşıyan bir "şablon" -- gerçek bir recurrence
tablosu yerine, aynı `flight_number` pencere boyunca birden fazla tarihli
`Flight` satırında tekrar kullanılıyor (bkz. Faz 4 dashboard planı). İç hat ve
yolcu uçuşları günlük; freighter'lar haftada 2-3x staggered pattern'lerle
uçuyor -- Turkish Cargo'nun gerçekte sadece 2 freighter TİPİ (B777F,
A330-200F, toplam ~19-20 kuyruk numarası) olduğu ve bu filonun her rotayı her
gün uçamayacağı gözlemiyle tutarlı.

`seasonality_multiplier`, yaz/yılbaşı gibi bilinen yoğun dönemlerde talep
HACMİNİ (fiyatlandırma modelini değil) kaba biçimde artırıp azaltıyor --
gerçek bir talep tahmin modeli değil, dashboard'un aylık trend grafiklerinde
görülebilir bir mevsimsel örüntü üretmek için eklenen basit bir çarpan.

Çalıştırmak için (app/backend klasöründeyken, venv aktifken): python -m app.seed_data
Varsayılan pencere: 365 gün (12 ay), `WINDOW_END` tarihinde biter. Pencerenin
SON günü (bugün) kasıtlı olarak optimizasyona tabi tutulmuyor (bkz.
backfill_history.py) -- dashboard'daki "Optimizasyonu Çalıştır" aksiyonunun
her zaman no-op olmaması için.
"""
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from app.database.connection import SessionLocal
from app.models import Airport, AircraftType, Route, Flight, CargoRequest, OptimizationResult

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

CARGO_TYPES = ["general", "perishable", "dangerous_goods", "valuable", "live_animal", "oversized"]
PRIORITY_CLASSES = ["contract", "spot"]

# 12 aylık pencere: WINDOW_END, mevcut demo'nun "bugünü" (önceki tek-günlük
# seed'in `base_date`'i) -- pencerenin SONU olarak korunuyor, geriye doğru
# WINDOW_DAYS gün üretiliyor. Böylece tek-günlük demo semantiği bozulmadan
# geçmişe genişletilmiş oluyor.
WINDOW_END = datetime(2026, 7, 15, 6, 0)
WINDOW_DAYS = 365

DAILY = frozenset(range(7))  # 0=Pazartesi .. 6=Pazar

# Embargo (IST-JNB, live_animal) ve kısıtlı-kargo (IST-NRT, dangerous_goods)
# senaryolarının haftada bir, rastgelelikten bağımsız enjekte edildiği gün.
CONFLICT_INJECTION_WEEKDAY = {"JNB": 0, "NRT": 1}


@dataclass(frozen=True)
class FlightScheduleDef:
    flight_number: str
    origin: str
    destination: str
    aircraft_type: str
    tail: str
    dep_offset_h: float
    duration_h: float
    weekdays: frozenset  # frozenset[int], hangi haftanın günlerinde uçuyor


def build_airports() -> list[Airport]:
    return [
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


def build_aircraft_types() -> list[AircraftType]:
    # Kapasiteler yayınlanmış teknik özelliklerden yuvarlanmıştır:
    #   A321NEO: dar gövde, sadece gövde altı kargo (~52 m3 LD3 kapasitesi mertebesinde)
    #   A330-200 / A330-300: orta-geniş gövde, alt güverte kargo hacmi ~90-135 m3 mertebesinde
    #   B777-300ER: büyük geniş gövde, alt güverte kargo hacmi ~160-200 m3 mertebesinde
    #   A350-900: geniş gövde, alt güverte kargo hacmi ~110-150 m3 mertebesinde
    #   A330-200F: adanmış freighter, yayınlanmış payload ~70t / hacim ~467-475 m3
    #   B777F: adanmış freighter, yayınlanmış yapısal payload ~102t (hacim genelde
    #          ağırlıktan önce dolar -> ~95t pratik kapasite kullanıldı) / hacim 653 m3
    return [
        AircraftType(aircraft_type="A321NEO", max_cargo_weight_kg=12000, max_cargo_volume_m3=52, temperature_controlled_capacity_kg=500, is_freighter=False, dangerous_goods_allowed=False),
        AircraftType(aircraft_type="A330-200", max_cargo_weight_kg=14000, max_cargo_volume_m3=88, temperature_controlled_capacity_kg=2800, is_freighter=False, dangerous_goods_allowed=True),
        AircraftType(aircraft_type="A330-300", max_cargo_weight_kg=16000, max_cargo_volume_m3=94, temperature_controlled_capacity_kg=3000, is_freighter=False, dangerous_goods_allowed=True),
        AircraftType(aircraft_type="B777-300ER", max_cargo_weight_kg=24000, max_cargo_volume_m3=160, temperature_controlled_capacity_kg=4500, is_freighter=False, dangerous_goods_allowed=True),
        AircraftType(aircraft_type="A350-900", max_cargo_weight_kg=20000, max_cargo_volume_m3=120, temperature_controlled_capacity_kg=4000, is_freighter=False, dangerous_goods_allowed=True),
        AircraftType(aircraft_type="A330-200F", max_cargo_weight_kg=70000, max_cargo_volume_m3=470, temperature_controlled_capacity_kg=15000, is_freighter=True, dangerous_goods_allowed=True),
        AircraftType(aircraft_type="B777F", max_cargo_weight_kg=95000, max_cargo_volume_m3=653, temperature_controlled_capacity_kg=20000, is_freighter=True, dangerous_goods_allowed=True),
    ]


def build_routes() -> list[Route]:
    # embargo_active / restricted_cargo_allowed=False senaryoları bilinçli seçildi:
    #   IST-JNB: bölgesel bir hayvan hastalığı salgını nedeniyle canlı hayvan (live_animal)
    #            kargosu geçici olarak durduruldu (gerçek dünyada kuş gribi vb. kaynaklı
    #            canlı hayvan embargoları sık yaşanır). embargoed_cargo_types="live_animal"
    #            ile kapsam daraltılmış durumda.
    #   IST-NRT: Japonya'nın tehlikeli madde (özellikle lityum pil) ithalatına yönelik sıkı
    #            gümrük kuralları nedeniyle bu rotada dangerous_goods kargo hiç kabul edilmiyor.
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
    return [
        Route(
            origin_airport=origin, destination_airport=dest, distance_km=distance,
            route_type=route_type, region=region, customs_required=customs_required,
            restricted_cargo_allowed=restricted_cargo_allowed, embargo_active=embargo_active,
            embargoed_cargo_types=embargoed_cargo_types, is_active=True,
        )
        for origin, dest, distance, route_type, region, customs_required, restricted_cargo_allowed, embargo_active, embargoed_cargo_types in route_defs
    ]


def build_flight_schedule_defs() -> list[FlightScheduleDef]:
    return [
        # İç hat, Avrupa ve uzun menzil yolcu uçuşları: gerçek THY frekansına
        # yakın günlük operasyon.
        FlightScheduleDef("TK2010", "IST", "ESB", "A321NEO", "TC-JSA", 0.0, 1.25, DAILY),
        FlightScheduleDef("TK2032", "IST", "ADB", "A321NEO", "TC-JSB", 0.5, 1.33, DAILY),
        FlightScheduleDef("TK2124", "IST", "AYT", "A321NEO", "TC-JSC", 1.0, 1.5, DAILY),
        FlightScheduleDef("TK2258", "IST", "GZT", "A321NEO", "TC-JSD", 1.5, 2.0, DAILY),
        FlightScheduleDef("TK2011", "IST", "ESB", "A321NEO", "TC-JSA", 8.0, 1.25, DAILY),
        FlightScheduleDef("TK1621", "IST", "FRA", "A330-300", "TC-LGB", 2.0, 3.5, DAILY),
        FlightScheduleDef("TK1979", "IST", "LHR", "A330-200", "TC-LGC", 2.5, 4.0, DAILY),
        FlightScheduleDef("TK1823", "IST", "CDG", "A330-300", "TC-LGD", 3.0, 3.75, DAILY),
        FlightScheduleDef("TK1943", "IST", "AMS", "A330-200", "TC-LGE", 3.5, 3.5, DAILY),
        FlightScheduleDef("TK1622", "IST", "FRA", "A330-300", "TC-LGB", 14.0, 3.5, DAILY),
        FlightScheduleDef("TK001", "IST", "JFK", "A350-900", "TC-LGF", 4.0, 11.0, DAILY),
        FlightScheduleDef("TK005", "IST", "ORD", "B777-300ER", "TC-LGG", 4.5, 11.5, DAILY),
        FlightScheduleDef("TK002", "IST", "JFK", "A350-900", "TC-LGF", 16.0, 11.0, DAILY),
        FlightScheduleDef("TK015", "IST", "MIA", "B777-300ER", "TC-LGI", 5.5, 12.5, DAILY),
        FlightScheduleDef("TK762", "IST", "DXB", "A330-300", "TC-LGH", 5.0, 4.0, DAILY),
        # Freighter'lar: ~19-20 kuyruklu gerçek filonun her rotayı her gün
        # uçamayacağı gözlemiyle tutarlı, kuyruk başına haftada 2-3x staggered
        # pattern (0=Pazartesi .. 6=Pazar).
        FlightScheduleDef("TK6131", "IST", "JNB", "B777F", "TC-CFA", 6.0, 10.0, frozenset({0, 3})),
        FlightScheduleDef("TK6132", "IST", "JNB", "B777F", "TC-CFA", 18.0, 10.0, frozenset({0, 3})),
        FlightScheduleDef("TK6255", "IST", "NBO", "A330-200F", "TC-CFB", 6.5, 6.0, frozenset({1, 4, 6})),
        FlightScheduleDef("TK6256", "IST", "NBO", "A330-200F", "TC-CFB", 19.0, 6.0, frozenset({1, 4, 6})),
        FlightScheduleDef("TK6287", "IST", "LOS", "A330-200F", "TC-CFC", 7.0, 7.0, frozenset({2, 5})),
        FlightScheduleDef("TK6288", "IST", "LOS", "A330-200F", "TC-CFC", 20.0, 7.0, frozenset({2, 5})),
        FlightScheduleDef("TK6070", "IST", "PVG", "A330-200F", "TC-CFD", 7.5, 9.0, frozenset({0, 2, 4})),
        FlightScheduleDef("TK6071", "IST", "PVG", "A330-200F", "TC-CFD", 21.0, 9.0, frozenset({0, 2, 4})),
        FlightScheduleDef("TK6072", "IST", "NRT", "B777F", "TC-CFE", 8.0, 11.0, frozenset({1, 3, 5})),
        FlightScheduleDef("TK6073", "IST", "NRT", "B777F", "TC-CFE", 22.0, 11.0, frozenset({1, 3, 5})),
        FlightScheduleDef("TK6501", "IST", "HKG", "B777F", "TC-CFF", 9.0, 10.5, frozenset({2, 6})),
        FlightScheduleDef("TK6601", "IST", "ICN", "A330-200F", "TC-CFG", 9.5, 9.5, frozenset({1, 4})),
        FlightScheduleDef("TK6301", "IST", "GRU", "B777F", "TC-CFH", 10.0, 13.0, frozenset({0, 3, 5})),
        FlightScheduleDef("TK6302", "IST", "GRU", "B777F", "TC-CFH", 23.0, 13.0, frozenset({0, 3, 5})),
    ]


def generate_flight_instances(
    schedule_defs: list[FlightScheduleDef],
    route_id_by_pair: dict,
    window_start_date: date,
    window_end_date: date,
) -> list[Flight]:
    """Pencere içindeki her takvim günü için, o günün haftanın günü (weekday)
    pattern'ine uyan şablonlardan tarihli bir Flight satırı üretir. Pencerenin
    son günü hariç tüm uçuşlar 'completed' -- son gün (bugün) 'scheduled' kalır."""
    flights = []
    day = window_start_date
    while day <= window_end_date:
        weekday = day.weekday()
        is_last_day = day == window_end_date
        day_anchor = datetime.combine(day, time(6, 0))
        for sd in schedule_defs:
            if weekday not in sd.weekdays:
                continue
            flights.append(
                Flight(
                    flight_number=sd.flight_number,
                    route_id=route_id_by_pair[(sd.origin, sd.destination)],
                    aircraft_type=sd.aircraft_type,
                    aircraft_registration=sd.tail,
                    departure_scheduled=day_anchor + timedelta(hours=sd.dep_offset_h),
                    arrival_scheduled=day_anchor + timedelta(hours=sd.dep_offset_h + sd.duration_h),
                    status="scheduled" if is_last_day else "completed",
                )
            )
        day += timedelta(days=1)
    return flights


def seasonality_multiplier(day: date) -> float:
    """THY'nin bilinen yoğun dönemlerini (yaz, yılbaşı) kaba biçimde simüle eder
    -- gerçek bir talep tahmin modeli değil, dashboard trend grafiklerinde
    mevsimsel bir örüntü görülebilsin diye eklenen basit bir çarpan. Sadece
    talep HACMİNE uygulanır, $/kg fiyatlandırma modeline değil (çifte sayımı
    önlemek için)."""
    if day.month in (6, 7, 8):
        return 1.20
    if day.month == 12:
        return 1.15
    if day.month in (1, 2):
        return 0.85
    return 1.0


def calculate_revenue(route: Route, cargo_type: str, priority_class: str, weight_kg: float) -> float:
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


def random_request(flight: Flight, route: Route, cargo_type: str = None, priority_class: str = None) -> CargoRequest:
    weight = round(random.uniform(50, 3000), 1)
    volume = round(weight / random.uniform(150, 250), 2)
    cargo_type = cargo_type or random.choice(CARGO_TYPES)
    priority_class = priority_class or random.choice(PRIORITY_CLASSES)
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


def generate_requests_for_flight_instance(flight: Flight, route: Route, seasonality: float = 1.0) -> list[CargoRequest]:
    n_requests = max(1, round(random.randint(10, 18) * seasonality))
    return [random_request(flight, route) for _ in range(n_requests)]


def inject_weekly_guaranteed_conflicts(day: date, day_flights: list[Flight], route_by_id: dict) -> list[CargoRequest]:
    """
    Embargo (IST-JNB) ve kısıtlı-kargo (IST-NRT) senaryolarının rastgelelikten
    bağımsız, her hafta en az bir kez garanti test edilebilir kalması için: bu
    iki rotanın haftalık "enjeksiyon günü"nde (CONFLICT_INJECTION_WEEKDAY) o gün
    uçan ilgili uçuşlara birkaç "çakışan" talep elle ekleniyor. Her uçuş-gününde
    değil haftada bir yapılmasının nedeni: bir yıllık organik rastgele dağılım
    zaten kendiliğinden bol miktarda live_animal/dangerous_goods talebi üretiyor
    -- bu iki rotayı yapay şekilde aşırı çarpıtmamak için enjeksiyon sınırlı.
    """
    extra = []
    for flight in day_flights:
        route = route_by_id[flight.route_id]
        if route.destination_airport == "JNB" and day.weekday() == CONFLICT_INJECTION_WEEKDAY["JNB"]:
            extra.append(random_request(flight, route, cargo_type="live_animal"))
            extra.append(random_request(flight, route, cargo_type="live_animal"))
        elif route.destination_airport == "NRT" and day.weekday() == CONFLICT_INJECTION_WEEKDAY["NRT"]:
            extra.append(random_request(flight, route, cargo_type="dangerous_goods"))
            extra.append(random_request(flight, route, cargo_type="dangerous_goods"))
    return extra


def seed(db=None, window_end: datetime = WINDOW_END, window_days: int = WINDOW_DAYS):
    """
    db verilmezse gerçek (cargo.db) veritabanına yazar; verilirse (örn. testlerde
    izole bir in-memory session) o session üzerinde çalışır ve session'ı kapatmaz —
    kapatma sorumluluğu çağırana ait.

    window_end/window_days: [window_end - window_days + 1 gün, window_end] tarih
    aralığında günlük uçuş+kargo talebi üretir. Testler daha küçük bir pencere
    (örn. window_days=14) ile hızlı çalışır; varsayılan çağrı (`python -m
    app.seed_data`) tam 12 aylık pencereyi üretir.
    """
    owns_session = db is None
    if owns_session:
        # Şema artık Alembic tarafından yönetiliyor -- burada tablo oluşturmuyoruz.
        # `alembic upgrade head` çalıştırılmadan seed() çağrılırsa, tablo yok hatası
        # alınır; bu kasıtlı, kurulum sırasının (migration önce, seed sonra) açıkça
        # görünmesini sağlıyor.
        db = SessionLocal()

    # OptimizationResult önce silinmeli -- cargo_requests'e FK ile bağlı, aksi
    # halde bir sonraki seed çalıştırmasında orphan referanslar kalır.
    for model in [OptimizationResult, CargoRequest, Flight, Route, AircraftType, Airport]:
        db.query(model).delete()
    db.commit()

    airports = build_airports()
    db.add_all(airports)

    aircraft_types = build_aircraft_types()
    db.add_all(aircraft_types)
    db.commit()

    routes = build_routes()
    db.add_all(routes)
    db.commit()

    route_id_by_pair = {(r.origin_airport, r.destination_airport): r.route_id for r in routes}
    route_by_id = {r.route_id: r for r in routes}

    window_start_date = (window_end - timedelta(days=window_days - 1)).date()
    window_end_date = window_end.date()

    schedule_defs = build_flight_schedule_defs()
    flights = generate_flight_instances(schedule_defs, route_id_by_pair, window_start_date, window_end_date)
    db.add_all(flights)
    db.commit()

    flights_by_day = defaultdict(list)
    for flight in flights:
        flights_by_day[flight.departure_scheduled.date()].append(flight)

    n_freighter_flights = sum(1 for f in flights if f.aircraft_type in ("A330-200F", "B777F"))

    total_requests = 0
    day = window_start_date
    day_index = 0
    while day <= window_end_date:
        day_index += 1
        multiplier = seasonality_multiplier(day)
        day_flights = flights_by_day.get(day, [])

        day_requests = []
        for flight in day_flights:
            route = route_by_id[flight.route_id]
            day_requests.extend(generate_requests_for_flight_instance(flight, route, multiplier))
        day_requests.extend(inject_weekly_guaranteed_conflicts(day, day_flights, route_by_id))

        db.add_all(day_requests)
        db.commit()  # günlük commit -- bellek sınırlı kalır, ilerleme takip edilebilir
        total_requests += len(day_requests)

        if day_index % 30 == 0 or day == window_end_date:
            print(f"  ... {day_index}/{window_days} gün işlendi (şu ana kadar {total_requests} cargo_request)")

        day += timedelta(days=1)

    if owns_session:
        db.close()

    print(f"Seed tamamlandı: {len(airports)} airport, {len(aircraft_types)} aircraft_type, "
          f"{len(routes)} route, {len(flights)} flight ({n_freighter_flights} freighter-flight-instance), "
          f"{total_requests} cargo_request, pencere {window_start_date} .. {window_end_date}.")


if __name__ == "__main__":
    seed()
