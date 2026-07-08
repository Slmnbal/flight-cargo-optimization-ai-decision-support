# Profesyonel Yazılım Geliştirme Rehberi

Bu doküman, Flight Cargo Optimization & AI Decision Support System projesini "çalışan bir script" değil, "profesyonel bir yazılım ürünü" olarak geliştirmen için pratik bir referans. Kod yazmaya başlamadan önce, her fazda bu prensipleri nasıl uygulayacağını burada bulacaksın.

Amaç ezber değil alışkanlık: buradaki disiplinleri Faz 1'den itibaren uygularsan, Faz 7'ye geldiğinde zaten "production-ready" bir proje olur, sona bırakılan bir temizlik işi olmaz.

## 1. Zihniyet Değişimi: Script Yazan Biri vs Ürün Geliştiren Biri

Bir data analyst genelde tek seferlik notebook/script üretir: çalışır, sonucu alır, biter. Bir yazılım mühendisi ise şunu sorar: "Bu kodu 6 ay sonra ben ya da başka biri anlayabilir mi, değiştirebilir mi, bozmadan genişletebilir mi?"

Pratik sonucu: her satır kod yazarken kendine şunu sor — "Bu fonksiyonu test edebilir miyim?", "Bu değişkeni başka biri anlar mı?", "Bu hata olursa ne olur?". Bu üç soru, aşağıdaki tüm pratiklerin kökeni.

## 2. Git ve GitHub Disiplini

Bir projeyi profesyonel yapan ilk şey kod kalitesi değil, geçmişinin okunabilir olmasıdır. Bir işe alım yöneticisi senin commit geçmişine bakarak nasıl çalıştığını anlar.

**Branch stratejisi:**
`main` dalı her zaman çalışır durumda kalmalı. Her yeni özellik için ayrı branch aç: `feature/data-layer-schema`, `feature/optimization-engine`, `fix/capacity-constraint-bug`. İş bitince pull request (PR) ile main'e birleştir — tek başına çalışsan bile, kendi PR'ını kendine review et.

**Commit mesajları (Conventional Commits):**
Rastgele "update", "fix", "asdf" gibi mesajlar yerine yapılandırılmış format kullan:
```
feat(data): add SQLAlchemy models for cargo_requests and flights
fix(optimization): correct capacity constraint sign error
docs(readme): add architecture diagram
test(api): add unit tests for /optimize endpoint
refactor(agent): extract tool-calling logic into separate module
```
Prefixler: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `perf`. Bu hem geçmişini okunabilir kılar hem de ileride otomatik changelog/versiyonlama için altyapı olur.

**Küçük, sık commit at.** Bir haftalık işi tek commit'te göndermek yerine, her mantıklı adımı ayrı commit yap. "Faz 1 bitti" değil, "routes tablosu eklendi", "seed data yazıldı", "validation testleri eklendi" gibi adımlarla ilerle.

**Issue ve proje takibi:** GitHub Issues'ı basit bir yapılacaklar listesi gibi kullan. Her faz için bir milestone, her görev için bir issue aç. Bu, "nasıl planlama yaptığını" gösteren somut bir kanıt olur — mülakatlarda "issue tracker'ımda şöyle takip ettim" demek güçlü bir cümle.

## 3. Proje Yapısı ve Modülerlik

Sende zaten hedef klasör yapısı var — buna sadık kal, ama önemli olan neden böyle yapıldığını anlamak:

- `backend/app/api/` yalnızca HTTP katmanı (request/response) içerir, iş mantığı içermez.
- `backend/app/services/` gerçek iş mantığını barındırır (optimizasyonu çağırma, sonucu işleme).
- `backend/app/models/` veritabanı tablolarını (SQLAlchemy ORM) temsil eder.
- `backend/app/schemas/` Pydantic ile API'nin dış dünyaya gösterdiği veri şeklini tanımlar (ORM modeliyle karıştırma).
- `backend/app/optimization/`, `ml/`, `agents/` birbirinden bağımsız, tek başına test edilebilir modüllerdir.

