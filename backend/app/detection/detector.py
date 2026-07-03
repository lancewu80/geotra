import asyncio
import logging
import threading
from datetime import datetime, timezone
from typing import Callable

from ..config import settings
from .analyzer import Event, FlowAnalyzer

logger = logging.getLogger(__name__)

EventCallback = Callable[[list[Event]], None]


class VideoDetector:
    """Runs YOLO detection + ByteTrack tracking on a webcam stream inside a
    dedicated OS thread (ultralytics' streaming generator blocks on frame
    capture, so it can't live on the asyncio event loop). Detected events
    are handed off to the event loop via `loop.call_soon_threadsafe`.
    """

    def __init__(self, analyzer: FlowAnalyzer, loop: asyncio.AbstractEventLoop, event_queue: asyncio.Queue):
        self.analyzer = analyzer
        self._loop = loop
        self._queue = event_queue
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="video-detector", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _emit(self, events: list[Event]) -> None:
        if not events:
            return
        self._loop.call_soon_threadsafe(self._queue.put_nowait, events)

    def _run(self) -> None:
        from ultralytics import YOLO  # imported lazily: heavy import, only needed here

        source: str | int = settings.camera_source
        try:
            source = int(source)
        except ValueError:
            pass

        model = YOLO(settings.yolo_model)
        try:
            results = model.track(
                source=source,
                classes=[0],  # COCO class 0 = person
                persist=True,
                stream=True,
                tracker="bytetrack.yaml",
                device=settings.yolo_device,
                verbose=False,
            )
            for result in results:
                if self._stop.is_set():
                    break

                ts = datetime.now(timezone.utc)
                active_ids: set[int] = set()
                events: list[Event] = []

                boxes = result.boxes
                if boxes is not None and boxes.id is not None:
                    for xyxy, tid in zip(boxes.xyxy.tolist(), boxes.id.tolist()):
                        track_id = int(tid)
                        active_ids.add(track_id)
                        x1, y1, x2, y2 = xyxy
                        foot_point = ((x1 + x2) / 2, y2)  # bottom-center ~ ground contact point
                        events.extend(self.analyzer.update(track_id, foot_point, ts))

                events.extend(self.analyzer.close_stale_tracks(active_ids, ts))
                self._emit(events)
        except Exception:
            logger.exception("video detector loop crashed")
