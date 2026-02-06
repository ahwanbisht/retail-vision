from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import cv2
import numpy as np

from app.config import settings


@dataclass
class TrackedCustomer:
    customer_id: int
    entry_time: datetime
    latest_seen: datetime
    path: list[tuple[float, float]] = field(default_factory=list)

    @property
    def dwell_duration(self) -> float:
        return (self.latest_seen - self.entry_time).total_seconds()


class VisionEngine:
    """YOLOv8 + DeepSORT pipeline scaffold for retail analytics."""

    def __init__(self) -> None:
        self.model = self._load_detector(settings.detection.model_path)
        self.tracker = self._load_tracker()
        self.customers: dict[int, TrackedCustomer] = {}
        self.shelf_presence_seconds: dict[str, float] = defaultdict(float)

    def _load_detector(self, model_path: str) -> Any:
        from ultralytics import YOLO

        return YOLO(model_path)

    def _load_tracker(self) -> Any:
        try:
            from deep_sort_realtime.deepsort_tracker import DeepSort  # type: ignore

            return DeepSort(max_age=30, n_init=3)
        except Exception:
            return None

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        return cv2.resize(frame, (settings.detection.frame_width, settings.detection.frame_height))

    def detect(self, frame: np.ndarray) -> list[dict[str, Any]]:
        results = self.model.predict(
            frame,
            conf=settings.detection.confidence_threshold,
            verbose=False,
        )

        detections: list[dict[str, Any]] = []
        result = results[0]
        names = result.names
        for box in result.boxes:
            class_id = int(box.cls.item())
            confidence = float(box.conf.item())
            label = names[class_id]
            if confidence < settings.detection.confidence_threshold:
                continue
            detections.append(
                {
                    "bbox": box.xyxy[0].cpu().numpy().tolist(),
                    "confidence": confidence,
                    "label": label,
                }
            )
        return detections

    def track(self, detections: list[dict[str, Any]]) -> list[TrackedCustomer]:
        now = datetime.now(timezone.utc)
        if not self.tracker:
            return list(self.customers.values())

        ds_input = []
        for d in detections:
            x1, y1, x2, y2 = d["bbox"]
            ds_input.append(([x1, y1, x2 - x1, y2 - y1], d["confidence"], d["label"]))

        tracks = self.tracker.update_tracks(ds_input, frame=None)
        for track in tracks:
            if not track.is_confirmed():
                continue
            track_id = int(track.track_id)
            x1, y1, x2, y2 = track.to_ltrb()
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

            customer = self.customers.get(track_id)
            if customer is None:
                customer = TrackedCustomer(customer_id=track_id, entry_time=now, latest_seen=now)
                self.customers[track_id] = customer

            customer.latest_seen = now
            customer.path.append((cx, cy))

        return list(self.customers.values())
