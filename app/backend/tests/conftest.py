"""
Testler için ortak fixture'lar. `conftest.py` ismi özel — pytest bu dosyayı
otomatik bulur, içindeki fixture'lar hiçbir import yapılmadan tüm testlerde
kullanılabilir hale gelir.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
from app.models import Airport, AircraftType, Route, Flight, CargoRequest, OptimizationResult, AgentMessage  # noqa: F401


@pytest.fixture()
def db_session():
    """
    Her test için TAMAMEN AYRI, bellekte (in-memory) bir SQLite veritabanı oluşturur.
    Neden gerçek cargo.db'yi kullanmıyoruz: testler birbirini etkilememeli ve
    gerçek/geliştirme verini bozmamalı. Her test kendi temiz veritabanıyla başlar,
    test bitince bu veritabanı tamamen yok olur.

    poolclass=StaticPool: SQLite ":memory:" veritabanları varsayılan olarak
    thread-local'dır -- her yeni thread yeni (boş) bir bellek veritabanına bağlanır.
    test_api.py'deki FastAPI TestClient istekleri farklı bir thread'de çalışabildiği
    için, StaticPool olmadan create_all() ile oluşturulan tablolar TestClient'ın
    gördüğü bağlantıda "no such table" hatasına yol açar. StaticPool tüm
    bağlantıların (hangi thread'den gelirse gelsin) AYNI tek bağlantıyı
    paylaşmasını sağlayarak bunu önler.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
