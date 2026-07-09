"""
Settings'in env değişkenlerini doğru okuduğunu ve DATABASE_URL verilmediğinde
SQLite'a düştüğünü doğrular -- Paket C'nin "ikisini de destekle" kararının
kod seviyesinde gerçekten çalıştığının kanıtı.
"""
from app.config import Settings


def test_settings_falls_back_to_sqlite_when_database_url_unset(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert Settings().database_url == "sqlite:///./cargo.db"


def test_settings_reads_database_url_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://cargo:cargo@db:5432/cargo")
    assert Settings().database_url == "postgresql://cargo:cargo@db:5432/cargo"


def test_settings_treats_empty_database_url_as_unset(monkeypatch):
    # .env dosyasında "DATABASE_URL=" (boş) bırakılırsa create_engine("") ile
    # patlamak yerine yine SQLite varsayılanına düşmeli.
    monkeypatch.setenv("DATABASE_URL", "")
    assert Settings().database_url == "sqlite:///./cargo.db"
