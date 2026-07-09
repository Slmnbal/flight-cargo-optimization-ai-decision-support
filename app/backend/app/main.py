import logging

from fastapi import FastAPI

from app.api.routes import router

logging.basicConfig(level=logging.INFO)

# Şema artık Alembic tarafından yönetiliyor (bkz. app/backend/alembic/). Burada
# Base.metadata.create_all() ÇAĞRILMIYOR: SQLAlchemy'nin örtük tablo oluşturması ile
# Alembic'in migration geçmişi çakışırsa (Alembic'in haberi olmayan bir tablo var
# olursa), "alembic_version" satırı hiç oluşmaz ve ileride "table already exists"
# hatası ya da sessiz şema sürüklenmesi (drift) yaşanır. Kurulumda artık açık bir adım
# gerekiyor: `alembic upgrade head` (bkz. README).
app = FastAPI(
    title="Flight Cargo Optimization & AI Decision Support System",
    description="Kargo talebi kabul/red kararlarını optimize eden karar destek sistemi.",
    version="0.1.0",
)

app.include_router(router)


@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}
