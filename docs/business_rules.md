# İş Kuralları — Kargo Kabul/Red Kararlarının Arkasındaki Mantık

Bu doküman, sistemin veri modelinde ve optimizasyon motorunda kodlanmış olan iş
kurallarını düz yazıyla açıklıyor. AI Agent, "neden embargo var", "priority_class
nasıl işliyor" gibi kavramsal sorularda bu dokümanı (RAG üzerinden) referans alıyor —
canlı veritabanı sorguları (`get_accepted_requests` gibi tool'lar) SAYISAL/GÜNCEL
verileri döndürürken, bu doküman KAVRAMSAL/GEREKÇESEL soruları cevaplamak için var.

## Kargo Tipleri (cargo_type)

Sistemde altı kargo tipi tanımlı: `general` (genel kargo), `perishable` (bozulabilir,
örn. çiçek/gıda), `dangerous_goods` (tehlikeli madde, örn. lityum pil/kimyasal),
`live_animal` (canlı hayvan), `valuable` (değerli eşya, örn. mücevher), `oversized`
(standart dışı boyut/ağırlık). Her tip, optimizasyon motorunda farklı kısıtlara tabi
olabilir (soğuk zincir, embargo, tehlikeli madde izni) ve gelir modelinde farklı bir
birim fiyat çarpanına sahiptir — örn. `live_animal` ve `valuable`, taşıma
karmaşıklığı/riski nedeniyle `general`den daha yüksek $/kg getirir.

## Öncelik Sınıfı (priority_class): Contract vs Spot

Kargo talepleri iki öncelik sınıfından birine ait: `contract` (sözleşmeli, düzenli
müşteri — genelde hacim karşılığında indirimli, önceden anlaşılmış bir fiyata sahiptir)
ve `spot` (anlık, sözleşmesiz talep — o anki piyasa fiyatına tabidir, fiyatı daha
değişkendir).

Optimizasyon motoru, her uçuşta kapasitenin belirli bir yüzdesini (`RESERVE_PCT`,
şu an %30) SADECE contract kargoya ayırıyor — spot talepler bu yüzdelik dilime
giremiyor, sadece kalan kapasiteyi kullanabiliyor. Bu, "reserved capacity" (korumalı
kapasite) yaklaşımı olarak biliniyor ve gerçek havayolu revenue management
pratiğinde yaygın bir tekniktir (EMSR/allotment protection). Neden böyle: contract
müşteriler düzenli, uzun vadeli gelir kaynağıdır — o anki en yüksek gelirli spot
talebe her zaman öncelik verilseydi, contract müşteriler kapasite bulamayabilir ve
sözleşmeyi başka bir taşıyıcıya kaydırabilirdi. Bilinçli olarak "contract'a alt sınır
koy" yerine "spot'u üstten sınırla" yaklaşımı seçildi, çünkü contract talebi az olduğu
bir uçuşta alt sınır modeli çözümsüz (infeasible) hale gelebilirdi; spot'u üstten
sınırlamak model her zaman çözülebilir tutuyor (bkz. `docs/adr/0001-cargo-optimization-constraints.md`).

## Soğuk Zincir (Temperature Controlled Cargo)

Bazı kargo talepleri (`requires_temperature_control=True`, tipik olarak `perishable`
tipi kargo) sıcaklık kontrollü bir bölmede taşınmalıdır. Her uçak tipinin
(`AircraftType.temperature_controlled_capacity_kg`) ayrı, genelde toplam kapasitesinden
çok daha küçük bir soğuk zincir kapasitesi vardır. Optimizasyon motoru bu talepleri
ayrıca kısıtlar: bir uçuştaki tüm soğuk-zincir taleplerinin toplam ağırlığı, o uçağın
soğuk zincir kapasitesini aşamaz — bu, genel ağırlık kapasitesinden tamamen bağımsız
işleyen ayrı bir kısıttır.

## Embargo

Bazı rotalarda (`Route.embargo_active=True`) geçici bir kargo kısıtlaması uygulanır.
Kapsamı `Route.embargoed_cargo_types` alanıyla belirlenir: bu alan boşsa embargo o
rotadaki TÜM kargo tiplerini kapsar (rota tamamen kapalı); doluysa (virgülle ayrılmış
bir liste, örn. `"live_animal"`) sadece listelenen tipler o rotada taşınamaz. Örnek
senaryo: IST-JNB rotasında, bölgesel bir hayvan hastalığı salgını nedeniyle sadece
canlı hayvan kargosu geçici olarak durduruldu — genel kargo, tehlikeli madde vb. bu
rotada normal şekilde taşınmaya devam ediyor. Embargolu talepler, optimizasyon
modeline hiç girmeden (bir "ön-filtre" ile) doğrudan reddediliyor; bunun nedeni
`docs/adr/0001-cargo-optimization-constraints.md`'de tartışılıyor.

## Tehlikeli Madde ve Kısıtlı Kargo Taşıma İzinleri

Bir `dangerous_goods` talebinin bir uçuşta taşınabilmesi için İKİ koşul birden
sağlanmalı: (1) o uçuşun rotası tehlikeli madde taşımaya izin vermeli
(`Route.restricted_cargo_allowed=True`) VE (2) o uçuşu yapan uçak tipi tehlikeli
madde sertifikasına sahip olmalı (`AircraftType.dangerous_goods_allowed=True`).
İkisinden biri bile sağlanmıyorsa talep reddedilir. Örnek senaryo: IST-NRT (Tokyo)
rotasında, varış ülkesinin (Japonya) tehlikeli madde ithalatına yönelik sıkı gümrük
kuralları nedeniyle bu rotada dangerous_goods kargo hiçbir zaman kabul edilmiyor
(`Route.restricted_cargo_allowed=False`) — kullanılan uçak tipi tehlikeli madde
taşıyabilse bile.

## Gelir Modeli

Bir kargo talebinin geliri, sadece ağırlığa değil; rotanın bölgesine (uzun menzilli
rotalar $/kg olarak daha pahalıdır), kargo tipine (örn. `live_animal` ve `valuable`
daha yüksek birim fiyata sahiptir) ve öncelik sınıfına (contract, hacim karşılığında
indirimli bir birim fiyata sahiptir; spot piyasa fiyatını yansıtır) bağlıdır. Bu,
gerçek IATA kargo tarifelerinin çok basitleştirilmiş bir yansımasıdır — kesin bir
tarife tablosu değildir, ama "gelir rotaya ve kargo tipine göre anlamlı şekilde
değişmeli" ilkesini kodluyor.

## Optimizasyon Kararının Anlamı: accepted / rejected / reason

Her optimizasyon çalıştırıldığında, her kargo talebi için bir kabul/red kararı
üretilir ve `optimization_results` tablosuna yazılır. `decision="rejected"` olan
kayıtlarda bir `reason` alanı bulunur: `"embargo"` ve `"dangerous_goods_restricted"`
kesin nedenlerdir (talep LP modeline hiç girmeden ön-filtre ile elendi).
`"capacity_exceeded"` ise genel bir sebep — ağırlık, hacim, soğuk zincir kapasitesi
veya priority-class korumalı kapasite kısıtlarından HANGİSİNİN tam olarak bağlayıcı
olduğu ayrıca hesaplanmıyor (bu, solver'ın iç değişkenlerini -- dual value/slack --
incelemeyi gerektirirdi, şu an kapsam dışı). Kısacası: `"capacity_exceeded"` gördüğünde
"bir ya da birden fazla kapasite kısıtı bu talebi engelledi" anlamına gelir, ama hangisi
olduğu net değildir.
