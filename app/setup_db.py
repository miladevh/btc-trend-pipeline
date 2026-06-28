import os
import psycopg2

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "database": os.environ.get("DB_NAME", "btc_pipeline"),
    "user": os.environ.get("DB_USER", "btc_user"),
    "password": os.environ.get("DB_PASSWORD", "changeme")
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS price_history (
        id SERIAL PRIMARY KEY,
        open_time BIGINT UNIQUE,
        open NUMERIC,
        high NUMERIC,
        low NUMERIC,
        close NUMERIC,
        volume NUMERIC
    )
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id SERIAL PRIMARY KEY,
        prediction_time TIMESTAMP DEFAULT NOW(),
        predicted_label INTEGER,
        actual_label INTEGER,
        model_version TEXT
    )
""")

conn.commit()
print("جدول‌ها با موفقیت ساخته شدند.")

cur.close()
conn.close()