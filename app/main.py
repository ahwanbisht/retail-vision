from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket
from pydantic import BaseModel

from app.analytics.alerts import (
    TelegramAlerter,
    format_alert,
    loitering_trigger,
    overcrowding_trigger,
)

app = FastAPI(title="Retail Vision API")
alerter = TelegramAlerter()


class OccupancyPayload(BaseModel):
    camera_id: str
    people_count: int


class LoiteringPayload(BaseModel):
    camera_id: str
    customer_id: int
    dwell_seconds: float


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "retail-vision"}


@app.post("/alerts/occupancy")
def occupancy_alert(payload: OccupancyPayload) -> dict[str, str | bool]:
    triggered = overcrowding_trigger(payload.people_count)
    if triggered:
        alert_msg = format_alert(
            alert_type="overcrowding",
            camera_id=payload.camera_id,
            severity="high",
            details=f"people_count={payload.people_count}",
        )
        alerter.send(alert_msg)
    return {"triggered": triggered, "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/alerts/loitering")
def loitering_alert(payload: LoiteringPayload) -> dict[str, str | bool]:
    triggered = loitering_trigger(payload.dwell_seconds)
    if triggered:
        alert_msg = format_alert(
            alert_type="loitering",
            camera_id=payload.camera_id,
            severity="medium",
            details=f"customer_id={payload.customer_id}, dwell_seconds={payload.dwell_seconds:.1f}",
        )
        alerter.send(alert_msg)
    return {"triggered": triggered, "timestamp": datetime.now(timezone.utc).isoformat()}


@app.websocket("/ws/occupancy")
async def ws_occupancy(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            people_count = payload.get("people_count", 0)
            await websocket.send_json(
                {
                    "event": "occupancy_update",
                    "people_count": people_count,
                    "triggered": overcrowding_trigger(people_count),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
    except Exception:
        await websocket.close()
