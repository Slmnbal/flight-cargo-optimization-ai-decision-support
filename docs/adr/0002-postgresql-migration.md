# ADR 0002: PostgreSQL Desteği — Dual-Support (SQLite Fallback ile)

## Durum
Kabul edildi (2026-07-09).

## Bağlam

MVP'de `DATABASE_URL` sabit kodlanmıştı (`sqlite:///./cargo.db`), env değişkeninden
okunmuyordu, ve şema `Base.metadata.create_all()` ile örtük olarak oluşturuluyordu —
migration aracı yoktu. Derinleştirme fazının hedefi PostgreSQL desteği eklemekti; iki
seçenek vardı: SQLite'ı tamamen bırakıp Postgres'i zorunlu kılmak, ya da ikisini birlikte
desteklemek.

## Karar — İkisini de destekle (dual-support)

`DATABASE_URL` env değişkeni tanımlı değilse `sqlite:///./cargo.db`'ye düşülüyor
(`app/config.py`); Docker Compose bunu Postgres URL'iyle override ediyor. Gerekçe: proje
kod tabanı **saf SQLAlchemy ORM** kullanıyor — hiçbir raw SQL, hiçbir Postgres'e özgü
tip/fonksiyon (JSONB, array kolonları, window function'lar vb.) yok. Bu durumda iki
dialect'i desteklemek neredeyse bedava geliyor; tek gerçek dialect-özel detay
`check_same_thread` bayrağıydı (SQLite'a özgü, `connection.py`'de artık koşullu).

Bu karar, `docs/project_overview.md`'nin "ücretsiz/açık araçlarla kal, düşük bariyer"
felsefesiyle uyumlu: `git clone` → `venv` → `alembic upgrade head` → `seed_data.py` →
`uvicorn` akışı hâlâ hiçbir DB kurulumu gerektirmiyor, ama `DATABASE_URL` verilerek
production-benzeri bir Postgres'e de sorunsuz geçilebiliyor. pytest'in kendi test
fixture'ı (`tests/conftest.py`) zaten izole bir in-memory SQLite kullanıyor ve bu
karardan hiç etkilenmiyor.

## Karar — Şema yönetimi: Alembic, `create_all()` değil

`Base.metadata.create_all()` iki yerde (`main.py`, `seed_data.py`) örtük çalışıyordu.
Alembic devreye girdiğinde bu çağrılar kaldırıldı — aksi halde SQLAlchemy, Alembic'in
haberi olmadığı tabloları sessizce oluşturabilir (`alembic_version` satırı hiç
yazılmaz), bu da ileride "table already exists" hatasına ya da fark edilmeyen şema
sürüklenmesine (drift) yol açar. Bunun bedeli: kurulum artık bir adım daha uzun
(`alembic upgrade head` seed'den önce çalıştırılmalı) — ama bu, gerçek production
deploy'ların çalışma şekli, ve README'de açıkça belgelendi.

## Bilinen sınırlama

Bu ortamda Docker daemon çalışır durumda değildi, bu yüzden `docker compose up --build`
ile gerçek bir Postgres konteynerine karşı uçtan uca doğrulama yapılamadı. Doğrulanan
kısımlar: `docker compose config` ile compose dosyasının söz dizimi/servis bağımlılık
grafiği geçerli; SQLite yolu (Alembic migration + seed + tüm pytest testleri + canlı
`/optimize` çağrısı) uçtan uca çalıştı; `psycopg2-binary` sürücüsü kuruldu ve import
edilebiliyor. Postgres'e karşı gerçek bir `alembic upgrade head` + `seed_data.py`
çalıştırması, Docker Desktop (veya yerel bir Postgres) mevcut olduğunda yapılmalı —
bu, Package C'nin resmi olarak "tamamlandı" sayılmadan önceki son doğrulama adımı.
