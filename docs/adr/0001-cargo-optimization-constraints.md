# ADR 0001: Kargo Optimizasyonuna Soğuk Zincir, Embargo, Kısıtlı Kargo ve Priority-Class Kısıtları Eklenmesi

## Durum
Kabul edildi (2026-07-09).

## Bağlam

MVP'deki optimizasyon motoru (`app/backend/app/optimization/optimizer.py`) sadece iki kısıt
içeriyordu: her uçuşta toplam ağırlık ve hacim, uçağın kapasitesini aşamaz. Ancak veri
modelinde (`AircraftType`, `Route`, `CargoRequest`) zaten tanımlı ama optimizer tarafından
hiç okunmayan alanlar vardı: `temperature_controlled_capacity_kg`, `requires_temperature_control`,
`embargo_active`, `restricted_cargo_allowed`, `dangerous_goods_allowed`, `priority_class`.
Bu ADR, bu alanları gerçek kısıtlara/karar mantığına dönüştürürken verilen dört tasarım
kararını ve gerekçelerini kayıt altına alıyor.

## Karar 1 — Embargo kapsamı: kargo-tipine-özel

`Route.embargo_active` tek başına "hangi kargo tipi" sorusuna cevap vermiyordu. İki seçenek
vardı: (a) embargo'yu tüm uçuşu kapatan kör bir anahtar olarak bırakmak, (b) kapsamı
daraltabilen yeni bir alan eklemek.

**Seçilen:** `Route.embargoed_cargo_types` (nullable, virgülle ayrılmış `cargo_type` listesi)
eklendi. `embargo_active=True` iken bu alan boşsa TÜM kargo tipleri kapsanır (geriye dönük
uyumlu "kör" davranış), doluysa sadece listelenen tipler kapsanır. Tek bir bool yerine
bool+scope ikilisi, hem "IST-JNB'de sadece canlı hayvan embargosu var" gibi gerçekçi
senaryoları hem de "bu rota tamamen kapalı" gibi kaba senaryoları aynı mekanizmayla,
şema değişikliğini minimumda tutarak ifade edebiliyor.

**Bedeli:** Alembic henüz kurulmadığı için (Paket C) bu şema değişikliği `cargo.db`'nin
silinip yeniden seed edilmesini gerektirdi — geliştirme verisi olduğu için (gitignored)
kabul edilebilir bir maliyet.

## Karar 2 — Priority-class mekanizması: reserved capacity (korumalı kapasite)

Üç seçenek değerlendirildi:

| Seçenek | Garanti gücü | Gerçekçilik | Uygulama |
|---|---|---|---|
| A. Weighted objective (contract'ın revenue'sunu bir çarpanla büyütmek) | Zayıf — sadece yakın-berabere durumlarda tie-break | Orta | Objective fonksiyonunu değiştirir |
| **B. Reserved capacity (seçilen)** | Güçlü, yapısal | Yüksek — gerçek havayolu revenue management pratiği (EMSR/allotment protection) | Ek bir sert kısıt, objective değişmez |
| C. Soft penalty (reddedilen contract için objective'e ceza terimi eklemek) | Ayarlanabilir, garantisiz | Orta | Objective fonksiyonunu değiştirir |

**Seçilen: B.** Her uçuşta `spot` talepler tek başına `(1 - RESERVE_PCT) * max_cargo_weight_kg`'yi
aşamaz (`RESERVE_PCT = 0.30`, `optimizer.py`). Bu, mevcut ağırlık kısıtına **ek** bir kısıt —
onu değiştirmiyor. `RESERVE_PCT` neden 0.30: gerçek revenue management uygulamalarında
tipik korumalı kapasite oranları %20-%40 arasında değişiyor; %30 hem contract kargoya
anlamlı bir koruma sağlıyor hem de spot geliri fazla kısıtlamıyor — kesin bir bilimsel
optimum değil, tartışılabilir bir başlangıç noktası.

**Neden "contract'a alt sınır" değil, "spot'a üst sınır":** Eğer "bu uçuşta en az X kg
contract kargo taşınmalı" şeklinde bir alt sınır kısıtı kursaydık, o uçuşta yeterli contract
talebi yoksa model **infeasible** (çözümsüz) olurdu — solver hiçbir çözüm bulamaz, API hata
döner. Spot'u üstten sınırlamak modeli her zaman çözülebilir tutuyor: contract talebi azsa,
ayrılan kapasite spot tarafından değil, sadece boş kalır (ki bu da gerçekçi — havayolları
gerçekten de bazen kapasiteyi boş bırakmayı, düşük getirili spot kargoyla doldurup daha
sonra yüksek getirili bir contract talebine yer kalmama riskini almaya tercih eder).

## Karar 3 — Dangerous goods / embargo: pre-filter, LP kısıtı değil

İki matematiksel olarak eşdeğer yaklaşım vardı:
- **Pre-filter (seçilen):** talep LP'ye hiç `x_i` değişkeni olarak girmez, `run_optimization`
  içinde LP kurulmadan önce elenir, direkt `status="rejected"` yazılır.
- **Kısıt olarak zorlama:** her elenecek talep için `problem += x_i <= 0` şeklinde bir kısıt
  eklenebilirdi — talep LP'ye girer ama karar değişkeni sıfıra zorlanır.

**Seçilen: pre-filter.** Zaten var olan `status == "pending"` filtresiyle aynı örüntüyü
sürdürüyor, LP'yi küçültüyor (daha az değişken/kısıt = daha hızlı çözüm), ve "bu talep
hiçbir zaman değerlendirmeye alınmadı" ile "değerlendirildi ama reddedildi" arasındaki
kavramsal farkı kodda görünür kılıyor. Kısıt-olarak-zorlama yaklaşımının tek avantajı,
ileride "kaç talep salt embargo yüzünden LP'nin gerçek kapasite kısıtlarına hiç girmeden
elendi" gibi bir analiz istenirse LP'nin kendi çözüm nesnesinden (dual value/slack) bu
bilgiyi çıkarabilmesiydi — bugünkü kapsamda buna ihtiyaç yok.

## Karar 4 — `OptimizationResult.reason` alanı ve bilinen sınırlaması

Agent'ın (Paket D) "neden reddedildi" sorusuna gerçek bir sebep verebilmesi için
`OptimizationResult.reason` alanı eklendi. Pre-filter ile elenen talepler için kesin bir
sebep biliniyor (`"embargo"`, `"dangerous_goods_restricted"`). Ancak LP'nin kendisinin
reddettiği talepler için (ağırlık kapasitesi mi, soğuk zincir mi, yoksa priority-reservation
mı bağlayıcıydı) kesin bir ayrım yapmıyoruz — bunun için LP'nin dual value/slack
değerlerini incelemek gerekirdi, bu kapsam dışı bırakıldı. Bu talepler için tek, genel bir
`"capacity_exceeded"` sebebi kullanılıyor. Bilinçli bir basitleştirme; gelecekte
gerçek kısıt-bazlı ayrım isteniyorsa `pulp`'ın `problem.constraints[...].pi` (dual value)
özelliği araştırılabilir.

## Sonuç

`optimizer.py` artık `Route` tablosunu ilk kez sorguluyor ve önceden tanımlı-ama-kullanılmayan
altı model alanının tamamını gerçek karar mantığına dönüştürüyor. Yeni davranış
`app/backend/tests/test_optimizer.py`'daki altı yeni testle (soğuk zincir, kargo-tipine-özel
embargo, kapsamlı embargo, rota kaynaklı/uçak kaynaklı tehlikeli-madde reddi, priority
reserved-capacity) doğrulanıyor.
