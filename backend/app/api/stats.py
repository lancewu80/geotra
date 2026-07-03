from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..db import get_session
from ..schemas import CrossingStats, HeatmapCell, TrajectoryPoint, ZoneStats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/zones", response_model=list[ZoneStats])
async def zone_stats(session: AsyncSession = Depends(get_session)):
    zones = (await session.execute(select(models.Zone))).scalars().all()
    results = []
    for zone in zones:
        current_occupancy = (
            await session.execute(
                select(func.count())
                .select_from(models.ZoneOccupancyEvent)
                .where(
                    models.ZoneOccupancyEvent.zone_id == zone.id,
                    models.ZoneOccupancyEvent.exit_ts.is_(None),
                )
            )
        ).scalar_one()
        avg_dwell = (
            await session.execute(
                select(func.avg(models.ZoneOccupancyEvent.dwell_seconds)).where(
                    models.ZoneOccupancyEvent.zone_id == zone.id,
                    models.ZoneOccupancyEvent.exit_ts.is_not(None),
                )
            )
        ).scalar_one()
        results.append(
            ZoneStats(
                zone_id=zone.id,
                zone_name=zone.name,
                current_occupancy=current_occupancy,
                avg_dwell_seconds=avg_dwell,
            )
        )
    return results


@router.get("/crossings", response_model=list[CrossingStats])
async def crossing_stats(since: datetime | None = None, session: AsyncSession = Depends(get_session)):
    lines = (await session.execute(select(models.Line))).scalars().all()
    results = []
    for line in lines:
        in_stmt = select(func.count()).select_from(models.CrossingEvent).where(
            models.CrossingEvent.line_id == line.id, models.CrossingEvent.direction == "in"
        )
        out_stmt = select(func.count()).select_from(models.CrossingEvent).where(
            models.CrossingEvent.line_id == line.id, models.CrossingEvent.direction == "out"
        )
        if since:
            in_stmt = in_stmt.where(models.CrossingEvent.ts >= since)
            out_stmt = out_stmt.where(models.CrossingEvent.ts >= since)
        in_count = (await session.execute(in_stmt)).scalar_one()
        out_count = (await session.execute(out_stmt)).scalar_one()
        results.append(
            CrossingStats(
                line_id=line.id, line_name=line.name, in_count=in_count, out_count=out_count
            )
        )
    return results


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
