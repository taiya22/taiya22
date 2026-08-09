"""国土地理院（GSI）DEMタイルの取得（実データ）。

GSI は数値標高モデルを XYZ タイルとして公開している（ログイン不要・公開データ）。
  - dem  (z=14): DEM10B 相当（10mメッシュ）
  - dem5a/dem5b (z=15): 5mメッシュ（整備済み地域のみ）
本モジュールは対象 BBox を覆うタイル群を取得し、単一の DemGrid に結合する。

注意: 本実行環境はネットワークポリシーにより GSI へ到達できないことがある。
その場合は `chiso fetch --demo`（合成デモ）を用いる。実装は到達可能環境で機能する。

出典: 国土地理院 標高タイル / 地理院タイル利用規約
  https://maps.gsi.go.jp/development/ichiran.html
  https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html
"""
from __future__ import annotations

import math
import time

import numpy as np
import requests

from ..config import Prefecture
from ..dem import DemGrid
from .sources import append_source

TILE_TXT_URL = "https://cyberjapandata.gsi.go.jp/xyz/{tileset}/{z}/{x}/{y}.txt"
TILE_PX = 256


def _deg2num(lat: float, lon: float, z: int) -> tuple[int, int]:
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    latr = math.radians(lat)
    y = int((1.0 - math.log(math.tan(latr) + 1.0 / math.cos(latr)) / math.pi) / 2.0 * n)
    return x, y


def _num2deg(x: float, y: float, z: int) -> tuple[float, float]:
    n = 2 ** z
    lon = x / n * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lat, lon


def _fetch_tile(tileset: str, z: int, x: int, y: int,
                session: requests.Session, timeout: int = 30) -> np.ndarray:
    """1タイル(256x256)の標高配列を返す。欠測は np.nan。存在しないタイルは全 nan。"""
    url = TILE_TXT_URL.format(tileset=tileset, z=z, x=x, y=y)
    r = session.get(url, timeout=timeout)
    if r.status_code == 404:
        return np.full((TILE_PX, TILE_PX), np.nan, dtype=np.float32)
    r.raise_for_status()
    rows = []
    for line in r.text.strip().splitlines():
        rows.append([np.nan if v == "e" else float(v) for v in line.split(",")])
    arr = np.array(rows, dtype=np.float32)
    if arr.shape != (TILE_PX, TILE_PX):
        raise ValueError(f"想定外のタイル形状 {arr.shape}: {url}")
    return arr


def fetch_dem(pref: Prefecture, tileset: str = "dem", z: int = 14,
              *, max_tiles: int = 4000, polite_delay_s: float = 0.02) -> DemGrid:
    """対象県 BBox を覆う GSI DEM タイルを取得し DemGrid に結合する。"""
    x0, y0 = _deg2num(pref.bbox_max_lat, pref.bbox_min_lon, z)  # 北西
    x1, y1 = _deg2num(pref.bbox_min_lat, pref.bbox_max_lon, z)  # 南東
    xs = range(min(x0, x1), max(x0, x1) + 1)
    ys = range(min(y0, y1), max(y0, y1) + 1)
    ntiles = len(xs) * len(ys)
    if ntiles > max_tiles:
        raise RuntimeError(
            f"取得タイル数 {ntiles} が上限 {max_tiles} を超過。範囲を絞るかズームを下げる。"
        )

    big = np.full((len(ys) * TILE_PX, len(xs) * TILE_PX), np.nan, dtype=np.float32)
    session = requests.Session()
    for iy, ty in enumerate(ys):
        for ix, tx in enumerate(xs):
            tile = _fetch_tile(tileset, z, tx, ty, session)
            big[iy * TILE_PX:(iy + 1) * TILE_PX, ix * TILE_PX:(ix + 1) * TILE_PX] = tile
            if polite_delay_s:
                time.sleep(polite_delay_s)

    # 大格子の地理範囲（タイル境界）
    nw_lat, nw_lon = _num2deg(min(xs), min(ys), z)
    se_lat, se_lon = _num2deg(max(xs) + 1, max(ys) + 1, z)
    nrows, ncols = big.shape
    dlat = (nw_lat - se_lat) / nrows   # Web Mercator を等間隔近似（県スケールで<1%）
    dlon = (se_lon - nw_lon) / ncols

    append_source(
        kind="DEM(地形/推定層の原料)",
        provider="国土地理院",
        url=TILE_TXT_URL.format(tileset=tileset, z=z, x="{x}", y="{y}"),
        license_="地理院タイル利用規約（出典明示で利用可）",
        note=f"{pref.name_ja} / tileset={tileset} z={z} tiles={ntiles}",
    )
    return DemGrid(
        elev=big, lat0=nw_lat, lon0=nw_lon, dlat=dlat, dlon=dlon,
        source=f"gsi_{tileset}_z{z}", synthetic=False,
    )
