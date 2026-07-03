from dataclasses import dataclass, field
from datetime import datetime

from .geometry import line_side, point_in_polygon, segments_intersect

XY = tuple[float, float]


@dataclass
class ZoneConfig:
    id: int
    name: str
    polygon: list[XY]


@dataclass
class LineConfig:
    id: int
    name: str
    coords: tuple[XY, XY]
    in_direction: str  # "left" or "right"


@dataclass
class PositionEvent:
    track_id: int
    point: XY
    ts: datetime
    type: str = "position"


@dataclass
class CrossingEvent:
    line_id: int
    track_id: int
    direction: str  # "in" | "out"
    ts: datetime
    type: str = "crossing"


@dataclass
class ZoneEnterEvent:
    zone_id: int
    track_id: int
    ts: datetime
    type: str = "zone_enter"


@dataclass
class ZoneExitEvent:
    zone_id: int
    track_id: int
    enter_ts: datetime
    exit_ts: datetime
    dwell_seconds: float
    type: str = "zone_exit"


Event = PositionEvent | CrossingEvent | ZoneEnterEvent | ZoneExitEvent


@dataclass
class _TrackState:
    last_point: XY | None = None
    zone_enter_ts: dict[int, datetime] = field(default_factory=dict)


class FlowAnalyzer:
    """Stateful per-track analysis: line crossings, zone dwell time.

    Not thread-safe on its own, but is only ever driven from the single
    detector thread that owns it, so no locking is needed.
    """

    def __init__(self, zones: list[ZoneConfig], lines: list[LineConfig]):
        self.zones = zones
        self.lines = lines
        self._tracks: dict[int, _TrackState] = {}

    def set_config(self, zones: list[ZoneConfig], lines: list[LineConfig]) -> None:
        self.zones = zones
        self.lines = lines

    def update(self, track_id: int, point: XY, ts: datetime) -> list[Event]:
        events: list[Event] = []
        state = self._tracks.setdefault(track_id, _TrackState())

        if state.last_point is not None:
            for line in self.lines:
                if segments_intersect(state.last_point, point, line.coords[0], line.coords[1]):
                    side_after = line_side(line.coords, point)
                    # positive cross product = left of the directed line
                    # (p1 -> p2); crossing_side is the side just entered
                    crossing_side = "left" if side_after > 0 else "right"
                    direction = "in" if crossing_side == line.in_direction else "out"
                    events.append(CrossingEvent(line.id, track_id, direction, ts))

        for zone in self.zones:
            inside = point_in_polygon(point, zone.polygon)
            was_inside = zone.id in state.zone_enter_ts
            if inside and not was_inside:
                state.zone_enter_ts[zone.id] = ts
                events.append(ZoneEnterEvent(zone.id, track_id, ts))
            elif not inside and was_inside:
                enter_ts = state.zone_enter_ts.pop(zone.id)
                dwell = (ts - enter_ts).total_seconds()
                events.append(ZoneExitEvent(zone.id, track_id, enter_ts, ts, dwell))

        state.last_point = point
        events.append(PositionEvent(track_id, point, ts))
        return events

    def close_stale_tracks(self, active_track_ids: set[int], ts: datetime) -> list[Event]:
        """Emit zone-exit events for tracks that disappeared while still
        inside a zone (e.g. person walked out of camera view), and drop
        their state so memory doesn't grow unbounded."""
        events: list[Event] = []
        for track_id in list(self._tracks.keys()):
            if track_id in active_track_ids:
                continue
            state = self._tracks.pop(track_id)
            for zone_id, enter_ts in state.zone_enter_ts.items():
                dwell = (ts - enter_ts).total_seconds()
                events.append(ZoneExitEvent(zone_id, track_id, enter_ts, ts, dwell))
        return events
