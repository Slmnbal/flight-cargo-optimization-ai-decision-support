"""
Geçmişteki her gün için optimizasyonu çalıştırır -- bugün (pencerenin son
günü) HARİÇ, o gün kasıtlı olarak "pending" bırakılır ki dashboard'daki
"Optimizasyonu Çalıştır" aksiyonunun gerçek bir etkisi olsun (aksi halde
run_optimization tüm talepleri accepted/rejected yapar ve buton her zaman
no-op olur).

seed_data.py'den SONRA çalıştırılmalı: python -m app.backfill_history

Her gün için ayrı bir senaryo (`daily-YYYY-MM-DD`) üretilir -- mevcut
GET /results/{scenario_name} ve GET /kpis/{scenario_name} endpoint'leri bu
isimlendirmeyle değişmeden çalışır (örn. dashboard'da bir trend grafiği
noktasına tıklayıp o günün detayına inmek için).

Ayrı ve elle tetiklenen bir adım -- seed() veya testler tarafından otomatik
çağrılmaz, çünkü yüzlerce CBC çözümü (pencere başına bir) gözle görülür süre
alır.
"""
from datetime import date, datetime, time, timedelta

from app.database.connection import SessionLocal
from app.optimization.optimizer import run_optimization
from app.seed_data import WINDOW_DAYS, WINDOW_END


def backfill(db=None, window_end: datetime = WINDOW_END, window_days: int = WINDOW_DAYS, pending_days: int = 1):
    """
    pending_days: pencerenin sonundan itibaren optimizasyona TABİ TUTULMAYACAK
    gün sayısı (varsayılan 1 -- sadece "bugün" pending kalır).
    """
    owns_session = db is None
    if owns_session:
        db = SessionLocal()

    window_start_date = (window_end - timedelta(days=window_days - 1)).date()
    last_optimized_date = window_end.date() - timedelta(days=pending_days)

    day = window_start_date
    n_days = 0
    while day <= last_optimized_date:
        scenario_name = f"daily-{day.isoformat()}"
        run_at = datetime.combine(day, time(23, 0))
        result = run_optimization(db, scenario_name=scenario_name, flight_date=day, run_at=run_at)
        n_days += 1
        if n_days % 30 == 0:
            print(f"  ... {n_days} gün optimize edildi (son: {day}, durum: {result['status']})")
        day += timedelta(days=1)

    if owns_session:
        db.close()

    print(f"Backfill tamamlandı: {n_days} gün optimize edildi ({window_start_date} .. {last_optimized_date}). "
          f"{window_end.date()} kasıtlı olarak pending bırakıldı.")


if __name__ == "__main__":
    backfill()
