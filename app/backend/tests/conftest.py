"""
Testler için ortak fixture'lar. `conftest.py` ismi özel — pytest bu dosyayı
otomatik bulur, içindeki fixture'lar hiçbir import yapılmadan tüm testlerde
kullanılabilir hale gelir.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base
from app.models import Airport, AircraftType, Route, Flight, CargoRequest, OptimizationResult  # noqa: F401


@pytest.fixture()
def db_session():
    """
    Her test için TAMAMEN AYRI, bellekte (in-memory) bir SQLite veritabanı oluşturur.
    Neden gerçek cargo.db'yi kullanmıyoruz: testler birbirini etkilememeli ve
    gerçek/geliştirme verini bozmamalı. Her test kendi temiz veritabanıyla başlar,
    test bitince bu veritabanı tamamen yok olur.
    """
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
