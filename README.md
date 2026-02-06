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

## Environment Configuration

Create a `.env` file from `.env.example` and set `POSTGRES_URL` to your database connection string. The app reads this automatically via `pydantic-settings`.

```bash
cp .env.example .env
```

### Using Supabase as PostgreSQL

If you already use Supabase, set `POSTGRES_URL` to your Supabase connection URL and include `sslmode=require`.

Example (pooler format):

```env
POSTGRES_URL=postgresql+psycopg2://postgres.<PROJECT_REF>:<PASSWORD>@aws-0-<REGION>.pooler.supabase.com:6543/postgres?sslmode=require
```

Notes:

- In Supabase dashboard, copy the **Connection string** from **Project Settings → Database**.
- Prefer the **pooler** connection string for app/runtime traffic.
- The SQL schema can be applied directly to Supabase Postgres using `psql` or the Supabase SQL editor.

Apply schema with `psql`:

```bash
psql "$POSTGRES_URL" -f app/db/schema.sql
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
