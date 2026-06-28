import os
import requests
import psycopg2
import joblib
import json
import pandas as pd
from datetime import datetime

# مسیر پوشه‌ای که خود این فایل در آن قرار دارد (مستقل از این‌که از کجا اجرا شود)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "database": os.environ.get("DB_NAME", "btc_pipeline"),
    "user": os.environ.get("DB_USER", "btc_user"),
    "password": os.environ.get("DB_PASSWORD", "changeme")
}


def fetch_latest_candles(symbol="BTCUSDT", interval="4h", limit=100):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(url, params=params)
    return response.json()


def save_candles_to_db(candles):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    for c in candles:
        open_time, open_, high, low, close, volume = c[0], c[1], c[2], c[3], c[4], c[5]
        cur.execute("""
            INSERT INTO price_history (open_time, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (open_time) DO NOTHING
        """, (open_time, open_, high, low, close, volume))

    conn.commit()
    cur.close()
    conn.close()


def build_features(candles):
    df = pd.DataFrame(candles, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    df["return_3"] = df["close"].pct_change(3)
    df["return_7"] = df["close"].pct_change(7)
    df["volatility_14"] = df["close"].pct_change().rolling(14).std()
    df["sma20"] = df["close"].rolling(20).mean()
    df["price_sma_ratio"] = df["close"] / df["sma20"]
    df["volume_ratio"] = df["volume"] / df["volume"].rolling(20).mean()
    df["momentum_14"] = df["close"].pct_change(14)

    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))

    sma20_std = df["close"].rolling(20).std()
    df["bb_upper"] = df["sma20"] + 2 * sma20_std
    df["bb_lower"] = df["sma20"] - 2 * sma20_std
    df["bb_position"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

    return df


def predict_latest(df):
    model = joblib.load(os.path.join(BASE_DIR, "rf_model.pkl"))
    with open(os.path.join(BASE_DIR, "features.json")) as f:
        features = json.load(f)

    latest_row = df.iloc[[-1]][features]
    prediction = model.predict(latest_row)[0]
    return int(prediction)


def save_prediction_to_db(prediction):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO predictions (predicted_label, model_version)
        VALUES (%s, %s)
    """, (prediction, "rf_v1"))
    conn.commit()
    cur.close()
    conn.close()


def run_pipeline():
    print(f"[{datetime.now()}] شروع اجرای پایپلاین...")

    candles = fetch_latest_candles()
    save_candles_to_db(candles)
    print("داده جدید ذخیره شد.")

    df = build_features(candles)
    prediction = predict_latest(df)
    print(f"پیش‌بینی: {prediction}")

    save_prediction_to_db(prediction)
    print("پیش‌بینی ذخیره شد.")


if __name__ == "__main__":
    run_pipeline()