"""
backfill_history.py'nin, geçmiş her gün için ayrı bir `daily-YYYY-MM-DD`
senaryosu ürettiğini ve pencerenin son gününü (bugünü) kasıtlı olarak
optimize etmeden "pending" bıraktığını doğrular -- bu, dashboard'daki
"Optimizasyonu Çalıştır" aksiyonunun her zaman no-op olmamasını garanti eden
kritik bir davranış.
"""
from app.backfill_history import backfill
from app.models import CargoRequest, Flight, OptimizationResult
from app.seed_data import WINDOW_END, seed


def test_backfill_leaves_final_day_pending_and_names_scenarios_per_day(db_session):
    seed(db=db_session, window_days=7)
    backfill(db=db_session, window_days=7, pending_days=1)

    scenarios = {r.scenario_name for r in db_session.query(OptimizationResult).all()}
    assert scenarios == {f"daily-2026-07-{day:02d}" for day in range(9, 15)}

    final_day_flight_ids = {
        f.flight_id for f in db_session.query(Flight).all()
        if f.departure_scheduled >= WINDOW_END
    }
    final_day_requests = [
        r for r in db_session.query(CargoRequest).all() if r.flight_id in final_day_flight_ids
    ]
    assert final_day_requests  # son gün gerçekten talep içeriyor olmalı (aksi halde test anlamsız)
    assert all(r.status == "pending" for r in final_day_requests)

    earlier_requests = [
        r for r in db_session.query(CargoRequest).all() if r.flight_id not in final_day_flight_ids
    ]
    assert all(r.status in ("accepted", "rejected") for r in earlier_requests)
