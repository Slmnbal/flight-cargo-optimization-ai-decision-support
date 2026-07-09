"""
Cargo kabul/red kararı veren optimizasyon motoru.

Karar değişkeni: x_i = 1 ise talep kabul edilir, 0 ise reddedilir.
Amaç fonksiyonu: maximize sum(revenue_i * x_i)

Kısıtlar (her uçuş için):
- toplam ağırlık ve hacim, o uçağın kapasitesini aşamaz.
- soğuk zincir gerektiren taleplerin toplam ağırlığı, uçağın soğuk zincir kapasitesini aşamaz.
- spot (sözleşmesiz) kargo, kapasitenin bir kısmını contract kargo için ayrılmış bırakacak
  şekilde sınırlanır (reserved capacity / korumalı kapasite).

Ayrıca, LP'ye hiç girmeden ön-filtre ile elenenler:
- embargo uygulanan rotalarda, embargo kapsamındaki kargo tipleri.
- tehlikeli madde (dangerous_goods) taşıması rota veya uçak tarafından izin verilmiyorsa.

Modelleme notu: embargo ve tehlikeli-madde kısıtları "karar değişkenini 0'a zorlayan bir
LP kısıtı" yerine, LP kurulmadan ÖNCE bir ön-filtre (pre-filter) olarak uygulanıyor.
İkisi matematiksel olarak eşdeğer ama pre-filter modeli küçültüyor ve mevcut
"status == pending" filtresiyle aynı örüntüyü sürdürüyor. Neden bu tercih edildi,
alternatifi ne olurdu: docs/adr/0001-cargo-optimization-constraints.md.
"""
import shutil
from collections import defaultdict

import pulp
from sqlalchemy.orm import Session

from app.models import CargoRequest, Flight, AircraftType, Route, OptimizationResult

# Her uçuşta kapasitenin bu yüzdesi spot (sözleşmesiz) kargoya kapalı, sadece contract
# kargo kullanabilir (reserved capacity / korumalı kapasite -- gerçek havayolu revenue
# management pratiğinde tipik oran %20-%40 arasıdır). Spot'u ÜSTTEN sınırlıyoruz,
# contract'a alt sınır koymuyoruz: contract talebi az olduğunda "en az X kg contract
# olmalı" gibi bir alt sınır modeli infeasible (çözümsüz) yapabilirdi; spot'u üstten
# sınırlamak model her zaman çözülebilir kalırken, contract talebi düşükse fazla
# kapasitenin spot tarafından doldurulmasına izin verir.
RESERVE_PCT = 0.30


def _is_dangerous_goods_blocked(req: CargoRequest, route: Route, aircraft: AircraftType) -> bool:
    """Tehlikeli madde, ilgili rota veya uçak tipi tarafından izin verilmiyorsa taşınamaz."""
    if req.cargo_type != "dangerous_goods":
        return False
    return not route.restricted_cargo_allowed or not aircraft.dangerous_goods_allowed


def _is_embargoed(req: CargoRequest, route: Route) -> bool:
    """
    Route.embargo_active=True iken kapsamı embargoed_cargo_types belirler:
    boş/None ise TÜM kargo tipleri, doluysa (virgülle ayrılmış liste) sadece
    listedeki tipler o rotada taşınamaz.
    """
    if not route.embargo_active:
        return False
    if not route.embargoed_cargo_types:
        return True
    embargoed_types = {t.strip() for t in route.embargoed_cargo_types.split(",")}
    return req.cargo_type in embargoed_types


