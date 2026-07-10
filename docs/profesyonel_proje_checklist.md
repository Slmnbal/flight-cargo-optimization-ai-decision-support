# Profesyonel Bir Proje İçin Checklist

Bu doküman, "bir proje ne zaman profesyonel sayılır" sorusuna somut bir cevap veriyor. Her madde için: ne demek, neden önemli, ve senin bu projede şu an nerede olduğun (✅ yapıldı / ⚠️ kısmen / ❌ henüz yok). Amaç, teoriyi havada bırakmamak — her madde, kendi projende gördüğün gerçek bir şeye bağlanıyor.

Bunu bir sınav listesi gibi değil, bir **pusula** gibi kullan: yeni bir proje başladığında ya da mevcut projeni değerlendirirken buraya bak.

## 1. Kod Kalitesi

**Ne demek:** Kodun sadece çalışması yetmez, okunabilir ve bakımı yapılabilir olmalı.

- Anlamlı isimlendirme (`weight_kg`, `revenue` — `x`, `temp` değil) ✅
- Type hint kullanımı (`def run_optimization(db: Session) -> dict:`) ✅
- Her fonksiyonun tek bir işi yapması (single responsibility) ✅ — örn. `optimizer.py` sadece optimizasyon yapıyor, veritabanı bağlantısı ayrı dosyada
- Otomatik format/lint araçları (black, ruff) ❌ — henüz eklemedik, kolay bir sonraki adım
- Kod tekrarını önleme (DRY - Don't Repeat Yourself) ✅ — örn. tüm modelleri `models/__init__.py`'de tek yerden import etmemiz

## 2. Mimari (Architecture)

**Ne demek:** Sistemin parçalarının birbirinden bağımsız, net sınırlarla ayrılmış olması.

- Katmanlı mimari (data / business logic / API / UI ayrı) ✅ — `models/`, `optimization/`, `api/`, `frontend/`
- Veritabanı modeli ile API'nin dış görünümünün ayrılması ✅ — `models/` (SQLAlchemy) vs `schemas/` (Pydantic)
- Bağımlılıkların tek yönlü akması (UI → API → iş mantığı → veri, tersi değil) ✅
- Konfigürasyon ile kodun ayrılması (`.env`, sabit değerler kod içine gömülmemeli) ✅

## 3. Veri Yönetimi

**Ne demek:** Verinin nasıl saklandığı, değiştiği ve korunduğu planlı olmalı.

- Şema tasarımı öncesi düşünülmüş, dokümante edilmiş ✅ — `docs/database_schema.md`
- Migration (şema değişikliklerini takip eden) aracı — Alembic gibi ❌ — şu an şema değişince elle güncelliyoruz, ileri aşamada gerekir
- Yedekleme stratejisi ❌ — production'a geçerken gerekir, MVP'de yok
- Referans bütünlüğü (foreign key) ✅

## 4. Test

**Ne demek:** Kodun doğru çalıştığını, insan hatası veya varsayıma değil, otomatik kontrole dayandırmak.

- Unit test (izole fonksiyon testleri) ✅ — `test_optimizer.py`
- Doğruluk testi (sadece "çalışıyor" değil, "doğru sonucu veriyor" kontrolü) ✅ — kapasite/gelir hesaplamasını doğrulayan testimiz
- Integration test (API + veritabanı birlikte) ❌ — henüz yok, iyi bir sonraki adım
- Test coverage ölçümü ❌ — "kodun yüzde kaçı testli" ölçümü henüz yok
- CI'da otomatik test çalıştırma ✅ — GitHub Actions

## 5. Güvenlik

**Ne demek:** Hassas bilgilerin korunması, kötüye kullanımın engellenmesi.

- Secrets (API key, şifre) kodda değil `.env`'de, `.gitignore`'da ✅
- Girdi doğrulama (kullanıcıdan gelen veri kontrol ediliyor mu) ✅ — Pydantic şemaları bunu otomatik yapıyor
- Bağımlılık güvenlik taraması (kullandığın kütüphanelerde bilinen açık var mı) ❌ — `pip-audit` gibi bir araç eklenebilir
- Kimlik doğrulama/yetkilendirme (API'ye kim erişebilir) ❌ — şu an API tamamen açık, gerçek kullanımda bir auth katmanı gerekir

## 6. Hata Yönetimi ve Gözlemlenebilirlik (Observability)

**Ne demek:** Bir şey ters gittiğinde bunu görebilmek ve anlayabilmek.

- Yapılandırılmış loglama (`print()` değil, `logging`) ✅
- API'de merkezi hata yönetimi (try/except + anlamlı HTTP hataları) ✅
- Hata izleme servisi (Sentry gibi) ❌ — production'da gerçek kullanıcı hatalarını yakalamak için
- Metrik/monitoring (sistem ne kadar yavaş, kaç istek geliyor) ❌ — MVP sonrası konu

## 7. Dokümantasyon

**Ne demek:** Başka biri (ya da 6 ay sonraki sen) projeyi anlayabilmeli.

- README (amaç, kurulum, çalıştırma) ✅
- Mimari açıklaması ✅ — `docs/project_overview.md`, `docs/proje_yolculugu.md`
- API dokümantasyonu ✅ — FastAPI'nin otomatik `/docs` sayfası
- Kod içi docstring'ler ✅
- Karar gerekçeleri (ADR - neden bu teknolojiyi seçtin) ⚠️ — kısmen var (yorumlarda), ayrı bir `docs/adr/` klasörü henüz yok

## 8. CI/CD ve Dağıtım (Deployment)

**Ne demek:** Kodun test edilip, güvenilir şekilde çalışan bir ortama ulaşması.

- Otomatik test pipeline'ı (her push'ta) ✅ — GitHub Actions
- Konteynerleştirme (Docker) ✅
- Ortam ayrımı (development / staging / production) ❌ — şu an tek ortam var
- Otomatik dağıtım (deploy) ❌ — proje şu an sadece yerelde/Docker'da çalışıyor, gerçek bir sunucuya otomatik dağıtım yok
- Sürüm etiketleme (semantic versioning, `v1.0.0` gibi git tag'leri) ❌

## 9. Performans ve Ölçeklenebilirlik

**Ne demek:** Sistemin veri/kullanıcı arttıkça makul hızda çalışmaya devam etmesi.

- N+1 query gibi bilinen performans hatalarından kaçınma ✅ — optimizer'da bunu bizzat düzelttik
- Önbellekleme (caching) ❌ — MVP ölçeğinde gerekmiyor
- Yük testi (load testing) ❌ — gerçek kullanıcı ölçeğine geçerken gerekir

## 10. İşbirliği ve Süreç

**Ne demek:** Bir ekiple (ya da gelecekteki kendinle) düzenli çalışabilmek.

- Anlamlı commit mesajları (Conventional Commits) ✅
- Küçük, sık commit'ler ✅
- Branch stratejisi (özellik başına ayrı branch, PR ile birleştirme) ⚠️ — şu an doğrudan `main`'e çalışıyoruz, tek kişilik projede kabul edilebilir ama takımda olmaz
- Issue/proje takibi (GitHub Issues, Projects) ❌ — henüz kullanmadık

## Özet: Şu An Neredesin?

Bu projede **kod kalitesi, mimari, temel test, temel dokümantasyon, CI ve konteynerleştirme** tarafında gerçekten sağlam bir yer var — bu, çoğu "portföy projesi"nin bile atladığı seviyeler. Eksik kalanlar (migration, auth, hata izleme, ortam ayrımı, branch stratejisi) genelde **gerçek kullanıcısı olan, birden fazla kişinin çalıştığı** projelerde devreye giriyor — yani "bu projeyi tek başıma portföy için yapıyorum" aşamasında bunların hepsini tamamlamamış olman normal ve beklenen.

Mülakatta değerli olan şey, bu listeyi ezbere bilmen değil, **"şunu bilerek yapmadım, çünkü bu aşamada gerekli değildi, ama gerçek bir production sistemde şöyle eklerdim" diyebilmen.** Bu, "sadece kod yazan biri" ile "sistemi bütünsel düşünen biri" arasındaki farkı gösterir.
