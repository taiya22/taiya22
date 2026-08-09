"""日本の地域標準メッシュ（JIS X 0410）ユーティリティ。

3次メッシュ（約1km）を主に扱う。
  - 1次メッシュ: 緯度40分 × 経度1度
  - 2次メッシュ: その1/8（緯度5分 × 経度7.5分）
  - 3次メッシュ: 2次の1/10（緯度30秒 × 経度45秒）≒ 1km

乱数は使わない。同じ入力から同じ出力（CHISO.md §6 再現性）。
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# 3次メッシュ1セルの大きさ（度）
DLAT3 = 30.0 / 3600.0     # 30秒
DLON3 = 45.0 / 3600.0     # 45秒


@dataclass(frozen=True)
class BBox:
    """経緯度の矩形（度）。"""

    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float

    def contains(self, lat: float, lon: float) -> bool:
        return (
            self.min_lat <= lat < self.max_lat
            and self.min_lon <= lon < self.max_lon
        )

    @property
    def center(self) -> tuple[float, float]:
        return ((self.min_lat + self.max_lat) / 2.0,
                (self.min_lon + self.max_lon) / 2.0)


def mesh3_code(lat: float, lon: float) -> str:
    """経緯度から3次メッシュコード（8桁）を返す。"""
    lat_min = lat * 60.0
    p = int(lat_min // 40)
    lat_rem = lat_min - p * 40           # 分, 0..40

    u = int(lon) - 100
    lon_rem = lon - int(lon)             # 度, 0..1

    q = int(lat_rem // 5)                # 0..7
    lat_rem2 = lat_rem - q * 5           # 分, 0..5
    v = int(lon_rem // 0.125)            # 0..7
    lon_rem2 = lon_rem - v * 0.125       # 度, 0..0.125

    r = int(lat_rem2 // 0.5)             # 0..9
    w = int(lon_rem2 // 0.0125)          # 0..9

    return f"{p:02d}{u:02d}{q}{v}{r}{w}"


def mesh3_bbox(code: str) -> BBox:
    """3次メッシュコード（8桁）からBBoxを返す。"""
    if len(code) != 8 or not code.isdigit():
        raise ValueError(f"3次メッシュコードは8桁の数字: got {code!r}")
    p = int(code[0:2])
    u = int(code[2:4])
    q = int(code[4])
    v = int(code[5])
    r = int(code[6])
    w = int(code[7])

    lat_min0 = p * 40 + q * 5 + r * 0.5           # 分
    min_lat = lat_min0 / 60.0
    min_lon = 100 + u + v * 0.125 + w * 0.0125    # 度
    return BBox(min_lat, min_lon, min_lat + DLAT3, min_lon + DLON3)


def mesh3_center(code: str) -> tuple[float, float]:
    return mesh3_bbox(code).center


def iter_mesh3_in_bbox(bbox: BBox) -> list[str]:
    """BBox内に中心を持つ3次メッシュコードを列挙（決定的な順序）。"""
    codes: list[str] = []
    # メッシュ格子に沿って走査
    lat = math.floor(bbox.min_lat / DLAT3) * DLAT3
    while lat < bbox.max_lat:
        lon = math.floor(bbox.min_lon / DLON3) * DLON3
        while lon < bbox.max_lon:
            c_lat = lat + DLAT3 / 2
            c_lon = lon + DLON3 / 2
            if bbox.contains(c_lat, c_lon):
                codes.append(mesh3_code(c_lat, c_lon))
            lon += DLON3
        lat += DLAT3
    return sorted(set(codes))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """2点間距離（km）。集水・河川近接などの距離計算に使う。"""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))
