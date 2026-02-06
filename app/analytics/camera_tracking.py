from __future__ import annotations

import argparse
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import cv2
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from ultralytics import YOLO

from app.config import settings
from app.db.models import Customer, Movement

try:
    from deep_sort_realtime.deepsort_tracker import DeepSort
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "deep-sort-realtime is required for camera tracking. Install with: pip install -r requirements-vision.txt"
    ) from exc


@dataclass
class TrackState:
    track_id: int
    entry_time: datetime
    last_seen: datetime
    path: list[tuple[float, float]] = field(default_factory=list)
    db_customer_id: int | None = None
    shelf_dwell_start: datetime | None = None
    shelf_dwell_seconds: float = 0.0


class CameraTrackerApp:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.model = YOLO(args.model)
        self.tracker = DeepSort(max_age=30, n_init=3)
        self.target_classes = {"person", "bottle", "backpack"}
        self.target_classes.update(args.product_classes)
        self.track_states: dict[int, TrackState] = {}
        self.lost_timeout_seconds = args.lost_timeout_seconds

        self.engine = create_engine(settings.postgres_url, future=True)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def _inside_shelf_zone(self, cx: float, cy: float) -> bool:
        if not self.args.shelf_zone:
            return False
        x1, y1, x2, y2 = self.args.shelf_zone
        return x1 <= cx <= x2 and y1 <= cy <= y2

    def _upsert_state(self, session: Session, track_id: int, cx: float, cy: float, now: datetime) -> TrackState:
        state = self.track_states.get(track_id)
        if state is None:
            customer = Customer(entry_time=now)
            session.add(customer)
            session.flush()
            state = TrackState(track_id=track_id, entry_time=now, last_seen=now, db_customer_id=customer.id)
            self.track_states[track_id] = state

        state.last_seen = now
        state.path.append((cx, cy))

        if state.db_customer_id is not None:
            session.add(
                Movement(
                    customer_id=state.db_customer_id,
                    timestamp=now,
                    x_coordinate=float(cx),
                    y_coordinate=float(cy),
                )
            )

        if self._inside_shelf_zone(cx, cy):
            if state.shelf_dwell_start is None:
                state.shelf_dwell_start = now
        elif state.shelf_dwell_start is not None:
            state.shelf_dwell_seconds += (now - state.shelf_dwell_start).total_seconds()
            state.shelf_dwell_start = None

        return state

    def _finalize_lost_tracks(self, session: Session, active_track_ids: set[int], now: datetime) -> None:
        to_finalize: list[int] = []
        for tid, state in self.track_states.items():
            is_lost = tid not in active_track_ids and (now - state.last_seen).total_seconds() > self.lost_timeout_seconds
            if is_lost:
                to_finalize.append(tid)

        for tid in to_finalize:
            state = self.track_states.pop(tid)
            if state.shelf_dwell_start is not None:
                state.shelf_dwell_seconds += (now - state.shelf_dwell_start).total_seconds()
                state.shelf_dwell_start = None

            if state.db_customer_id is not None:
                customer = session.get(Customer, state.db_customer_id)
                if customer is not None:
                    customer.exit_time = now
                    customer.total_time_spent = (now - state.entry_time).total_seconds()

    def run(self) -> None:
        cap = cv2.VideoCapture(self.args.camera_index)
        if not cap.isOpened():
            raise RuntimeError("Unable to open camera. Try --camera-index 1")

        last_frame_time = time.perf_counter()

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                frame = cv2.resize(frame, (self.args.width, self.args.height))
                now = datetime.now(timezone.utc)

                results = self.model.predict(frame, conf=self.args.confidence, verbose=False)
                result = results[0]
                names = result.names

                deep_sort_input = []
                for box in result.boxes:
                    class_id = int(box.cls.item())
                    confidence = float(box.conf.item())
                    label = names[class_id]
                    if label not in self.target_classes:
                        continue

                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().tolist()
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 190, 255), 2)
                    cv2.putText(
                        frame,
                        f"{label} {confidence:.2f}",
                        (int(x1), int(y1) - 8),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 190, 255),
                        2,
                    )

                    if label == "person":
                        deep_sort_input.append(([x1, y1, x2 - x1, y2 - y1], confidence, label))

                tracks = self.tracker.update_tracks(deep_sort_input, frame=frame)
                active_track_ids: set[int] = set()

                with self.session_factory() as session:
                    for track in tracks:
                        if not track.is_confirmed():
                            continue

                        tid = int(track.track_id)
                        active_track_ids.add(tid)
                        x1, y1, x2, y2 = track.to_ltrb()
                        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

                        state = self._upsert_state(session, tid, cx, cy, now)

                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (50, 220, 50), 2)
                        cv2.putText(
                            frame,
                            f"ID {tid} dwell {state.shelf_dwell_seconds:.1f}s",
                            (int(x1), int(y2) + 16),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (50, 220, 50),
                            2,
                        )

                    self._finalize_lost_tracks(session, active_track_ids, now)
                    session.commit()

                if self.args.shelf_zone:
                    x1, y1, x2, y2 = self.args.shelf_zone
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 100, 100), 2)
                    cv2.putText(frame, "Shelf zone", (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 100, 100), 2)

                now_perf = time.perf_counter()
                fps = 1.0 / max(now_perf - last_frame_time, 1e-6)
                last_frame_time = now_perf
                cv2.putText(frame, f"FPS: {fps:.1f}", (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

                cv2.imshow("Retail Vision Camera", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run YOLOv8 + DeepSORT on laptop camera")
    parser.add_argument("--model", default=settings.detection.model_path, help="YOLO model path")
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--width", type=int, default=settings.detection.frame_width)
    parser.add_argument("--height", type=int, default=settings.detection.frame_height)
    parser.add_argument("--confidence", type=float, default=settings.detection.confidence_threshold)
    parser.add_argument("--lost-timeout-seconds", type=float, default=2.0)
    parser.add_argument(
        "--product-classes",
        type=lambda s: [x.strip() for x in s.split(",") if x.strip()],
        default=[],
        help="Comma-separated custom product labels to render (for fine-tuned models).",
    )
    parser.add_argument(
        "--shelf-zone",
        type=lambda s: tuple(int(v) for v in s.split(",")),
        default=None,
        help="Optional shelf rectangle x1,y1,x2,y2 used for dwell-time accumulation.",
    )

    args = parser.parse_args()
    if not (0.4 <= args.confidence <= 0.6):
        raise ValueError("Set --confidence in the recommended range 0.4 to 0.6")
    if args.shelf_zone is not None and len(args.shelf_zone) != 4:
        raise ValueError("--shelf-zone must be x1,y1,x2,y2")
    return args


if __name__ == "__main__":
    CameraTrackerApp(parse_args()).run()
