"""最小限の幾何ユーティリティ（依存を軽くするため自前実装）。

座標は (lon, lat) 順（GeoJSON 準拠）。距離は近似。geopandas 不使用でも動く。
"""
from __future__ import annotations

import math

Point = tuple[float, float]        # (lon, lat)
Ring = list[Point]
Polygon = list[Ring]               # [outer, hole1, ...]
LineString = list[Point]


def point_in_ring(pt: Point, ring: Ring) -> bool:
    x, y = pt
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi
        ):
            inside = not inside
        j = i
    return inside


def point_in_polygon(pt: Point, poly: Polygon) -> bool:
    if not poly or not point_in_ring(pt, poly[0]):
        return False
    for hole in poly[1:]:
        if point_in_ring(pt, hole):
            return False
    return True


def _m_per_deg(lat: float) -> tuple[float, float]:
    return 111_320.0, 111_320.0 * math.cos(math.radians(lat))


def dist_point_to_segment_km(pt: Point, a: Point, b: Point) -> float:
    """点と線分の最短距離[km]（局所平面近似）。"""
    lat = pt[1]
    my, mx = _m_per_deg(lat)
    px, py = (pt[0]) * mx, (pt[1]) * my
    ax, ay = a[0] * mx, a[1] * my
    bx, by = b[0] * mx, b[1] * my
    dx, dy = bx - ax, by - ay
    seg2 = dx * dx + dy * dy
    if seg2 == 0:
        d = math.hypot(px - ax, py - ay)
    else:
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / seg2))
        cx, cy = ax + t * dx, ay + t * dy
        d = math.hypot(px - cx, py - cy)
    return d / 1000.0


def dist_point_to_line_km(pt: Point, line: LineString) -> float:
    if len(line) < 2:
        if not line:
            return math.inf
        my, mx = _m_per_deg(pt[1])
        return math.hypot((pt[0] - line[0][0]) * mx, (pt[1] - line[0][1]) * my) / 1000.0
    return min(dist_point_to_segment_km(pt, line[i], line[i + 1])
              for i in range(len(line) - 1))


def dist_point_to_point_km(a: Point, b: Point) -> float:
    my, mx = _m_per_deg((a[1] + b[1]) / 2)
    return math.hypot((a[0] - b[0]) * mx, (a[1] - b[1]) * my) / 1000.0
