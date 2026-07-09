# Flight Cargo Optimization & AI Decision Support System

Havayolu/kargo operasyonlarında gelen kargo taşıma taleplerini, uçuş kapasitesini ve operasyonel kısıtları kullanarak hangi taleplerin kabul, hangilerinin reddedilmesi gerektiğine karar veren uçtan uca bir karar destek sistemi.

## Problem Tanımı

Bir havayolunun kargo operasyonunda, her uçuşun sınırlı bir ağırlık ve hacim kapasitesi vardır. Gelen kargo talepleri bu kapasiteyi aşabilir. Amaç, kapasite kısıtları içinde kalarak toplam geliri maksimize eden kabul/red kombinasyonunu bulmaktır. Bu klasik bir **matematiksel optimizasyon** (0-1 Integer Programming / Multiple Knapsack Problem) problemidir.

## Mimari

```
İstek (Streamlit UI)
        │
        ▼
   FastAPI Backend  ──────►  SQLite Veritabanı
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

Katmanlar birbirinden bağımsız: veritabanı SQLAlchemy ORM ile soyutlanmış (PostgreSQL'e geçiş tek satır), optimizasyon motoru saf Python/PuLP (herhangi bir framework'e bağımlı değil), API bu ikisini dışarıya REST olarak açıyor, arayüz sadece API'yi tüketiyor.

## Veritabanı Şeması

5 çekirdek tablo: `airports`, `aircraft_types` (referans tabloları), `routes`, `flights`, `cargo_requests`. Optimizasyon sonuçları `optimization_results` tablosuna yazılır. Detaylı şema için bkz. proje kökündeki `docs/database_schema.md`.

## Optimizasyon Modeli

Karar değişkeni: `x_i ∈ {0,1}` (talep i kabul/red). Amaç fonksiyonu: `maximize Σ revenue_i * x_i`. Kısıtlar: her uçuş için kabul edilen taleplerin toplam ağırlığı ve hacmi, o uçağın kapasitesini aşamaz. CBC solver (açık kaynak) ile çözülüyor.

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
