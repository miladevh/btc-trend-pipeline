import streamlit as st
import psycopg2
import pandas as pd
import plotly.graph_objects as go
import os
from datetime import timezone, timedelta

IRAN_TZ = timezone(timedelta(hours=3, minutes=30))

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "database": os.environ.get("DB_NAME", "btc_pipeline"),
    "user": os.environ.get("DB_USER", "btc_user"),
    "password": os.environ.get("DB_PASSWORD", "changeme")
}

st.set_page_config(page_title="BTC Trend Pipeline", page_icon="📈", layout="wide")

st.title("📈 BTC Trend Pipeline Dashboard")
st.caption("یک پروژه‌ی نمایشی برای پیش‌بینی روند هفتگی بیت‌کوین — صرفاً برای نمایش مهارت، نه ابزار معاملاتی")


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def to_iran_time(utc_dt):
    """زمان ذخیره‌شده در پایگاه‌داده را که UTC است، به ساعت ایران تبدیل می‌کند."""
    if utc_dt is None:
        return None
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(IRAN_TZ)


def load_price_history():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT open_time, close
        FROM price_history
        ORDER BY open_time DESC
        LIMIT 200
    """, conn)
    conn.close()
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    return df.sort_values("open_time")


def load_latest_prediction():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT prediction_time, predicted_label, model_version
        FROM predictions
        ORDER BY prediction_time DESC
        LIMIT 1
    """, conn)
    conn.close()
    return df


def load_prediction_history():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT prediction_time, predicted_label, model_version
        FROM predictions
        ORDER BY prediction_time DESC
        LIMIT 20
    """, conn)
    conn.close()
    return df


# بخش اول: آخرین پیش‌بینی
latest = load_latest_prediction()

if latest.empty:
    st.warning("هنوز هیچ پیش‌بینی‌ای ثبت نشده است.")
else:
    label = latest.iloc[0]["predicted_label"]
    time = to_iran_time(latest.iloc[0]["prediction_time"])
    version = latest.iloc[0]["model_version"]

    col1, col2, col3 = st.columns(3)

    with col1:
        if label == 1:
            st.metric("روند پیش‌بینی‌شده", "صعودی 📈")
        else:
            st.metric("روند پیش‌بینی‌شده", "نزولی 📉")

    with col2:
        st.metric("زمان آخرین پیش‌بینی", str(time))

    with col3:
        st.metric("نسخه مدل", version)

st.divider()

# بخش جدید: پیش‌بینی دستی و آنی
st.subheader("درخواست پیش‌بینی تازه")
st.caption("به‌جای صبر کردن برای اجرای خودکار هر چهار ساعت، همین حالا یک پیش‌بینی تازه بساز.")

if st.button("🔄 اجرای پایپلاین و پیش‌بینی جدید", type="primary"):
    with st.spinner("در حال گرفتن داده‌ی زنده از بایننس و محاسبه‌ی پیش‌بینی..."):
        try:
            from run_pipeline import run_pipeline
            run_pipeline()
            st.success("پیش‌بینی تازه با موفقیت ساخته و ذخیره شد!")
            st.rerun()
        except Exception as e:
            st.error(f"خطا در اجرای پایپلاین: {e}")

st.divider()

# بخش دوم: نمودار قیمت
st.subheader("روند قیمت بیت‌کوین (۲۰۰ کندل اخیر)")
price_df = load_price_history()

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=price_df["open_time"],
    y=price_df["close"],
    mode="lines",
    name="قیمت بسته‌شدن"
))
fig.update_layout(xaxis_title="زمان", yaxis_title="قیمت (دلار)", height=400)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# بخش سوم: تاریخچه پیش‌بینی‌ها
st.subheader("تاریخچه‌ی پیش‌بینی‌های اخیر")
history_df = load_prediction_history()
history_df["prediction_time"] = history_df["prediction_time"].apply(to_iran_time)
history_df["trend"] = history_df["predicted_label"].apply(lambda x: "صعودی 📈" if x == 1 else "نزولی 📉")
st.dataframe(
    history_df[["prediction_time", "trend", "model_version"]],
    use_container_width=True
)