from datetime import datetime, timezone

import requests

from app.config import settings


class TelegramAlerter:
    def __init__(self) -> None:
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id

    @property
    def enabled(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send(self, message: str) -> None:
        if not self.enabled:
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        requests.post(url, json={"chat_id": self.chat_id, "text": message}, timeout=8)


def loitering_trigger(dwell_seconds: float) -> bool:
    return dwell_seconds > settings.alerts.loitering_seconds


def overcrowding_trigger(person_count: int) -> bool:
    return person_count >= settings.alerts.overcrowding_threshold


def suspicious_rapid_movement_trigger(speed_px_per_s: float) -> bool:
    return speed_px_per_s >= settings.alerts.rapid_movement_threshold


def shelf_empty_trigger(empty_seconds: float) -> bool:
    return empty_seconds >= settings.alerts.shelf_empty_seconds


def format_alert(alert_type: str, camera_id: str, severity: str, details: str) -> str:
    ts = datetime.now(timezone.utc).isoformat()
    return f"[{ts}] [{severity.upper()}] {alert_type} @ {camera_id}: {details}"
