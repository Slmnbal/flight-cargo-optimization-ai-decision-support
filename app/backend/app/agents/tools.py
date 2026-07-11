"""
AI Agent'ın kullanabileceği "tool"lar (fonksiyonlar).

Önemli prensip: bu fonksiyonların her biri veritabanından GERÇEK veri okuyor,
hiçbir sayı ya da karar uydurmuyor. Agent, kullanıcı sorusuna cevap verirken
sadece bu fonksiyonların döndürdüğü sonuçlara dayanmak zorunda - bu bizim
temel guardrail'imiz (bkz. explainer.py).

Docstring'ler ve type hint'ler burada süs değil: Gemini SDK, bir fonksiyonu
"tool" olarak kullanabilmek için onun ne işe yaradığını (docstring) ve hangi
parametreleri beklediğini (type hint) otomatik olarak buradan çıkarıyor.
"""
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models import CargoRequest, OptimizationResult, Flight, AircraftType, Route
from app.ml.demand_forecast import load_model as _load_ml_model, predict_acceptance_probability as _predict_acceptance_probability
from app.rag.knowledge_base import search_knowledge_base as _search_knowledge_base
from app.services import analytics_service


def get_accepted_requests(scenario_name: str) -> list[dict]:
    """Belirli bir senaryoda kabul edilen kargo taleplerinin listesini döndürür.

    Args:
        scenario_name: Optimizasyon çalıştırılırken verilen senaryo adı (örn. 'default').
    """
    db = SessionLocal()
    try:
        results = (
            db.query(OptimizationResult)
            .filter(OptimizationResult.scenario_name == scenario_name, OptimizationResult.decision == "accepted")
            .all()
        )
        return [{"request_id": r.request_id, "revenue": r.revenue} for r in results]
    finally:
        db.close()


def get_rejected_requests(scenario_name: str) -> list[dict]:
    """Belirli bir senaryoda reddedilen kargo taleplerinin listesini döndürür.

    Args:
        scenario_name: Optimizasyon çalıştırılırken verilen senaryo adı (örn. 'default').
    """
    db = SessionLocal()
    try:
        results = (
            db.query(OptimizationResult)
            .filter(OptimizationResult.scenario_name == scenario_name, OptimizationResult.decision == "rejected")
            .all()
        )
        return [{"request_id": r.request_id} for r in results]
    finally:
        db.close()


def get_scenario_kpi_summary(scenario_name: str) -> dict:
    """Belirli bir senaryonun toplu KPI özetini döndürür: toplam talep sayısı,
    kabul/red sayısı, toplam gelir, red sebeplerinin dağılımı ve son çalışma
    zamanı. 'Bu senaryonun sonucu ne oldu', 'toplam gelir ne kadardı' gibi
    özet sorularda get_accepted_requests/get_rejected_requests'in ham liste
    döndürmesi yerine bunu kullan.

    Args:
        scenario_name: Optimizasyon çalıştırılırken verilen senaryo adı (örn.
            'live' ya da backfill'in ürettiği 'daily-2026-07-10').
    """
    db = SessionLocal()
    try:
        summary = analytics_service.get_scenario_kpi_summary(db, scenario_name)
        if summary is None:
            return {"error": f"'{scenario_name}' adlı senaryo için sonuç bulunamadı"}
        return summary
    finally:
        db.close()


def list_recent_scenarios(limit: int = 10) -> list[dict]:
    """En son çalıştırılan optimizasyon senaryolarını (canlı çalıştırmalar +
    geçmişe dönük backfill günleri), en yeniden en eskiye doğru, kısa özetleriyle
    listeler. 'Hangi senaryolar var', 'en son ne zaman optimizasyon çalıştı'
    gibi sorularda kullan.

    Args:
        limit: Kaç senaryo döndürüleceği (varsayılan 10).
    """
    db = SessionLocal()
    try:
        # Gemini'nin function calling'i int tipli parametreleri bazen float
        # olarak gönderiyor (örn. 10.0) -- list[:limit] slicing'i bunu kabul
        # etmiyor, bu yüzden burada (sistem sınırında) açıkça int'e çeviriyoruz.
        items, _total = analytics_service.list_scenario_summaries(db, limit=int(limit), offset=0)
        return items
    finally:
        db.close()


