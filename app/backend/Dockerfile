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

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
