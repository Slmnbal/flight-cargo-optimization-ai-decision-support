FROM python:3.11-slim

# CBC solver'ı sistem paketi olarak kuruyoruz (pulp'ın bundled binary'sine
# güvenmek yerine) - bu, Apple Silicon'da yaşadığımız "Bad CPU type" gibi
# mimari uyumsuzluklarını konteyner içinde tamamen ortadan kaldırıyor.
RUN apt-get update && apt-get install -y --no-install-recommends coinor-cbc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

EXPOSE 8000

# Konteyner her başladığında önce şemayı güncel migration seviyesine getir, sonra
# uygulamayı başlat -- gerçek production deploy'ların çalışma şekli budur (şema
# değişikliği, kodun kendisiyle birlikte, otomatik ve açık bir adım olarak uygulanır).
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
