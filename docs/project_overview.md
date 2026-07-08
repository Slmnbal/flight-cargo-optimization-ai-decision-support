# Flight Cargo Optimization & AI Decision Support System — Proje Özeti

## Ne Yapıyoruz

Havayolu/kargo operasyonlarında gelen kargo taşıma taleplerini, uçuş kapasitesini, rota bilgilerini ve operasyonel kısıtları kullanarak hangi kargo taleplerinin kabul, hangilerinin reddedilmesi gerektiğine karar veren uçtan uca bir karar destek sistemi geliştiriyoruz.

Bu bir dashboard projesi değil. Veritabanı katmanı, matematiksel optimizasyon motoru, ML tabanlı talep/risk tahmini, FastAPI backend, kullanıcı arayüzü ve sonuçları doğal dille açıklayan bir AI Agent'tan oluşan, Docker ile paketlenmiş, testli ve dokümante edilmiş profesyonel bir yazılım ürünü.

**GitHub repo adı:** `flight-cargo-optimization-ai-decision-support`

## Neden Bu Proje (Kariyer Amacı)

Amaç, klasik Data Analyst profilinden çıkıp AI Engineer + Optimization Engineer + Software Product Developer hibrit profiline geçiş yapmak. Proje şu anlatıyı somutlaştırmalı:

"Veri analitiği geçmişimi kullanarak havayolu/kargo operasyonlarında talep, kapasite ve rota verilerini analiz eden; matematiksel optimizasyon modeliyle kabul/red kararları üreten; ML ile tahmin/risk katmanı ekleyen; FastAPI, PostgreSQL ve UI ile çalışan bir karar destek yazılımına dönüştüren; AI Agent ile sonuçları açıklanabilir hale getiren uçtan uca bir sistem geliştirdim."

Bu proje aynı anda beş yetkinlik alanını kanıtlıyor: AI Engineer (LLM/agent/RAG/tool calling), Optimization Engineer (LP/MIP/solver), Data Scientist (forecasting/risk modeling), Software Engineer (temiz mimari, test, Docker) ve Data Analyst avantajı (SQL, KPI tasarımı, iş problemini teknik probleme çevirme).

## Karar Modelinin Özü

Karar değişkeni: `x_i = 1` ise kargo talebi kabul edilir, `x_i = 0` ise reddedilir.

Amaç fonksiyonu: `maximize Σ revenue_i * x_i` — toplam geliri maksimize et.

Kısıtlar: uçuş kapasitesi aşılmamalı, talep doğru rota/uçuşla eşleşmeli, tarih uygunluğu sağlanmalı, öncelikli talepler dikkate alınmalı, senaryo bazlı kurallar ve operasyonel kapasite sınırları korunmalı.

## Fazlar

### Faz 0 — Temeller (yazılım geçmişi olmayanlar için)
Terminal kullanımı (`pwd`, `ls`, `cd`, `mkdir`, `touch`), Python temel syntax (değişken, fonksiyon, döngü, koşul, liste/dict, class) ve git/GitHub temelleri (`init`, `add`, `commit`, `branch`, `push`). Bu faz, sonraki fazlarda kullanılacak araçları öğrenmeyi amaçlar; proje koduna dahil değildir.

### Faz 1 — Data Layer
**Amaç:** Projenin veritabanı yapısını kurmak.

Tablolar: `routes`, `flights`, `cargo_requests`, `aircraft_capacity`, `scenarios`, `optimization_results`, `accepted_requests`, `rejected_requests`, `kpi_results`.

Yapılacaklar: database şeması tasarlanacak, örnek veri üretilecek, SQLAlchemy modelleri yazılacak, seed data oluşturulacak, temel veri kalite kontrolleri yapılacak.

Gösterdiği yetkinlik: SQL, database design, data modeling, data validation, aviation/cargo veri okuryazarlığı.

### Faz 2 — Optimization Engine
**Amaç:** Kargo talebi kabul/red kararlarını optimize eden matematiksel modeli kurmak.

Araçlar: PuLP + CBC Solver (başlangıç), Google OR-Tools (orta seviye), Pyomo/Gurobi/CPLEX (ileri seviye).