def get_route_statistics(origin_airport: str, destination_airport: str) -> dict:
    """Bir rotanın statik bilgisini (mesafe, bölge, embargo/tehlikeli-madde
    kısıtı) ve o rotadaki TÜM geçmiş optimizasyon sonuçlarının (kaç talep,
    kabul/red oranı, toplam gelir, red sebepleri) özetini döndürür. 'IST-JNB
    rotasında kabul oranı ne', 'bu rota ne kadar gelir getirdi' gibi rota
    bazlı sorularda kullan.

    Args:
        origin_airport: Kalkış havalimanı IATA kodu (örn. 'IST').
        destination_airport: Varış havalimanı IATA kodu (örn. 'JNB').
    """
    db = SessionLocal()
    try:
        stats = analytics_service.get_route_statistics(db, origin_airport, destination_airport)
        if stats is None:
            return {"error": f"{origin_airport}-{destination_airport} rotası bulunamadı"}
        return stats
    finally:
        db.close()


def get_top_routes_by_revenue(limit: int = 5) -> list[dict]:
    """Kabul edilen kargo talepleri toplam gelirine göre en yüksek gelirli
    rotaları (tüm senaryolar/tarihler dahil) azalan sırada listeler. 'En
    karlı rota hangisi', 'en çok gelir getiren 3 rota' gibi sıralama/kıyaslama
    sorularında kullan.

    Args:
        limit: Kaç rota döndürüleceği (varsayılan 5).
    """
    db = SessionLocal()
    try:
        # bkz. list_recent_scenarios'taki aynı not: Gemini int parametreyi
        # float gönderebiliyor, slicing için açıkça int'e çeviriyoruz.
        return analytics_service.get_top_routes_by_revenue(db, int(limit))
    finally:
        db.close()


def _predict_for_request(db: Session, model, request_id: int) -> dict:
    """predict_acceptance_probability_for_request'in db/model enjekte edilebilir
    hali -- testte gerçek bir eğitilmiş model yerine sahte bir predict_proba
    nesnesi verilebilsin diye ayrıldı (bkz. _capacity_utilization'daki aynı gerekçe)."""
    request = db.query(CargoRequest).filter(CargoRequest.request_id == request_id).first()
    if request is None:
        return {"error": f"request_id {request_id} bulunamadı"}

    probability = _predict_acceptance_probability(model, request.weight_kg, request.volume_m3, request.revenue)
    return {"request_id": request_id, "acceptance_probability": round(probability, 4)}


def predict_acceptance_probability_for_request(request_id: int) -> dict:
    """Eğitilmiş ML modelini kullanarak bir kargo talebinin kabul edilme
    olasılığını tahmin eder. Model henüz eğitilmemişse (bkz. POST /ml/train)
    ya da request_id bulunamazsa hata döner. 'Bu talep kabul edilir mi',
    'X numaralı talebin kabul olasılığı ne' gibi sorularda kullan -- bu,
    solver'ın kesin kararı DEĞİL, geçmiş verilerden öğrenilmiş bir olasılık
    tahminidir.

    Args:
        request_id: Tahmin yapılacak kargo talebinin ID'si.
    """
    model = _load_ml_model()
    if model is None:
        return {"error": "ML modeli henüz eğitilmedi. Önce POST /ml/train çağrılmalı."}

    db = SessionLocal()
    try:
        return _predict_for_request(db, model, request_id)
    finally:
        db.close()


def _aircraft_type_specs(db: Session, aircraft_type: str) -> dict:
    aircraft = db.query(AircraftType).filter(AircraftType.aircraft_type == aircraft_type).first()
    if aircraft is None:
        return {"error": f"'{aircraft_type}' adlı uçak tipi bulunamadı"}
    return {
        "aircraft_type": aircraft.aircraft_type,
        "max_cargo_weight_kg": aircraft.max_cargo_weight_kg,
        "max_cargo_volume_m3": aircraft.max_cargo_volume_m3,
        "temperature_controlled_capacity_kg": aircraft.temperature_controlled_capacity_kg,
        "is_freighter": aircraft.is_freighter,
        "dangerous_goods_allowed": aircraft.dangerous_goods_allowed,
    }


def get_aircraft_type_specs(aircraft_type: str) -> dict:
    """Bir uçak tipinin kargo kapasitesi özelliklerini döndürür: max ağırlık/
    hacim, soğuk zincir kapasitesi, freighter olup olmadığı, tehlikeli madde
    taşıyıp taşıyamayacağı. 'A330-200F'in kapasitesi ne', 'B777F tehlikeli
    madde taşıyabilir mi' gibi uçak tipi referans sorularında kullan.

    Args:
        aircraft_type: Uçak tipi kodu (örn. 'A330-200F', 'B777F', 'A321NEO').
    """
    db = SessionLocal()
    try:
        return _aircraft_type_specs(db, aircraft_type)
    finally:
        db.close()


def _restricted_routes(db: Session) -> list[dict]:
    routes = (
        db.query(Route)
        .filter(Route.embargo_active.is_(True) | Route.restricted_cargo_allowed.is_(False))
        .all()
    )
    return [
        {
            "origin_airport": r.origin_airport,
            "destination_airport": r.destination_airport,
            "embargo_active": r.embargo_active,
            "embargoed_cargo_types": r.embargoed_cargo_types,
            "restricted_cargo_allowed": r.restricted_cargo_allowed,
        }
        for r in routes
    ]


