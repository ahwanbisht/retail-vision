from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DetectionConfig(BaseModel):
    model_path: str = "yolov8n.pt"
    frame_width: int = 640
    frame_height: int = 480
    confidence_threshold: float = 0.5
    target_classes: list[str] = ["person", "bottle", "backpack"]
    custom_product_classes: list[str] = []


class AlertConfig(BaseModel):
    loitering_seconds: int = 300
    overcrowding_threshold: int = 20
    rapid_movement_threshold: float = 220.0
    shelf_empty_seconds: int = 90


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "retail-vision"
    postgres_url: str = "postgresql+psycopg2://retail:retail@localhost:5432/retail_vision"
    websocket_ping_seconds: int = 5

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    detection: DetectionConfig = DetectionConfig()
    alerts: AlertConfig = AlertConfig()


settings = Settings()
