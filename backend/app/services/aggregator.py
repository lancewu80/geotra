import asyncio
import logging
import time

from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy import update

from .. import models
from ..config import settings
from ..db import async_session_factory
from ..detection.analyzer import CrossingEvent, Event, PositionEvent, ZoneEnterEvent, ZoneExitEvent
from .broadcaster import ConnectionManager

logger = logging.getLogger(__name__)


async def event_consumer(queue: asyncio.Queue, manager: ConnectionManager) -> None:
    """Single consumer task: fans events out to WebSocket clients and
    persists them to Postgres. Position events are batched and flushed on
    an interval to avoid one DB round-trip per frame; crossing/zone events
    are written immediately since they're comparatively rare."""
    position_buffer: list[PositionEvent] = []
    last_flush = time.monotonic()

    while True:
        try:
            events: list[Event] = await asyncio.wait_for(
                queue.get(), timeout=settings.position_flush_interval
            )
        except asyncio.TimeoutError:
            events = []

        for event in events:
            if isinstance(event, PositionEvent):
                position_buffer.append(event)
                await manager.broadcast(
                    {
                        "type": "position",
                        "track_id": event.track_id,
                        "x": event.point[0],
                        "y": event.point[1],
                        "ts": event.ts.isoformat(),
                    }
                )
            elif isinstance(event, CrossingEvent):
                async with async_session_factory() as session:
                    session.add(
                        models.CrossingEvent(
                            line_id=event.line_id,
                            track_id=event.track_id,
                            direction=event.direction,
                            ts=event.ts,
                        )
                    )
                    await session.commit()
                await manager.broadcast(
                    {
                        "type": "crossing",
                        "line_id": event.line_id,
                        "track_id": event.track_id,
                        "direction": event.direction,
                        "ts": event.ts.isoformat(),
                    }
                )
            elif isinstance(event, ZoneEnterEvent):
                async with async_session_factory() as session:
                    session.add(
                        models.ZoneOccupancyEvent(
                            zone_id=event.zone_id,
                            track_id=event.track_id,
                            enter_ts=event.ts,
                            exit_ts=None,
                            dwell_seconds=None,
                        )
                    )
                    await session.commit()
                await manager.broadcast(
                    {
                        "type": "zone_enter",
                        "zone_id": event.zone_id,
                        "track_id": event.track_id,
                        "ts": event.ts.isoformat(),
                    }
                )
            elif isinstance(event, ZoneExitEvent):
                async with async_session_factory() as session:
                    # updates the still-open row created on zone_enter,
                    # rather than inserting a new one, so `exit_ts IS NULL`
                    # always identifies currently-occupied rows
                    stmt = (
                        update(models.ZoneOccupancyEvent)
                        .where(
                            models.ZoneOccupancyEvent.zone_id == event.zone_id,
                            models.ZoneOccupancyEvent.track_id == event.track_id,
                            models.ZoneOccupancyEvent.exit_ts.is_(None),
                        )
                        .values(exit_ts=event.exit_ts, dwell_seconds=event.dwell_seconds)
                    )
                    await session.execute(stmt)
                    await session.commit()
                await manager.broadcast(
                    {
                        "type": "zone_exit",
                        "zone_id": event.zone_id,
                        "track_id": event.track_id,
                        "dwell_seconds": event.dwell_seconds,
                        "ts": event.exit_ts.isoformat(),
                    }
                )

        now = time.monotonic()
        if position_buffer and now - last_flush >= settings.position_flush_interval:
            async with async_session_factory() as session:
                session.add_all(
                    [
                        models.TrackPosition(
                            track_id=e.track_id,
                            ts=e.ts,
                            geom=from_shape(Point(e.point), srid=0),
                        )
                        for e in position_buffer
                    ]
                )
                await session.commit()
            position_buffer.clear()
            last_flush = now
