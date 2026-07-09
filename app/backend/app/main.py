import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# React SPA'nın JS'i kullanıcının TARAYICISINDA çalışır (Streamlit'in aksine, o
# container-to-container çağırıyordu) -- tarayıcı farklı bir origin'den (Vite dev
# sunucusu, ya da Docker'da nginx'in sunduğu statik build) istek attığı için CORS
# izni olmadan her istek engellenir. allow_origins'i bilinen origin'lerle sınırlı
# tutuyoruz (wildcard "*" değil) çünkü /optimize ve /agent/ask maliyetli/etkili
# endpoint'ler.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev sunucusu
        "http://localhost:4173",  # `vite preview` (yerel prod build kontrolü)
        "http://localhost:8080",  # docker-compose'daki frontend container'ının yayınlanan portu
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}
