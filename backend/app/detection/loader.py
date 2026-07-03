from geoalchemy2.shape import to_shape
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from .analyzer import FlowAnalyzer, LineConfig, ZoneConfig


async def load_zones(session: AsyncSession) -> list[ZoneConfig]:
    result = await session.execute(select(models.Zone))
    zones = []
    for row in result.scalars():
        shape = to_shape(row.geom)
        zones.append(ZoneConfig(id=row.id, name=row.name, polygon=list(shape.exterior.coords)))
    return zones


async def load_lines(session: AsyncSession) -> list[LineConfig]:
    result = await session.execute(select(models.Line))
    lines = []
    for row in result.scalars():
        shape = to_shape(row.geom)
        coords = list(shape.coords)
        lines.append(
            LineConfig(
                id=row.id,
                name=row.name,
                coords=(coords[0], coords[-1]),
                in_direction=row.in_direction,
            )
        )
    return lines


async def reload_analyzer(session: AsyncSession, analyzer: FlowAnalyzer) -> None:
    zones = await load_zones(session)
    lines = await load_lines(session)
    analyzer.set_config(zones, lines)