Kural: bir dosya iki farklı sorumluluk taşımamalı (single responsibility). `main.py` içine her şeyi yazmak "prototip" seviyesidir; modüllere ayırmak "ürün" seviyesidir.

**Notebook'tan production'a geçiş kuralı:** `notebooks/` klasöründe keşif yap, model dene, veri incele. Ama bir mantık işe yarar hale geldiğinde onu mutlaka `backend/app/` içine, test edilebilir bir fonksiyon/sınıf olarak taşı. Notebook'ta kalan kod hiçbir zaman "bitmiş" sayılmaz.

## 4. Kod Standartları

- **Type hints kullan:** `def optimize(requests: list[CargoRequest]) -> OptimizationResult:` gibi. Bu hem okunabilirliği artırır hem IDE'nin hata yakalamasını sağlar.
- **Formatter ve linter:** `black` (otomatik formatlama) ve `ruff` (linting) kur. Kod stilini tartışmaya açmadan otomatikleştir.
- **Pre-commit hooks:** `pre-commit` paketiyle her commit öncesi otomatik format/lint kontrolü çalıştır. Bu, "profesyonel takım disiplini" gösteren küçük ama etkili bir detay.
- **Docstring:** Her public fonksiyon/sınıf için ne yaptığını, parametrelerini ve döndürdüğünü kısaca yaz.
- **Anlamlı isimlendirme:** `df2`, `temp`, `x` gibi isimler yerine `cargo_requests_df`, `capacity_utilization` gibi isimler kullan.

## 5. Test Stratejisi

Test yazmayan bir "karar destek sistemi" güvenilir değildir — özellikle optimizasyon ve finansal sonuç üreten bir sistemde test şart.

**Test piramidi:**
- **Unit test:** Tek bir fonksiyonu izole test eder (örn. "kapasite kısıtı doğru mu kuruluyor?"). Çoğunluk burada olmalı.
- **Integration test:** API endpoint'inin database ile birlikte doğru çalıştığını test eder (örn. `POST /optimize` gerçekten sonucu kaydediyor mu?).
- **Regression test:** Optimizasyon modelinde küçük bir bilinen senaryo tanımla, beklenen sonucu sabitle; kodu değiştirdikçe bu senaryonun hâlâ doğru sonucu verdiğini kontrol et. Solver kodunda bu kritik, çünkü bir kısıt değişikliği sessizce yanlış sonuç üretebilir.

`pytest` kullan, testleri `backend/tests/` altında, kaynak koddaki modül yapısını yansıtacak şekilde organize et (`tests/test_optimization.py`, `tests/test_api.py`). Her yeni özellik eklerken en az bir test ekle — "sonra yazarım" dediğin test genelde hiç yazılmaz.

## 6. Bağımlılık ve Ortam Yönetimi

- Sanal ortam kullan (`venv` veya `poetry`), asla global Python'a paket kurma.
- `requirements.txt` (veya `pyproject.toml`) sürüm numaralarıyla sabitlenmiş olmalı — "benim makinemde çalışıyordu" sorununu önler.
- Gizli bilgiler (API key, database şifresi) asla koda yazılmaz. `.env` dosyasında tut, `.env.example` ile hangi değişkenlerin gerektiğini dokümante et, `.env`'i `.gitignore`'a ekle.
- Farklı ortamlar (local, test, production) için ayrı config yönetimi düşün (Pydantic `Settings` sınıfı iyi bir başlangıç).

## 7. Logging ve Hata Yönetimi

`print()` debugging bir prototip alışkanlığıdır. Bunun yerine Python'ın `logging` modülünü kullan: hangi seviyede (`INFO`, `WARNING`, `ERROR`) ne zaman ne olduğunu kaydet. Özellikle optimizasyon motorunda solver'ın "infeasible" (çözümsüz) döndüğü durumları sessizce geçme — logla ve API'de anlamlı bir hata mesajı döndür.

