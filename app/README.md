# Flight Cargo Optimization & AI Decision Support System

Havayolu/kargo operasyonlarında gelen kargo taşıma taleplerini, uçuş kapasitesini ve operasyonel kısıtları kullanarak hangi taleplerin kabul, hangilerinin reddedilmesi gerektiğine karar veren uçtan uca bir karar destek sistemi.

## Problem Tanımı

Bir havayolunun kargo operasyonunda, her uçuşun sınırlı bir ağırlık ve hacim kapasitesi vardır. Gelen kargo talepleri bu kapasiteyi aşabilir. Amaç, kapasite kısıtları içinde kalarak toplam geliri maksimize eden kabul/red kombinasyonunu bulmaktır. Bu klasik bir **matematiksel optimizasyon** (0-1 Integer Programming / Multiple Knapsack Problem) problemidir.

## Mimari

```
İstek (Streamlit UI)
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
| `GET /routes`, `/flights`, `/cargo-requests` | Veriyi listeler |
| `POST /optimize?scenario_name=...` | Optimizasyonu çalıştırır, kabul/red kararlarını döndürür ve kaydeder |
| `POST /ml/train` | Geçmiş sonuçlardan kabul olasılığı modeli eğitir |
| `GET /ml/predict/{request_id}` | Bir talebin kabul olasılığını tahmin eder |
| `POST /agent/ask` | AI Agent'a doğal dilde soru sorar |

Tam interaktif dokümantasyon: sunucu çalışırken `http://localhost:8000/docs`.

## AI Agent

Google Gemini API ile **tool calling** kullanılıyor. Agent, kullanıcı sorusuna göre hangi fonksiyonu (`get_accepted_requests`, `get_rejected_requests`, `calculate_capacity_utilization`, `explain_request_decision`) çağıracağına kendisi karar veriyor. Guardrail: agent sadece bu fonksiyonların döndürdüğü gerçek veriye dayanır, veri uydurmaz, solver kararını değiştirmez (bkz. `app/backend/app/agents/explainer.py`).

## Nasıl Çalıştırılır

### Yerel (venv ile)

```bash
cd app/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head    # şemayı oluşturur (varsayılan: sqlite:///./cargo.db)
python -m app.seed_data
uvicorn app.main:app --reload
```

Ayrı bir terminalde:
```bash
cd app/frontend
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Docker ile

```bash
cd app
docker compose up --build
```

Backend: `http://localhost:8000/docs` — Frontend: `http://localhost:8501`

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
