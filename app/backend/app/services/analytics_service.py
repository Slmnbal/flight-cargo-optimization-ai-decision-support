"""
Senaryo/rota bazlı aggregation mantığı -- ne saf HTTP katmanına (api/routes.py)
ne de LLM konuşma mantığına (agents/explainer.py) ait olduğu için burada,
services/ altında (bkz. agent_service.py'nin kendi docstring'indeki aynı
gerekçe). Hem REST endpoint'leri (`/kpis/{scenario_name}`, `/scenarios`) hem
de AI Agent tool'ları (agents/tools.py) bu fonksiyonları çağırıyor -- aynı
hesaplama iki yerde ayrı ayrı yazılmıyor.

Ortak desen: ilgili OptimizationResult satırlarını tek sorguda çekip
Python'da grupla/aggregate et -- `/kpis/trend` ve `/scenarios`'ta zaten
kanıtlanmış bir yaklaşım (~106k satırda hızlı çalışıyor), burada da aynı
yaklaşım tekrarlanıyor.
"""
from collections import Counter

from sqlalchemy.orm import Session

from app.models import CargoRequest, Flight, OptimizationResult, Route


def get_scenario_kpi_summary(db: Session, scenario_name: str) -> dict | None:
    """Bir senaryonun toplu KPI özetini döndürür. Senaryo hiç çalışmamışsa None."""
    rows = db.query(OptimizationResult).filter(OptimizationResult.scenario_name == scenario_name).all()
    if not rows:
        return None

    accepted = [r for r in rows if r.decision == "accepted"]
    rejected = [r for r in rows if r.decision == "rejected"]
    reason_breakdown = Counter(r.reason for r in rejected if r.reason)

    return {
        "scenario_name": scenario_name,
        "total_requests": len(rows),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "total_revenue": sum(r.revenue for r in accepted),
        "rejection_reason_breakdown": dict(reason_breakdown),
        "last_run_at": max(r.run_at for r in rows),
    }


def list_scenario_summaries(db: Session, limit: int, offset: int) -> tuple[list[dict], int]:
    """Şimdiye kadar çalıştırılmış tüm senaryoları, en son çalışandan başlayarak
    özetler. (items, total) döner -- total, limit/offset uygulanmadan önceki
    toplam senaryo sayısı."""
    buckets: dict[str, dict] = {}
    for result in db.query(OptimizationResult).all():
        bucket = buckets.setdefault(result.scenario_name, {
            "total_requests": 0, "accepted_count": 0, "rejected_count": 0,
            "total_revenue": 0.0, "last_run_at": result.run_at,
        })
        bucket["total_requests"] += 1
        if result.decision == "accepted":
            bucket["accepted_count"] += 1
            bucket["total_revenue"] += result.revenue
        else:
            bucket["rejected_count"] += 1
        if result.run_at > bucket["last_run_at"]:
            bucket["last_run_at"] = result.run_at

    summaries = sorted(
        (
            {"scenario_name": name, "total_revenue": round(b["total_revenue"], 2), **{k: v for k, v in b.items() if k != "total_revenue"}}
            for name, b in buckets.items()
        ),
        key=lambda s: s["last_run_at"],
        reverse=True,
    )

    return summaries[offset : offset + limit], len(summaries)


def get_route_statistics(db: Session, origin_airport: str, destination_airport: str) -> dict | None:
    """Bir rotanın statik bilgisini (mesafe, bölge, embargo/kısıt) ve o
    rotadaki tüm geçmiş optimizasyon sonuçlarının (kabul/red/gelir) özetini
    döndürür. Rota bulunamazsa None."""
    route = (
        db.query(Route)
        .filter(
            Route.origin_airport == origin_airport.upper(),
            Route.destination_airport == destination_airport.upper(),
        )
        .first()
    )
    if route is None:
        return None

    rows = (
        db.query(OptimizationResult)
        .join(CargoRequest, OptimizationResult.request_id == CargoRequest.request_id)
        .join(Flight, CargoRequest.flight_id == Flight.flight_id)
        .filter(Flight.route_id == route.route_id)
        .all()
    )
    accepted = [r for r in rows if r.decision == "accepted"]
    rejected = [r for r in rows if r.decision == "rejected"]
    reason_breakdown = Counter(r.reason for r in rejected if r.reason)

    return {
        "origin_airport": route.origin_airport,
        "destination_airport": route.destination_airport,
        "region": route.region,
        "distance_km": route.distance_km,
        "embargo_active": route.embargo_active,
        "embargoed_cargo_types": route.embargoed_cargo_types,
        "restricted_cargo_allowed": route.restricted_cargo_allowed,
        "total_requests": len(rows),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "total_revenue": round(sum(r.revenue for r in accepted), 2),
        "rejection_reason_breakdown": dict(reason_breakdown),
    }


def get_top_routes_by_revenue(db: Session, limit: int) -> list[dict]:
    """Kabul edilen kargo talepleri toplam gelirine göre en yüksek gelirli
    rotaları azalan sırada döndürür (tüm senaryolar/tarihler dahil)."""
    rows = (
        db.query(OptimizationResult, Route)
        .join(CargoRequest, OptimizationResult.request_id == CargoRequest.request_id)
        .join(Flight, CargoRequest.flight_id == Flight.flight_id)
        .join(Route, Flight.route_id == Route.route_id)
        .filter(OptimizationResult.decision == "accepted")
        .all()
    )

    buckets: dict[int, dict] = {}
    for result, route in rows:
        bucket = buckets.setdefault(route.route_id, {
            "origin_airport": route.origin_airport,
            "destination_airport": route.destination_airport,
            "region": route.region,
            "total_revenue": 0.0,
            "accepted_count": 0,
        })
        bucket["total_revenue"] += result.revenue
        bucket["accepted_count"] += 1

    ranked = sorted(buckets.values(), key=lambda b: b["total_revenue"], reverse=True)
    for bucket in ranked:
        bucket["total_revenue"] = round(bucket["total_revenue"], 2)
    return ranked[:limit]
