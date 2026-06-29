# BTC Trend Pipeline

An end-to-end machine learning pipeline that predicts the weekly price trend (up/down) of Bitcoin using live market data. The project covers the full lifecycle: data ingestion, feature engineering, model training, a live prediction API, and containerized deployment.

> **Disclaimer:** This project is built to demonstrate ML engineering and MLOps skills (data pipelines, model serving, containerization). It is **not** a financial tool and should not be used for actual trading decisions. Short-to-medium term price movement is notoriously close to a random walk, and this project treats it as a hard, noisy classification problem rather than a solved one.

## Overview

The pipeline fetches BTC/USDT candlestick data from the Binance API, engineers technical indicators (RSI, moving averages, Bollinger Bands, momentum), and trains a classifier to predict whether the price trend over the next 7 days will be bullish or bearish. Predictions are served through a FastAPI endpoint, and the full system runs in Docker.

## Architecture

```
Binance API → run_pipeline.py → PostgreSQL → FastAPI → /predict
                    ↑                              ↓
              (cron, every 4h)              JSON response
```

1. **Ingestion**: `run_pipeline.py` fetches the latest 4h candles from Binance
2. **Storage**: Raw candles are stored in a `price_history` table (PostgreSQL)
3. **Feature engineering**: Technical indicators are computed on the fly
4. **Prediction**: A trained model predicts next-week trend direction
5. **Logging**: Each prediction is stored in a `predictions` table
6. **Serving**: FastAPI exposes the latest prediction via `/predict`

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python |
| Data | Pandas, NumPy |
| Modeling | Scikit-learn (Random Forest), XGBoost |
| Database | PostgreSQL |
| API | FastAPI, Uvicorn |
| Dashboard | Streamlit, Plotly |
| Containerization | Docker, Docker Compose |
| Scheduling | In-process scheduler (`schedule` library) |
| Data source | Binance public API |

## Model Results

Two models were trained and compared on a time-based train/test split (no shuffling, to avoid lookahead bias):

| Model | Accuracy | Notes |
|---|---|---|
| Random Forest | ~55% | Best performing, more stable on noisy features |
| XGBoost | ~54% | Slightly more prone to overfitting on this dataset |

For context, a coin-flip baseline is 50%. In financial trend prediction, this is a modest but genuine edge — consistent with the well-documented difficulty of predicting short/medium-term price direction from technical indicators alone.

**Features used:** 3-day and 7-day returns, 14-day volatility, price-to-SMA20 ratio, RSI, volume ratio, 14-day momentum, Bollinger Band position.

**Target:** Binary label — whether the price 7 days ahead moved more than ±3% from the current close.

## Project Structure

```
btc-trend-pipeline/
├── app/
│   ├── api.py              # FastAPI app, serves predictions
│   ├── dashboard.py        # Streamlit dashboard with live chart and manual trigger
│   ├── run_pipeline.py     # Fetches data, predicts, stores results
│   ├── scheduler.py        # Runs run_pipeline() automatically every 4h
│   ├── setup_db.py         # Creates database tables
│   ├── entrypoint.sh       # Starts scheduler + API + dashboard together
│   ├── rf_model.pkl        # Trained Random Forest model
│   └── features.json       # Feature list used by the model
├── notebooks/
│   └── model_training.ipynb # Full exploration, feature engineering, training
├── Dockerfile
├── docker-compose.yml
├── requirements.txt         # Minimal deps for running the app
└── requirements-dev.txt     # Full deps for notebook/training environment
```

## Running Locally with Docker

**Requirements:** Docker and Docker Compose installed.

1. Clone the repository:
   ```bash
   git clone https://github.com/miladevh/btc-trend-pipeline.git
   cd btc-trend-pipeline
   ```

2. Create a `.env` file in the project root:
   ```
   POSTGRES_DB=btc_pipeline
   POSTGRES_USER=btc_user
   POSTGRES_PASSWORD=your_password_here
   ```

3. Build and start the containers:
   ```bash
   docker compose up --build
   ```

4. Initialize the database tables (first run only):
   ```bash
   docker compose exec app python setup_db.py
   ```

5. Restart the app container so the scheduler can pick up the newly created tables:
   ```bash
   docker compose restart app
   ```

   The scheduler triggers an initial prediction automatically on startup — no manual run needed.

6. Query the API:
   ```bash
   curl http://localhost:8000/predict
   ```

   Example response:
   ```json
   {
     "prediction_time": "2026-06-28 02:48:05",
     "predicted_label": -1,
     "trend": "نزولی",
     "model_version": "rf_v1"
   }
   ```

## Dashboard

A Streamlit dashboard is available at `http://localhost:8501`, showing:
- The latest prediction, with trend, timestamp (converted to local time), and model version
- A manual "run pipeline now" button — fetches live data and generates a fresh prediction on demand, instead of waiting for the next scheduled run
- A price chart of the last 200 candles
- A history table of the most recent predictions

## Scheduling

The pipeline runs automatically every 4 hours (matching the candle interval) using an in-process scheduler (`scheduler.py`, built on the `schedule` library), not a system-level cron job. This keeps the project fully portable — the same container runs identically on any host with Docker, regardless of OS, with no external scheduler dependency.

Inside the container, `entrypoint.sh` starts both processes together:
- `scheduler.py` runs in the background, triggering `run_pipeline()` immediately on startup and then every 4 hours
- `uvicorn` runs in the foreground, serving the FastAPI app

```bash
#!/bin/bash
python scheduler.py &
uvicorn api:app --host 0.0.0.0 --port 8000
```

## Key Design Decisions

- **7-day trend instead of next-candle price**: Short-term BTC price movement is dominated by noise. Predicting a directional trend over a longer horizon produces a more learnable signal and a more realistic, defensible target.
- **Relative features over absolute values**: Raw price and volume were intentionally excluded from the feature set. Since BTC's price scale has changed enormously over time, raw values leak time-period information. Ratios, returns, and oscillators (RSI, Bollinger position) generalize better across time.
- **Time-based train/test split**: A random shuffle split would leak future information into training. The split here respects chronological order.
- **Two requirements files**: `requirements.txt` is kept minimal for the production container (fast builds); `requirements-dev.txt` captures the full notebook/exploration environment.
- **Environment-based configuration**: Database credentials and connection details are read from environment variables, not hardcoded, so the same code runs identically on a local machine and inside Docker.

## Possible Next Steps

- Replace the in-process scheduler with a managed orchestrator (e.g., Airflow) for more complex retraining workflows
- Add model monitoring to track prediction drift over time (`actual_label` column is already in place)
- Deploy to a cloud platform for public access

## Author

Milad Hatami — [GitHub](https://github.com/miladevh) · [LinkedIn](https://www.linkedin.com/in/miladhatami-310302297/)