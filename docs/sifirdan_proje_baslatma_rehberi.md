# Sıfırdan Bir Projeye Nasıl Başlanır? (Adım Adım Zaman Çizelgesi)

Bu doküman diğerlerinden farklı: "hangi kategoriler var" değil, **"hangi sırayla, ne zaman ne yapılır"** sorusuna cevap veriyor. Yeni bir projeye başladığında (bu proje ya da bir sonraki), buradaki sırayı takip edebilirsin.

Temel kural, en başta aklında olsun: **her adımda, elinde her zaman "çalışan ama eksik" bir şey olsun — asla "yarım ve bozuk" bir şey olmasın.** Profesyonellerin amatörlerden en büyük farkı budur: adımları küçük tutup her adımda sistemi çalışır durumda bırakmak.

## Adım 1: Fikri ve Kapsamı Netleştir (Kod Yazmadan Önce)

Hiçbir dosya oluşturmadan önce şu soruların cevabı net olmalı: Bu proje ne yapıyor? Kim kullanacak? En basit hali ne olurdu? Biz bunu bu proje için `docs/project_overview.md` ile yaptık — kod yazmadan önce.

**Neden bu sırada:** Kapsamı belirsizken kod yazmaya başlarsan, yarı yolda "aslında bunu istemiyormuşum" dersin ve baştan yazarsın. Bir sayfalık netlik, günlerce kod yeniden yazmayı önler.

## Adım 2: Proje Klasörünü Oluştur ve HEMEN Git'i Başlat

```
mkdir proje-adi
cd proje-adi
git init
```

**Neden bu kadar erken:** Git'i "proje bitince eklerim" diye ertelemek yaygın bir hata. Git'i en baştan kurarsan, ilk günden itibaren her adımın kaydı tutulur. Geç kurarsan, ilk haftaların hiçbir geçmişi olmaz.

## Adım 3: .gitignore'u İlk Commit'ten ÖNCE Ekle

```
touch .gitignore
```

İçine en azdan şunları yaz: `venv/`, `__pycache__/`, `.env`, `*.db`.

**Neden ilk commit'ten önce:** Eğer önce kod yazıp sonra `.gitignore` eklersen, sanal ortam veya gizli anahtarlar zaten git geçmişine girmiş olabilir — sonradan tamamen silmek çok zahmetlidir. Bu proje boyunca yaşadığımız "backend/venv klasörünü silemedim" sorununu hatırlarsın; `.gitignore`'u en baştan doğru kurmak bu tür başa çıkması zor durumları önler.

## Adım 4: Boş Bir İskelet Oluştur, İlk Commit'i At

Henüz tek satır iş mantığı yazmadan, sadece klasör yapısını kur (`app/`, `tests/`, boş `__init__.py` dosyaları) ve README'ye 2-3 cümlelik bir açıklama yaz. Sonra:

```
git add -A
git commit -m "chore: initial project skeleton"
```

**Neden bu kadar erken bir commit:** "Henüz bir şey yok ki commit atayım" diye düşünmek yaygın bir yanılgı. Boş iskelet bile bir başlangıç noktasıdır — ileride "en baştan beri buradaydım" diyebileceğin bir referans.

## Adım 5: GitHub'da Uzak Depo Oluştur, Hemen Bağla

```
git remote add origin <url>
git branch -M main
git push -u origin main
```

**Neden bu kadar erken:** Yerel bilgisayarın bozulursa/kaybolursa, GitHub'a hiç push etmediysen her şeyi kaybedersin. İlk commit'ten hemen sonra push etmek, projenin "yedeğinin" en baştan var olmasını sağlar.

## Adım 6: Sanal Ortamı Kur, Bağımlılık Dosyasını Oluştur

```
python3 -m venv venv
source venv/bin/activate
```

İlk paketi kurar kurmaz (örn. `pip install fastapi`) hemen:

```
pip freeze > requirements.txt
```

**Neden hemen:** `requirements.txt`'i "sona bırakırım" dersen, hangi paketi hangi sürümle kurduğunu unutursun. Her yeni paket kurulumundan sonra bu dosyayı güncellemek bir alışkanlık olmalı.

## Adım 7: En Basit Çalışan Parçayı Yaz (Tüm Sistemi Değil!)

Burada yaptığımız gibi: önce tek bir veritabanı bağlantısı dosyası (`connection.py`), sonra tek bir model (`Airport`), test et, çalıştığını gör. Tüm modelleri, tüm optimizasyonu, tüm API'yi aynı anda yazmaya kalkma.

**Neden:** Küçük bir parçayı yazıp test etmek, hatayı hemen yakalamanı sağlar. Yüz satır kod yazıp sonra test edersen, hata nerede olduğunu bulmak çok daha zor olur.

