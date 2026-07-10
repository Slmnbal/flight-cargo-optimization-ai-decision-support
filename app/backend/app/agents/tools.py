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
from app.models import CargoRequest, OptimizationResult, Flight, AircraftType
from app.rag.knowledge_base import search_knowledge_base as _search_knowledge_base


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
