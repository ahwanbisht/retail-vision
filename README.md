# retail-vision

Retail analytics stack scaffold built around:

- YOLOv8 (`yolov8n.pt`) for object detection
- DeepSORT for customer tracking
- FastAPI + WebSocket for real-time APIs
- PostgreSQL schema for structured retail telemetry
- Telegram alert integration for operational notifications
- Streamlit dashboard for management analytics
- React dashboard contract for staff-facing live metrics

## Detection and Tracking Defaults

- Resize input frames to `640x480`
- Confidence threshold defaults to `0.5` (tunable to `0.4-0.6`)
- Initial classes: `person`, `bottle`, `backpack`
- Support for custom product classes via configuration

## Performance Targets

- `>=15 FPS` on GPU
- `>=90%` precision after model calibration/fine-tuning

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Streamlit dashboard:

```bash
streamlit run dashboards/streamlit_app.py
```

## Database Schema

SQL schema lives in `app/db/schema.sql` with required tables:

- `customers`
- `movements`
- `alerts`
- `product_interactions`

## Telegram Alerts

Set the following in `.env`:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Alerts currently supported:

- Loitering (`>5 min`)
- Overcrowding (`>= threshold people`)
- Suspicious rapid movement threshold function
- Shelf-empty threshold function
