from fastapi import APIRouter, Depends
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Polygon
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..db import get_session
from ..deps import get_analyzer
from ..detection.analyzer import FlowAnalyzer
from ..detection.loader import reload_analyzer
from ..schemas import ZoneCreate, ZoneOut

router = APIRouter(prefix="/zones", tags=["zones"])


@router.get("", response_model=list[ZoneOut])
async def list_zones(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(models.Zone))
    return [
        ZoneOut(id=z.id, name=z.name, polygon=list(to_shape(z.geom).exterior.coords))
        for z in result.scalars()
    ]


@router.post("", response_model=ZoneOut)
async def create_zone(
    payload: ZoneCreate,
    session: AsyncSession = Depends(get_session),
    analyzer: FlowAnalyzer = Depends(get_analyzer),
):
    polygon = Polygon(payload.polygon)
    zone = models.Zone(name=payload.name, geom=from_shape(polygon, srid=0))
    session.add(zone)
    await session.commit()
    await session.refresh(zone)
    await reload_analyzer(session, analyzer)
    return ZoneOut(id=zone.id, name=zone.name, polygon=list(polygon.exterior.coords))


@router.delete("/{zone_id}", status_code=204)
async def delete_zone(
    zone_id: int,
    session: AsyncSession = Depends(get_session),
    analyzer: FlowAnalyzer = Depends(get_analyzer),
):
    zone = await session.get(models.Zone, zone_id)
    if zone is not None:
        await session.delete(zone)
        await session.commit()
        await reload_analyzer(session, analyzer)