Konular: Linear Programming, Integer Programming, Mixed Integer Programming, Capacity Optimization, Assignment Problem, Scenario Optimization, Constraint Modeling, Objective Function Design, Infeasibility Handling.

Gösterdiği yetkinlik: Operations Research, matematiksel modelleme, solver kullanımı, kısıt/amaç fonksiyonu tasarımı.

### Faz 3 — Backend API
**Amaç:** Optimizasyon motorunu ve veri katmanını API üzerinden çalışır hale getirmek.

Araçlar: FastAPI, SQLAlchemy, Pydantic, PostgreSQL, logging, pytest.

Örnek endpointler: `GET /routes`, `GET /flights`, `GET /cargo-requests`, `POST /scenarios`, `POST /optimize`, `GET /results/{scenario_id}`, `GET /kpis/{scenario_id}`, `POST /explain/{scenario_id}`.

Yapılacaklar: FastAPI uygulaması kurulacak, database bağlantısı yapılacak, senaryo/optimizasyon endpointleri yazılacak, sonuçlar database'e kaydedilecek, hata yönetimi ve logging eklenecek.

Gösterdiği yetkinlik: Backend engineering, REST API, model/solver serving, database entegrasyonu, production-oriented kodlama.

### Faz 4 — UI Layer
**Amaç:** Kullanıcının sistemi kolayca kullanabileceği bir arayüz geliştirmek.

Araçlar: Streamlit + Plotly (başlangıç), React + TypeScript + Tailwind (ileri aşama).

Ekranlar: genel dashboard, rota/uçuş/kargo tabloları, senaryo oluşturma, optimizasyon çalıştırma, accepted/rejected requests tabloları, kapasite kullanım grafiği, gelir/kayıp gelir analizi, senaryo karşılaştırma, AI Explanation Panel.

KPI kartları: toplam gelir, accepted/rejected sayısı, capacity utilization, unused capacity, lost revenue, objective value, solver status, runtime.

Gösterdiği yetkinlik: dashboard tasarımı, product thinking, operasyonel KPI tasarımı, veri görselleştirme.

### Faz 5 — ML Layer
**Amaç:** Optimizasyon sistemine tahmin ve risk katmanı eklemek.

Modeller: rota bazlı demand forecasting, capacity risk prediction, delay/risk scoring, revenue prediction, request priority scoring.

Araçlar: pandas, scikit-learn, XGBoost, LightGBM, MLflow, SHAP.

Akış: geçmiş veriler alınır → feature'lar üretilir (rota, tarih, sezon, kapasite, geçmiş talep) → model eğitilir → performans ölçülür → MLflow ile deney kaydedilir → tahmin, optimizasyon modeline girdi olarak verilir.

Gösterdiği yetkinlik: Data Science, forecasting, feature engineering, ML-to-optimization entegrasyonu.

### Faz 6 — AI Agent Layer
**Amaç:** Optimizasyon sonuçlarını doğal dille açıklayan ve kullanıcı sorularına cevap veren bir AI Agent geliştirmek.

Araçlar: OpenAI/Azure OpenAI API, LangChain/LangGraph, RAG, Vector Database (Chroma/FAISS/pgVector), tool calling, structured outputs, guardrails.

Agent tool'ları: `get_scenario_results`, `get_accepted_requests`, `get_rejected_requests`, `calculate_capacity_utilization`, `compare_scenarios`, `explain_optimization_result`.

Agent kuralları: veri uydurmaz, solver sonucunu değiştirmez, kritik kararlarda insan onayı gerektiğini belirtir, sadece tool çıktısına dayanarak cevap verir, belirsizliği açıkça ifade eder.

Gösterdiği yetkinlik: LLM application development, RAG, tool calling, agent tasarımı, explainable decision support.

### Faz 7 — Production Layer
**Amaç:** Projeyi profesyonel portföy projesi haline getirmek.

Eklenecekler: Docker, Docker Compose, pytest, logging, README, mimari diyagram, API dokümantasyonu, GitHub Actions (temel CI/CD), environment variables/.env yönetimi, monitoring temelleri.

Beklenen çıktı: `docker compose up` komutuyla projeyi çalıştırabilecek biri, README'de proje amacını, mimariyi, database şemasını, optimizasyon modelini, API'yi, ekran görüntülerini ve AI Agent açıklamasını bulabilmeli.

