from datetime import datetime

from geoalchemy2 import Geometry, WKBElement
from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Zone(Base):
    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    geom: Mapped[WKBElement] = mapped_column(Geometry(geometry_type="POLYGON", srid=0), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Line(Base):
    __tablename__ = "lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    geom: Mapped[WKBElement] = mapped_column(Geometry(geometry_type="LINESTRING", srid=0), nullable=False)
    in_direction: Mapped[str] = mapped_column(String, nullable=False, default="left")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (CheckConstraint("in_direction IN ('left', 'right')"),)


class TrackPosition(Base):
    __tablename__ = "track_positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    track_id: Mapped[int] = mapped_column(Integer, nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    geom: Mapped[WKBElement] = mapped_column(Geometry(geometry_type="POINT", srid=0), nullable=False)


class CrossingEvent(Base):
    __tablename__ = "crossing_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    line_id: Mapped[int] = mapped_column(ForeignKey("lines.id", ondelete="CASCADE"), nullable=False)
    track_id: Mapped[int] = mapped_column(Integer, nullable=False)
    direction: Mapped[str] = mapped_column(String, nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (CheckConstraint("direction IN ('in', 'out')"),)


class ZoneOccupancyEvent(Base):
    __tablename__ = "zone_occupancy_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id", ondelete="CASCADE"), nullable=False)
    track_id: Mapped[int] = mapped_column(Integer, nullable=False)
    enter_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exit_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dwell_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
