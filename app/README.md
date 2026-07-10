# Flight Cargo Optimization & AI Decision Support System

Havayolu/kargo operasyonlarında gelen kargo taşıma taleplerini, uçuş kapasitesini ve operasyonel kısıtları kullanarak hangi taleplerin kabul, hangilerinin reddedilmesi gerektiğine karar veren uçtan uca bir karar destek sistemi.

## Problem Tanımı

Bir havayolunun kargo operasyonunda, her uçuşun sınırlı bir ağırlık ve hacim kapasitesi vardır. Gelen kargo talepleri bu kapasiteyi aşabilir. Amaç, kapasite kısıtları içinde kalarak toplam geliri maksimize eden kabul/red kombinasyonunu bulmaktır. Bu klasik bir **matematiksel optimizasyon** (0-1 Integer Programming / Multiple Knapsack Problem) problemidir.

## Mimari

```
İstek (React + Vite Dashboard)
        │
        ▼
   FastAPI Backend  ──────►  SQLite / PostgreSQL
        │                    (routes, flights,
        ├──► Optimizasyon     cargo_requests, ...)
        │    Motoru (PuLP)
        │
        ├──► ML Modeli
        │    (kabul olasılığı)
        │
        └──► AI Agent
             (Gemini + tool calling)
```

Katmanlar birbirinden bağımsız: veritabanı SQLAlchemy ORM ile soyutlanmış (SQLite ve PostgreSQL ikisi de destekleniyor, tek env değişkeniyle seçiliyor), optimizasyon motoru saf Python/PuLP (herhangi bir framework'e bağımlı değil), API bu ikisini dışarıya REST olarak açıyor, arayüz sadece API'yi tüketiyor.

## Veritabanı Şeması

6 çekirdek tablo: `airports`, `aircraft_types` (referans tabloları), `routes`, `flights`, `cargo_requests`, `optimization_results`. Detaylı şema için bkz. proje kökündeki `docs/database_schema.md`. Şema, Alembic ile yönetiliyor (bkz. `app/backend/alembic/`) — `Base.metadata.create_all()` artık kullanılmıyor.

`flights`/`cargo_requests`, tek bir güne değil **12 aylık, günlük tekrarlayan bir uçuş takvimine** yayılıyor (bkz. `app/backend/app/seed_data.py`) — aynı `flight_number`, pencere boyunca haftanın belirli günlerinde (`weekdays` pattern'i) birden fazla tarihli `Flight` satırında tekrar kullanılıyor. Pencerenin son günü (bugün) kasıtlı olarak `pending`/`scheduled` bırakılıyor; önceki günler `python -m app.backfill_history` ile `daily-YYYY-MM-DD` adlı ayrı senaryolara optimize ediliyor (bkz. aşağıdaki "Nasıl Çalıştırılır").

## Veritabanı: SQLite (varsayılan) veya PostgreSQL

`DATABASE_URL` ortam değişkeni tanımlı değilse `sqlite:///./cargo.db` kullanılır (kurulum gerektirmez). PostgreSQL'e geçmek için `.env`'e `DATABASE_URL=postgresql://user:pass@host:5432/dbname` eklemek yeterli — kod saf SQLAlchemy ORM kullanıyor, dialect'e özel hiçbir şey yok.

Şema değişikliklerini Alembic uyguluyor:
```bash
cd app/backend
alembic upgrade head       # şemayı güncel migration seviyesine getirir
alembic revision --autogenerate -m "..."   # bir model değişikliğinden sonra yeni migration üretir
```
Docker Compose ile çalıştırıldığında (`docker compose up`), backend konteyneri her başladığında `alembic upgrade head`'i otomatik çalıştırır (bkz. `app/backend/Dockerfile`), ve Postgres servisi (`db`) sağlıklı hale gelene kadar bekler.

## Optimizasyon Modeli

Karar değişkeni: `x_i ∈ {0,1}` (talep i kabul/red). Amaç fonksiyonu: `maximize Σ revenue_i * x_i`. Kısıtlar: her uçuş için ağırlık/hacim kapasitesi, soğuk zincir kapasitesi, embargo (rota+kargo-tipine-özel), tehlikeli madde taşıma izni, ve priority-class (contract kargo için ayrılmış/korumalı kapasite). CBC solver (açık kaynak) ile çözülüyor. Tasarım kararları için bkz. `docs/adr/0001-cargo-optimization-constraints.md`.

## API Endpointleri

| Endpoint | Açıklama |
|---|---|
| `GET /routes`, `/aircraft-types` | Referans verisini listeler |
| `GET /flights`, `/cargo-requests` | Sayfalanmış + filtrelenebilir liste (`date_from`, `date_to`, `route_id`/`flight_id`, `status`, `cargo_type`, `priority_class`, `limit`, `offset`) — `{items, total}` şeklinde döner |
| `GET /flights/{flight_id}/capacity-utilization` | Bir uçuşun ağırlık/hacim kapasite kullanım yüzdesi |
| `GET /results/{scenario_name}` | Bir senaryonun kabul/red satırları |
| `GET /kpis/{scenario_name}` | Bir senaryonun toplu KPI özeti |
| `GET /kpis/trend?group_by=day\|week\|month` | Dönem bazlı gelir/kabul-red/kapasite trend serisi (dashboard grafiği için) |
| `POST /optimize?scenario_name=...` | Optimizasyonu çalıştırır, kabul/red kararlarını döndürür ve kaydeder |
| `POST /ml/train` | Geçmiş sonuçlardan kabul olasılığı modeli eğitir |
| `GET /ml/predict/{request_id}` | Bir talebin kabul olasılığını tahmin eder |
| `POST /agent/ask` | AI Agent'a doğal dilde soru sorar |

Tam interaktif dokümantasyon: sunucu çalışırken `http://localhost:8000/docs`.

## AI Agent

Google Gemini API ile **tool calling** kullanılıyor. Agent, kullanıcı sorusuna göre hangi fonksiyonu çağıracağına kendisi karar veriyor:

- `get_accepted_requests`, `get_rejected_requests`, `calculate_capacity_utilization`, `explain_request_decision`: **canlı veritabanı** sorguları (sayısal/güncel veri).
- `search_knowledge_base`: `docs/business_rules.md` ve ADR'ler üzerinde **RAG** (retrieval-augmented generation) — "priority_class nasıl işliyor", "neden embargo var" gibi kavramsal sorular için. Embedding Gemini'nin `embed_content` API'siyle üretiliyor, Chroma'da (`app/backend/app/rag/store/`, gitignored) saklanıyor. Kurmak/güncellemek için: `python -m app.rag.ingest_docs`.

Guardrail: agent sadece bu tool'ların döndürdüğü gerçek veriye/dokümana dayanır, veri uydurmaz, solver kararını değiştirmez, canlı veri ile dokümantasyon kaynaklı bilgiyi karıştırmaz (bkz. `app/backend/app/agents/explainer.py`).

**Hafıza:** `/agent/ask` bir `session_id` alır/döner. Aynı `session_id` ile art arda soru sorulduğunda, agent önceki turları hatırlar (son 20 mesaj, bkz. `app/backend/app/services/agent_service.py`) — `session_id` verilmezse her soru sıfırdan, hafızasız bir konuşma başlatır.

## Nasıl Çalıştırılır

### Yerel (venv ile)

```bash
cd app/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head    # şemayı oluşturur (varsayılan: sqlite:///./cargo.db)
python -m app.seed_data          # 12 aylık uçuş+kargo talebi verisi üretir
python -m app.backfill_history   # geçmiş her günü optimize eder (bugün hariç, "pending" kalır)
uvicorn app.main:app --reload
```

Ayrı bir terminalde (React + Vite dashboard):
```bash
cd app/frontend
npm install
cp .env.example .env   # VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

### Docker ile

```bash
cd app
docker compose up --build
```

Backend: `http://localhost:8000/docs` — Frontend: `http://localhost:8080`

Not: Docker Compose ile çalıştırıldığında `seed_data`/`backfill_history` otomatik çalışmıyor — ilk kurulumda backend konteynerine girip (`docker compose exec backend sh`) elle çalıştırman gerekir.

### Gemini API Key (opsiyonel, AI Agent için)

`app/backend/.env` dosyasına ekle:
```
GEMINI_API_KEY=your_key_here
```
Ücretsiz key: https://aistudio.google.com/apikey — key tanımlı değilse sistem çalışmaya devam eder, agent sadece "key eksik" mesajı döner.

## Testler

```bash
cd app/backend
pytest -v
```

## Kariyer Bağlantısı

Bu proje; veritabanı tasarımı, matematiksel optimizasyon (Operations Research), makine öğrenmesi, backend/API geliştirme ve LLM tabanlı AI Agent geliştirme yetkinliklerini tek bir gerçekçi problem üzerinde birleştiriyor. Detaylar için proje kökündeki `docs/project_overview.md` ve `docs/dev_principles_guide.md`.
