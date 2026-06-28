import schedule
import time
from run_pipeline import run_pipeline

def job():
    try:
        run_pipeline()
    except Exception as e:
        print(f"خطا در اجرای پایپلاین: {e}")

# هر چهار ساعت یک‌بار، تابع job را اجرا کن
schedule.every(4).hours.do(job)

print("زمان‌بند روشن شد. هر چهار ساعت پایپلاین اجرا می‌شود.")

# اولین اجرا، بدون نیاز به صبر چهار ساعته (تا ببینیم بلافاصله کار می‌کند)
job()

# حلقه‌ی دائمی که هر دقیقه چک می‌کند آیا وقتش رسیده یا نه
while True:
    schedule.run_pending()
    time.sleep(60)
