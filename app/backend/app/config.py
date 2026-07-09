"""
Uygulama ayarları. os.getenv() çağrılarını kod içine dağıtmak yerine, tüm env
değişkenlerini tek bir yerde topluyoruz -- Pydantic bunları otomatik doğrular
(örn. yanlış tipte bir değer verilirse başlangıçta hata verir, sessizce
ilerlemez) ve .env dosyasını otomatik okur.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Env değişkeni verilmezse SQLite'a düşer -- Docker Compose bunu Postgres
    # URL'iyle override eder (bkz. docker-compose.yml).
    database_url: str = "sqlite:///./cargo.db"
    gemini_api_key: str | None = None

    # env_ignore_empty=True: bir env değişkeni tanımlı ama boş ("") ise, onu hiç
    # tanımlanmamış gibi davranıp varsayılana düş. Bunu yapmazsak, .env dosyasında
    # DATABASE_URL= (boş) satırı bırakan biri farkında olmadan create_engine("")
    # ile karşılaşır -- boş satır "sqlite'a düş" niyetiyle bırakılmış olsa bile.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=True)


settings = Settings()
