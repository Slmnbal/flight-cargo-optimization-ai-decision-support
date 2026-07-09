import logging

from fastapi import FastAPI

from app.database.connection import Base, engine
from app.api.routes import router

logging.basicConfig(level=logging.INFO)

# Base.metadata artık app.models üzerinden (routes.py -> app.models import zinciri ile)
# tüm modelleri tanıyor, bu yüzden burada tüm tablolar güvenle oluşturulur.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Flight Cargo Optimization & AI Decision Support System",
    description="Kargo talebi kabul/red kararlarını optimize eden karar destek sistemi.",
    version="0.1.0",
)

app.include_router(router)


@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}