FastAPI'de hata yönetimini merkezi yap: her endpoint'te tekrar tekrar try/except yazmak yerine global exception handler kullan.

## 8. Dokümantasyon

README, bir projenin "kapak sayfası"dır — işe alım yöneticisi kodunu okumadan önce README'ni okur. İçermesi gerekenler zaten senin planında var (amaç, mimari, kurulum, ekran görüntüleri). Ek olarak:

- **Architecture Decision Record (ADR):** Önemli teknik kararları (`neden PuLP değil OR-Tools seçtim` gibi) kısa notlar halinde `docs/` altına yaz. Bu, "sadece kod yazmadım, düşünerek karar verdim" kanıtı olur.
- **API dokümantasyonu:** FastAPI otomatik Swagger/OpenAPI dokümantasyonu üretir (`/docs` endpoint'i) — bunu README'de göster.

## 9. CI/CD Temelleri

GitHub Actions ile her push/PR'da otomatik çalışan basit bir pipeline kur: testleri çalıştır, linter'ı çalıştır. Bu, "kodun her zaman çalışır durumda kalmasını" garanti eder ve mülakatlarda somut bir yetkinlik olarak gösterilir. Başlangıçta karmaşık deployment gerekmez — sadece `pytest` ve `ruff check` otomasyonu yeterli bir başlangıçtır.

## 10. Konteynerleştirme (Docker)

Docker, "bende çalışıyordu" sorununu tamamen ortadan kaldırır. Her servis (backend, database, opsiyonel frontend) için ayrı bir `Dockerfile`, hepsini birlikte ayağa kaldırmak için `docker-compose.yml`. Hedef: biri repo'yu klonlayıp `docker compose up` dediğinde sistem çalışsın. Bunu en baştan düşünüp erken kurmak, sona bırakıp "Docker'a taşıma" işkencesi çekmekten çok daha kolay.

## 11. İteratif Geliştirme Disiplini

Kendi prensiplerinde de yazdığın gibi: önce basit çalışan versiyon, sonra modülerleştirme. Somut kural: her faz için önce "en basit çalışan hali"ni bir branch'te tamamla, commit'le, sonra "profesyonelleştirme" adımlarını (test, logging, refactor) ayrı commit'lerle ekle. Bu, hem ilerlemeni somut gösterir hem de "mükemmeliyetçilik felci"ni önler.

## Bu Prensiplerin Fazlara Uygulanışı

| Faz | Bu rehberden öncelikli uygulanacaklar |
|---|---|
| Faz 1 – Data Layer | Git branch/commit disiplini, klasör yapısı, type hints, ilk pytest testleri (veri validasyonu) |
| Faz 2 – Optimization Engine | Regression testleri (sabit senaryo), ADR (solver seçim gerekçesi), docstring |
| Faz 3 – Backend API | Pydantic schema/model ayrımı, merkezi hata yönetimi, logging, integration testler |
| Faz 4 – UI Layer | Kullanıcı odaklı KPI tasarımı, README'ye ekran görüntüsü |
| Faz 5 – ML Layer | MLflow ile deney takibi (bu da bir çeşit "versiyon kontrolü"), model test/evaluation |
| Faz 6 – AI Agent | Guardrail testleri, tool-calling'in izole test edilmesi, agent davranış sınırlarının dokümantasyonu |
| Faz 7 – Production | Docker, CI/CD, tam README, ADR'lerin toparlanması |

## Sıradaki Adım

Bu rehberi uyguladığın somut ilk alışkanlıklar: repo'yu `git init` ile başlat, `.gitignore` ekle, `main` branch'i koru, ilk commit'i klasör iskeletiyle at. Hazır olduğunda Faz 1'e (Data Layer) geçebiliriz.
