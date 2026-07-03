from fastapi import APIRouter, Depends
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import LineString
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..db import get_session
from ..deps import get_analyzer
from ..detection.analyzer import FlowAnalyzer
from ..detection.loader import reload_analyzer
from ..schemas import LineCreate, LineOut

router = APIRouter(prefix="/lines", tags=["lines"])


@router.get("", response_model=list[LineOut])
async def list_lines(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(models.Line))
    lines = []
    for line in result.scalars():
        coords = list(to_shape(line.geom).coords)
        lines.append(
            LineOut(
                id=line.id,
                name=line.name,
                coords=(coords[0], coords[-1]),
                in_direction=line.in_direction,
            )
        )
    return lines


@router.post("", response_model=LineOut)
async def create_line(
    payload: LineCreate,
    session: AsyncSession = Depends(get_session),
    analyzer: FlowAnalyzer = Depends(get_analyzer),
):
    geom = LineString(payload.coords)
    line = models.Line(
        name=payload.name,
        geom=from_shape(geom, srid=0),
        in_direction=payload.in_direction,
    )
    session.add(line)
    await session.commit()
    await session.refresh(line)
    await reload_analyzer(session, analyzer)
    return LineOut(
        id=line.id, name=line.name, coords=payload.coords, in_direction=line.in_direction
    )


@router.delete("/{line_id}", status_code=204)
async def delete_line(
    line_id: int,
    session: AsyncSession = Depends(get_session),
    analyzer: FlowAnalyzer = Depends(get_analyzer),
):
    line = await session.get(models.Line, line_id)
    if line is not None:
        await session.delete(line)
        await session.commit()
        await reload_analyzer(session, analyzer)
