import os
from fastapi import FastAPI
import psycopg2

app = FastAPI()

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "database": os.environ.get("DB_NAME", "btc_pipeline"),
    "user": os.environ.get("DB_USER", "btc_user"),
    "password": os.environ.get("DB_PASSWORD", "changeme"),
    "sslmode": os.environ.get("DB_SSLMODE", "prefer")
}


@app.get("/")
def home():
    return {"message": "سرور ای‌پی‌آی روشن است"}


@app.get("/predict")
def get_latest_prediction():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT prediction_time, predicted_label, model_version
        FROM predictions
        ORDER BY prediction_time DESC
        LIMIT 1
    """)
    row = cur.fetchone()

    cur.close()
    conn.close()

    if row is None:
        return {"error": "هنوز هیچ پیش‌بینی‌ای ثبت نشده است"}

    prediction_time, predicted_label, model_version = row
    trend = "صعودی" if predicted_label == 1 else "نزولی"

    return {
        "prediction_time": str(prediction_time),
        "predicted_label": predicted_label,
        "trend": trend,
        "model_version": model_version
    }