"""
Kabul olasılığı tahmin modeli.

Geçmiş optimizasyon sonuçlarını (kabul/red edilmiş talepler) kullanarak, yeni bir
kargo talebinin kabul edilme olasılığını tahmin eder. Gerçek sistemde bu tahmin,
optimizasyon modeline "öncelik skoru" olarak girdi verilebilir (örn. kabul olasılığı
düşük ama gelirli talepleri daha erken teklif etmek gibi kararlarda kullanılabilir).
"""
from pathlib import Path

import joblib
import mlflow
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sqlalchemy.orm import Session

from app.models import CargoRequest, OptimizationResult

FEATURES = ["weight_kg", "volume_m3", "revenue"]

# Eğitilen modeli diske kaydediyoruz ki API her /ml/predict çağrısında modeli
# yeniden eğitmek zorunda kalmasın; sunucu yeniden başlasa bile model kaybolmaz.
# Gerçek production sistemlerinde bu genelde bir "model registry" (örn. MLflow
# Model Registry, S3) ile yapılır; burada basitleştirip yerel dosyaya kaydediyoruz.
MODEL_PATH = Path(__file__).parent / "model_store" / "acceptance_model.joblib"


def train_acceptance_model(db: Session):
    rows = (
        db.query(CargoRequest, OptimizationResult)
        .join(OptimizationResult, OptimizationResult.request_id == CargoRequest.request_id)
        .all()
    )

    if len(rows) < 10:
        return None, "Yeterli geçmiş veri yok (en az 10 sonuç gerekli). Önce /optimize çalıştır."

    data = pd.DataFrame(
        [
            {
                "weight_kg": req.weight_kg,
                "volume_m3": req.volume_m3,
                "revenue": req.revenue,
                "accepted": 1 if res.decision == "accepted" else 0,
            }
            for req, res in rows
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        data[FEATURES], data["accepted"], test_size=0.2, random_state=42
    )

    with mlflow.start_run():
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        predictions = model.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)

        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("features", FEATURES)
        mlflow.log_metric("accuracy", accuracy)
        mlflow.sklearn.log_model(model, "acceptance_model")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    return model, {"accuracy": accuracy, "n_samples": len(data)}


def load_model():
    """Diskten kayıtlı modeli yükler. Hiç eğitilmemişse None döner."""
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)


def predict_acceptance_probability(model, weight_kg: float, volume_m3: float, revenue: float) -> float:
    df = pd.DataFrame([{"weight_kg": weight_kg, "volume_m3": volume_m3, "revenue": revenue}])
    return float(model.predict_proba(df[FEATURES])[0][1])
