from shapely.geometry import Point, Polygon

XY = tuple[float, float]


def point_in_polygon(point: XY, polygon_coords: list[XY]) -> bool:
    return Polygon(polygon_coords).contains(Point(point))


def line_side(line_coords: tuple[XY, XY], point: XY) -> float:
    """Signed distance-like value: sign indicates which side of the
    directed line (p1 -> p2) the point falls on."""
    (x1, y1), (x2, y2) = line_coords
    px, py = point
    return (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)


def _orientation(a: XY, b: XY, c: XY) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def segments_intersect(p1: XY, p2: XY, q1: XY, q2: XY) -> bool:
    """Standard orientation-based segment intersection test."""
    d1 = _orientation(q1, q2, p1)
    d2 = _orientation(q1, q2, p2)
    d3 = _orientation(p1, p2, q1)
    d4 = _orientation(p1, p2, q2)
    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and (
        (d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)
    ):
        return True
    return False