Gösterdiği yetkinlik: MLOps, production readiness, deployment farkındalığı, sürdürülebilir proje yapısı.

## İlkeler (özet)

Önce basit çalışan versiyon, sonra modülerleştirme. Notebook'ta kalan model mutlaka API'ye taşınmalı. Optimizasyon sonucu database'e yazılmalı. AI Agent karar üretmez, solver sonucunu açıklar. Her faz GitHub'da commit'lerle ilerlemeli. Detaylı geliştirme prensipleri için bkz. `docs/dev_principles_guide.md`.

## Tavsiyelerim

**Önce ince bir dikey dilim kur, sonra derinleştir.** Yedi fazı sırayla tam bitirip bir sonrakine geçmek yerine, önce çok basit bir uçtan uca versiyon hedefle: 3-4 sahte kargo talebi, 2 uçuş, tek kısıtlı bir LP modeli, tek bir `/optimize` endpoint'i, ekrana sonucu yazdıran bir Streamlit sayfası. Bu "iskelet" bir hafta içinde çalışır hale gelirse hem motivasyonun artar hem de mimarinin tamamını erken görmüş olursun. Her fazı sonra tekrar tekrar genişletirsin (daha fazla kısıt, daha fazla tablo, ML, agent). Sırf birinci fazı "mükemmel" yapmaya çalışıp aylarca sadece database ile uğraşmak motivasyon kırar.

**Gerçekçi zaman beklentisi kur.** Yazılımda gerçekten sıfırsan, bu proje haftalar değil aylar sürer — ve bu normal. Haftada 5-6 saat ayırabiliyorsan bile ilerleme kaydedeceksin; önemli olan düzenli küçük adımlar, hepsini bir çırpıda bitirme çabası değil.

**Üretilen kodu kopyalama, anla.** Ben veya Claude Code sana bir kod bloğu verdiğinde, özellikle Faz 0-2 arasında, o kodu bizzat kendi elinle yaz (kopyala-yapıştır değil) ve her satır için "bu ne işe yarıyor" sorusunu kendine sor. İlerleyen fazlarda (Agent, ML) daha rahat "üretilen kodu kullan, mantığını anla" moduna geçebilirsin — ama en başta parmaklarında syntax'ın oturması lazım.

**Ücretsiz/açık araçlarla kal.** Gurobi, CPLEX, React gibi "ileri seviye" seçenekleri şimdilik unut. Portföy versiyonun PuLP + CBC + Streamlit + SQLite/PostgreSQL ile tamamen tamamlanabilir; bu araçlar README'de "gelecek adımlar" olarak bahsedilebilir. Amaç en pahalı aracı kullanmak değil, doğru mühendislik kararını verebildiğini göstermek.

**Karar defteri tut.** Her faz sonunda 3-4 cümlelik bir not al: ne yaptın, neden o yolu seçtin, nerede takıldın. Bu notlar hem `docs/` altındaki ADR'lerin taslağı olur hem de altı ay sonra mülakatta "bu projede şu kararı şu yüzden verdim" diyebilmen için tükenmez bir kaynak olur.

**İki şeyi aynı anda öğrenmeye çalışma.** Yeni bir kavramla (örn. SQLAlchemy) karşılaştığında önce onu küçük, izole bir örnekte dene, sonra projeye entegre et. Hem yeni kavramı hem projenin karmaşıklığını aynı anda çözmeye çalışmak öğrenmeyi yavaşlatır.

**Terminal + Cowork kombinasyonunu esnek kullan.** Günlük kodlama işini (dosya yazma, hata ayıklama) VS Code terminalinde Claude Code ile yap; ben burada daha çok plan, karar verme, dokümantasyon ve "büyük resmi görme" tarafında destek olayım. İkisi aynı klasörü paylaştığı için geçiş sorunsuz.

## Klasör Yapısı (hedef)

```
flight-cargo-optimization-ai-decision-support/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── database/
│   │   ├── optimization/
│   │   ├── ml/
│   │   ├── agents/
│   │   └── utils/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── streamlit_app.py
│   └── pages/
├── data/
│   ├── raw/
│   ├── processed/
│   └── sample/
├── notebooks/
├── docs/
├── docker-compose.yml
├── README.md
├── .env.example
└── .gitignore
```