def run_optimization(db: Session, scenario_name: str = "default") -> dict:
    requests = db.query(CargoRequest).filter(CargoRequest.status == "pending").all()

    if not requests:
        return {"status": "no_pending_requests", "accepted": [], "rejected": [], "total_revenue": 0.0}

    # N+1 query'den kaçınmak için: önce bu taleplerin kapsadığı benzersiz uçuş id'lerini
    # bul, her uçuş için TEK sorgu at (talep sayısı kadar değil). Route'u da burada
    # çözüyoruz -- optimizer artık embargo/kısıtlı-kargo kararları için Route'a bakıyor.
    unique_flight_ids = {req.flight_id for req in requests}
    flight_info = {}
    for flight_id in unique_flight_ids:
        flight = db.query(Flight).filter(Flight.flight_id == flight_id).first()
        aircraft = (
            db.query(AircraftType)
            .filter(AircraftType.aircraft_type == flight.aircraft_type)
            .first()
        )
        route = db.query(Route).filter(Route.route_id == flight.route_id).first()
        flight_info[flight_id] = {"aircraft": aircraft, "route": route}

    # --- Ön-filtre: embargo ve tehlikeli-madde kısıtlı talepler LP'ye hiç girmez ---
    eligible_requests = []
    pre_rejected = []  # (request, reason) çiftleri
    for req in requests:
        info = flight_info[req.flight_id]
        if _is_embargoed(req, info["route"]):
            pre_rejected.append((req, "embargo"))
        elif _is_dangerous_goods_blocked(req, info["route"], info["aircraft"]):
            pre_rejected.append((req, "dangerous_goods_restricted"))
        else:
            eligible_requests.append(req)

    problem = pulp.LpProblem("cargo_acceptance", pulp.LpMaximize)

    x = {req.request_id: pulp.LpVariable(f"x_{req.request_id}", cat="Binary") for req in eligible_requests}

    problem += pulp.lpSum(req.revenue * x[req.request_id] for req in eligible_requests)

    by_flight = defaultdict(list)
    for req in eligible_requests:
        by_flight[req.flight_id].append(req)

    for flight_id, reqs in by_flight.items():
        aircraft = flight_info[flight_id]["aircraft"]

        problem += pulp.lpSum(r.weight_kg * x[r.request_id] for r in reqs) <= aircraft.max_cargo_weight_kg
        problem += pulp.lpSum(r.volume_m3 * x[r.request_id] for r in reqs) <= aircraft.max_cargo_volume_m3

        # Soğuk zincir kısıtı: sadece requires_temperature_control=True olan taleplerin
        # toplam ağırlığı, uçağın soğuk zincir kapasitesini aşamaz. Ağırlık/hacim
        # kısıtlarıyla birebir aynı örüntü, tek fark filtre koşulu.
        problem += (
            pulp.lpSum(r.weight_kg * x[r.request_id] for r in reqs if r.requires_temperature_control)
            <= aircraft.temperature_controlled_capacity_kg
        )

        # Priority-class reserved capacity: spot talepler tek başına, kapasitenin
        # (1 - RESERVE_PCT)'ini aşamaz -- kalan RESERVE_PCT dilimi yapısal olarak
        # contract kargoya ayrılmış olur. Mevcut ağırlık kısıtına EK olarak çalışır,
        # onun yerine geçmez.
        problem += (
            pulp.lpSum(r.weight_kg * x[r.request_id] for r in reqs if r.priority_class == "spot")
            <= (1 - RESERVE_PCT) * aircraft.max_cargo_weight_kg
        )

    # Bazı mimarilerde (özellikle Apple Silicon Mac) PuLP'nin paket içine gömülü CBC
    # ikili dosyası çalışmayabilir ("Bad CPU type"). Önce sistemde kurulu bir CBC var mı
    # diye bakıyoruz (örn. `brew install cbc`), varsa onu kullanıyoruz; yoksa PuLP'nin
    # kendi bundled sürümüne düşüyoruz. Bu, kodun farklı işletim sistemi/mimarilerde
    # değişiklik yapmadan çalışmasını sağlıyor.
    system_cbc_path = shutil.which("cbc")
    solver = pulp.COIN_CMD(msg=False, path=system_cbc_path) if system_cbc_path else pulp.PULP_CBC_CMD(msg=False)
    problem.solve(solver)

    accepted, rejected = [], []
    for req in eligible_requests:
        decision = "accepted" if x[req.request_id].value() == 1 else "rejected"
        req.status = decision
        (accepted if decision == "accepted" else rejected).append(req.request_id)

        db.add(
            OptimizationResult(
                scenario_name=scenario_name,
                request_id=req.request_id,
                decision=decision,
                revenue=req.revenue if decision == "accepted" else 0.0,
                # Not: LP içinde hangi spesifik kısıtın (ağırlık/hacim/soğuk-zincir/
                # priority-reservation) bağlayıcı olduğunu dual value/slack incelemeden
                # ayırt edemiyoruz -- bu yüzden LP'nin reddettiği her talep için tek,
                # genel bir sebep kullanıyoruz. Bilinçli bir basitleştirme.
                reason=None if decision == "accepted" else "capacity_exceeded",
            )
        )

    for req, reason in pre_rejected:
        req.status = "rejected"
        rejected.append(req.request_id)
        db.add(
            OptimizationResult(
                scenario_name=scenario_name,
                request_id=req.request_id,
                decision="rejected",
                revenue=0.0,
                reason=reason,
            )
        )

    db.commit()

    total_revenue = sum(r.revenue for r in eligible_requests if r.status == "accepted")

    return {
        "status": pulp.LpStatus[problem.status],
        "accepted": accepted,
        "rejected": rejected,
        "total_revenue": total_revenue,
    }
