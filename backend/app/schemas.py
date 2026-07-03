from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Point = tuple[float, float]


class ZoneCreate(BaseModel):
    name: str
    polygon: list[Point]  # closed or open ring, >= 3 points


class ZoneOut(BaseModel):
    id: int
    name: str
    polygon: list[Point]


class LineCreate(BaseModel):
    name: str
    coords: tuple[Point, Point]
    in_direction: Literal["left", "right"] = "left"


class LineOut(BaseModel):
    id: int
    name: str
    coords: tuple[Point, Point]
    in_direction: str


class ZoneStats(BaseModel):
    zone_id: int
    zone_name: str
    current_occupancy: int
    avg_dwell_seconds: float | None


class CrossingStats(BaseModel):
    line_id: int
    line_name: str
    in_count: int
    out_count: int


class HeatmapCell(BaseModel):
    x: float
    y: float
    count: int


class TrajectoryPoint(BaseModel):
    x: float
    y: float
    ts: datetime