## Adım 8: Her Anlamlı Parça Bittiğinde Commit At

Bir model dosyası bitti → commit. Bir endpoint çalıştı → commit. Bir hata düzeltildi → commit. Bizim bu projede yaptığımız gibi: her faz (data layer, optimizasyon, API...) kendi commit'ini aldı.

**Neden sık commit:** Bir şey bozulursa, son çalışan commit'e geri dönebilirsin. Haftalık tek bir dev commit atarsan, o commit içinde hangi değişikliğin neyi bozduğunu bulmak imkansızlaşır.

## Adım 9: İş Mantığı Kritikleştikçe Test Yaz

Her fonksiyona baştan test yazmak zorunda değilsin — ama bir hesaplama yanlış olursa ciddi sonucu olacaksa (bizim optimizasyon motorumuz gibi: yanlış kabul/red kararı gerçek gelir kaybı demek), o noktada test yazma zamanı gelmiştir.

**Ne zaman "şimdi test yazmalıyım" dersin:** Bir fonksiyonu ikinci kez elle test ediyorsan (aynı senaryoyu tekrar tekrar terminalde deniyorsan), o kontrolü bir teste çevirmenin zamanı gelmiştir — elle tekrar tekrar yapmak yerine `pytest` bunu senin için otomatik yapsın.

## Adım 10: Ne Zaman Docker'a Geçersin?

**Docker'a geçmenin doğru zamanı: sistem uçtan uca ELLE çalıştığında.** Yani önce `uvicorn` ve `streamlit`'i kendi terminalinde elle çalıştırıp her şeyin doğru çalıştığını görmelisin — biz bu projede tam olarak bunu yaptık: Faz 1-6 hep yerelde elle test edildi, Docker'a en son (Faz 7'de) geçtik.

**Neden bu kadar geç:** Docker, "çalışan bir şeyi taşınabilir hale getirme" aracıdır — henüz çalışmayan, sık sık değişen bir şeyi Docker'a koymak, her küçük değişiklikte image'ı yeniden derlemek zorunda kalman demek, bu da geliştirmeyi çok yavaşlatır. Önce yerelde hızlı hızlı dene-düzelt döngüsünü tamamla, sistem stabilleşince Docker'a taşı.

**İşareti ne:** Kendine "bu projeyi bir arkadaşıma göndersem, benim bilgisayarımdaki adımları tek tek anlatmam gerekir mi?" diye sor. Cevap "evet" ise, Docker'a geçme vaktin gelmiş demektir.

## Adım 11: Ne Zaman CI/CD (GitHub Actions) Eklersin?

**Doğru zaman: elinde anlamlı, gerçekten bir şeyi doğrulayan testler olduğunda.** Testin yoksa CI'nin çalıştıracağı bir şey yok demektir — boş bir CI kurmak vakit kaybı. Biz bu projede önce testleri (Faz 7'nin başında) yazdık, hemen ardından CI'yi kurduk.

## Adım 12: Ne Zaman "Derinleştirme" Yaparsın?

Uçtan uca, en basit haliyle her şey çalıştıktan SONRA (bizim MVP dediğimiz aşama), geri dönüp derinleştirirsin: daha fazla kısıt, daha gerçekçi veri, daha gelişmiş bir agent, gerçek bir veritabanına (PostgreSQL) geçiş gibi. Bunu en baştan yapmaya çalışmak, hiçbir parçanın bitmemesine yol açar.

## Özet: Sıralama Tablosu

| Sıra | Adım | Ne zaman yapılır |
|---|---|---|
| 1 | Kapsamı netleştir | Kod yazmadan önce |
| 2 | `git init` | Klasörü oluşturur oluşturmaz |
| 3 | `.gitignore` | İlk commit'ten önce |
| 4 | Boş iskelet + ilk commit | Aynı gün |
| 5 | GitHub'a push | İlk commit'ten hemen sonra |
| 6 | venv + requirements.txt | İlk paket kurulumunda |
| 7 | En basit çalışan parça | Büyük özellikten önce her zaman |
| 8 | Sık commit | Her anlamlı adımda |
| 9 | Test yazmaya başla | Bir mantığı elle tekrar tekrar kontrol ediyorsan |
| 10 | Docker | Sistem yerelde uçtan uca elle çalıştığında |
| 11 | CI/CD | Anlamlı testler var olduğunda |
| 12 | Derinleştirme | MVP tamamlandıktan sonra |

Bu sıralama, tam olarak bu projede izlediğimiz yol. Bir sonraki projene başladığında, bu tabloyu aç ve baştan takip et.
