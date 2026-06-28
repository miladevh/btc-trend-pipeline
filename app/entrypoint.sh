#!/bin/bash
# هر دو پردازش را در پس‌زمینه اجرا کن
python scheduler.py &
uvicorn api:app --host 0.0.0.0 --port 8000