def list_restricted_routes() -> list[dict]:
    """Embargo uygulanan ya da tehlikeli madde taşımasına izin vermeyen tüm
    rotaları, kısıtın kapsamıyla birlikte listeler. 'Hangi rotalar embargolu',
    'tehlikeli madde hangi rotalarda kısıtlı' gibi sorularda kullan.
    """
    db = SessionLocal()
    try:
        return _restricted_routes(db)
    finally:
        db.close()


def _capacity_utilization(db: Session, flight_id: int) -> dict:
    """
    calculate_capacity_utilization'ın gerçek mantığı -- hem Gemini tool'u hem
    de GET /flights/{flight_id}/capacity-utilization endpoint'i bu private
    fonksiyonu paylaşır. Ayrı tutulmasının nedeni: Gemini SDK, tool olarak
    kullanılan fonksiyonun imzasını (type hint'ler dahil) otomatik olarak LLM
    tool şemasına çeviriyor -- bir `db: Session` parametresi eklemek bu şemayı
    kirletirdi. Bu yüzden LLM'e görünen `calculate_capacity_utilization(flight_id)`
    imzası değişmeden kalıyor, REST endpoint'i ise kendi DI session'ını buraya verir.
    """
    flight = db.query(Flight).filter(Flight.flight_id == flight_id).first()
    if flight is None:
        return {"error": f"flight_id {flight_id} bulunamadı"}

    aircraft = db.query(AircraftType).filter(AircraftType.aircraft_type == flight.aircraft_type).first()
    accepted = (
        db.query(CargoRequest)
        .filter(CargoRequest.flight_id == flight_id, CargoRequest.status == "accepted")
        .all()
    )
    used_weight = sum(r.weight_kg for r in accepted)
    used_volume = sum(r.volume_m3 for r in accepted)

    return {
        "flight_id": flight_id,
        "flight_number": flight.flight_number,
        "weight_utilization_pct": round(100 * used_weight / aircraft.max_cargo_weight_kg, 1),
        "volume_utilization_pct": round(100 * used_volume / aircraft.max_cargo_volume_m3, 1),
    }


def calculate_capacity_utilization(flight_id: int) -> dict:
    """Bir uçuşun ağırlık ve hacim kapasitesinin yüzde kaçının kullanıldığını hesaplar.

    Args:
        flight_id: Kapasite kullanımı hesaplanacak uçuşun ID'si.
    """
    db = SessionLocal()
    try:
        return _capacity_utilization(db, flight_id)
    finally:
        db.close()


def explain_request_decision(request_id: int) -> dict:
    """Belirli bir kargo talebinin neden kabul veya reddedildiğine dair ham gerçekleri döndürür.

    Args:
        request_id: Açıklanacak kargo talebinin ID'si.
    """
    db = SessionLocal()
    try:
        request = db.query(CargoRequest).filter(CargoRequest.request_id == request_id).first()
        if request is None:
            return {"error": f"request_id {request_id} bulunamadı"}

        result = (
            db.query(OptimizationResult)
            .filter(OptimizationResult.request_id == request_id)
            .order_by(OptimizationResult.run_at.desc())
            .first()
        )
        if result is None:
            return {"error": "Bu talep için henüz bir optimizasyon çalıştırılmadı"}

        flight = db.query(Flight).filter(Flight.flight_id == request.flight_id).first()
        aircraft = db.query(AircraftType).filter(AircraftType.aircraft_type == flight.aircraft_type).first()

        return {
            "request_id": request_id,
            "decision": result.decision,
            "revenue": request.revenue,
            "weight_kg": request.weight_kg,
            "volume_m3": request.volume_m3,
            "priority_class": request.priority_class,
            "flight_number": flight.flight_number,
            "flight_max_weight_kg": aircraft.max_cargo_weight_kg,
            "flight_max_volume_m3": aircraft.max_cargo_volume_m3,
        }
    finally:
        db.close()


def search_knowledge_base(query: str) -> list[str]:
    """Projenin kendi tasarım dokümantasyonundan (iş kuralları, kısıt gerekçeleri,
    ADR'ler) kullanıcının sorusuyla en alakalı metin parçalarını getirir. Canlı
    veritabanı verisi DEĞİLDİR -- 'neden embargo var', 'priority_class nasıl
    işliyor', 'reserved capacity ne demek' gibi kavramsal/tasarım sorularında kullan.

    Args:
        query: Kullanıcının kavramsal/tasarım sorusu.
    """
    return _search_knowledge_base(query)
