from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

DATABASE_URL = settings.database_url

# check_same_thread SQLite'a özgü bir bayrak: SQLite varsayılan olarak bir bağlantının
# sadece açıldığı thread'den kullanılmasına izin verir, FastAPI ise her isteği farklı
# bir thread'de işleyebilir -- bu yüzden SQLite'ta bunu kapatmamız gerekiyor. Postgres/
# psycopg2 böyle bir kısıtlamaya sahip değil, dolayısıyla bu argümanı ona hiç göndermiyoruz.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: her istekte bir DB oturumu açar, iş bitince kapatır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
