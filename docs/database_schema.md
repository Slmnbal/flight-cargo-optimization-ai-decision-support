# Database Schema — Faz 1

Bu doküman, Data Layer için üzerinde anlaştığımız tabloları tanımlar. İlk versiyonda (MVP) beş çekirdek tablo kuruyoruz: `airports`, `aircraft_types`, `routes`, `flights`, `cargo_requests`. Optimizasyon sonuçlarını tutan tablolar (`scenarios`, `optimization_results`, `accepted_requests`, `rejected_requests`, `kpi_results`) Faz 2/3'te, optimizasyon motoru çalışır hale gelince ekleniyor.

## airports (referans tablosu)

| Alan | Tip | Açıklama |
|---|---|---|
| airport_code | string (PK) | IATA kodu, örn. `IST` |
| airport_name | string | Havalimanı adı |
| country | string | Ülke |
| timezone | string | Saat dilimi |
| customs_available | boolean | Gümrük işlemi yapılabiliyor mu |

## aircraft_types (referans tablosu)

| Alan | Tip | Açıklama |
|---|---|---|
| aircraft_type | string (PK) | Örn. `A350`, `B777F` |
| max_cargo_weight_kg | float | Maksimum kargo ağırlık kapasitesi |
| max_cargo_volume_m3 | float | Maksimum kargo hacim kapasitesi |
| temperature_controlled_capacity_kg | float | Soğuk zincir kapasitesi |
| is_freighter | boolean | Tam kargo uçağı mı |
| dangerous_goods_allowed | boolean | Tehlikeli madde taşıyabiliyor mu |

## routes

| Alan | Tip | Açıklama |
|---|---|---|
| route_id | int (PK) | Benzersiz kimlik |
| origin_airport | string (FK → airports) | Kalkış |
| destination_airport | string (FK → airports) | Varış |
| distance_km | float | Mesafe |
| route_type | string | `domestic` / `international` |
| region | string | Örn. Europe, North America |
| customs_required | boolean | Gümrük gerekiyor mu |
| restricted_cargo_allowed | boolean | Tehlikeli madde/canlı hayvan izni var mı |
| embargo_active | boolean | Geçici kargo kısıtlaması var mı |
| is_active | boolean | Rota hâlâ uçuluyor mu |

## flights

| Alan | Tip | Açıklama |
|---|---|---|
| flight_id | int (PK) | Benzersiz kimlik |
| flight_number | string | Örn. `TK001` |
| route_id | int (FK → routes) | Hangi rotaya ait |
| aircraft_type | string (FK → aircraft_types) | Uçak tipi |
| aircraft_registration | string | Kuyruk numarası |
| departure_scheduled | datetime | Planlanan kalkış |
| departure_actual | datetime (nullable) | Gerçekleşen kalkış |
| arrival_scheduled | datetime | Planlanan varış |
| arrival_actual | datetime (nullable) | Gerçekleşen varış |
| status | string | `scheduled` / `departed` / `delayed` / `cancelled` |

## cargo_requests

| Alan | Tip | Açıklama |
|---|---|---|
| request_id | int (PK) | Benzersiz kimlik |
| flight_id | int (FK → flights) | Talep edilen uçuş |
| cargo_type | string | `general` / `perishable` / `dangerous_goods` / `live_animal` / `valuable` / `oversized` |
| weight_kg | float | Ağırlık |
| volume_m3 | float | Hacim |
| requires_temperature_control | boolean | Soğuk zincir gerekiyor mu |
| priority_class | string | `contract` / `spot` |
| revenue | float | Bu talebi kabul edersek elde edilecek gelir |
| booking_cutoff_hours | int | Uçuştan kaç saat önce teslim gerekiyor |
| status | string | `pending` / `accepted` / `rejected` (optimizasyon sonrası güncellenir) |

## İlişkiler (özet)

`airports` ← `routes` (origin/destination) ← `flights` (route_id) ← `cargo_requests` (flight_id). `aircraft_types` ← `flights` (aircraft_type).

## Sıradaki Adım

Bu şemayı SQLAlchemy modellerine dönüştürüyoruz: `backend/app/models/` altında her tablo için bir Python dosyası.
