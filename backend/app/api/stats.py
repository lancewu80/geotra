from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..db import get_session
from ..schemas import CrossingStats, HeatmapCell, TrajectoryPoint, ZoneStats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/zones", response_model=list[ZoneStats])
async def zone_stats(session: AsyncSession = Depends(get_session)):
    # single aggregate query instead of 1 + 2*N (N = zone count) round trips,
    # so cost doesn't scale with how many clients poll this concurrently
    stmt = (
        select(
            models.Zone.id,
            models.Zone.name,
            func.count(models.ZoneOccupancyEvent.id)
            .filter(models.ZoneOccupancyEvent.exit_ts.is_(None))
            .label("current_occupancy"),
            func.avg(models.ZoneOccupancyEvent.dwell_seconds)
            .filter(models.ZoneOccupancyEvent.exit_ts.is_not(None))
            .label("avg_dwell_seconds"),
        )
        .select_from(models.Zone)
        .outerjoin(models.ZoneOccupancyEvent, models.ZoneOccupancyEvent.zone_id == models.Zone.id)
        .group_by(models.Zone.id, models.Zone.name)
    )
    rows = (await session.execute(stmt)).all()
    return [
        ZoneStats(
            zone_id=r.id,
            zone_name=r.name,
            current_occupancy=r.current_occupancy,
            avg_dwell_seconds=r.avg_dwell_seconds,
        )
        for r in rows
    ]


@router.get("/crossings", response_model=list[CrossingStats])
async def crossing_stats(since: datetime | None = None, session: AsyncSession = Depends(get_session)):
    # the `since` filter has to live in the JOIN condition rather than a
    # WHERE clause, otherwise the outer join degrades into an inner join
    # and lines with zero crossings in the window would drop out entirely
    join_condition = models.CrossingEvent.line_id == models.Line.id
    if since:
        join_condition = and_(join_condition, models.CrossingEvent.ts >= since)

    stmt = (
        select(
            models.Line.id,
            models.Line.name,
            func.count(models.CrossingEvent.id)
            .filter(models.CrossingEvent.direction == "in")
            .label("in_count"),
            func.count(models.CrossingEvent.id)
            .filter(models.CrossingEvent.direction == "out")
            .label("out_count"),
        )
        .select_from(models.Line)
        .outerjoin(models.CrossingEvent, join_condition)
        .group_by(models.Line.id, models.Line.name)
    )
    rows = (await session.execute(stmt)).all()
    return [
        CrossingStats(line_id=r.id, line_name=r.name, in_count=r.in_count, out_count=r.out_count)
        for r in rows
    ]


@router.get("/heatmap", response_model=list[HeatmapCell])
async def heatmap(
    cell_size: float = 20.0,
    since: datetime | None = None,
    session: AsyncSession = Depends(get_session),
):
    grid = func.ST_SnapToGrid(models.TrackPosition.geom, cell_size)
    stmt = select(
        func.ST_X(grid).label("x"),
        func.ST_Y(grid).label("y"),
        func.count().label("count"),
    ).group_by(grid)
    if since:
        stmt = stmt.where(models.TrackPosition.ts >= since)
    rows = (await session.execute(stmt)).all()
    return [HeatmapCell(x=r.x, y=r.y, count=r.count) for r in rows]


@router.get("/trajectory/{track_id}", response_model=list[TrajectoryPoint])
async def trajectory(track_id: int, session: AsyncSession = Depends(get_session)):
    stmt = (
        select(
            models.TrackPosition.ts,
            func.ST_X(models.TrackPosition.geom).label("x"),
            func.ST_Y(models.TrackPosition.geom).label("y"),
        )
        .where(models.TrackPosition.track_id == track_id)
        .order_by(models.TrackPosition.ts)
    )
    rows = (await session.execute(stmt)).all()
    return [TrajectoryPoint(x=r.x, y=r.y, ts=r.ts) for r in rows]
