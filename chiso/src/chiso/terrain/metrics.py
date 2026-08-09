"""DEM から地形指標を算出し、1kmメッシュ（3次メッシュ）に集約する（F-02）。

出力する指標はすべて「地形からの計測値」であり、それ自体は ESTIMATE でも
ACTUAL でもない一次量である。適性の推定（ESTIMATE）は assess 側で規則を通して行う。
合成（総合スコア化）は一切しない。乱数を使わない。

限界（limitations）:
  - 傾斜・起伏はDEM解像度に律速される。局所的な段々畑や小規模造成は反映されない。
  - 谷底/尾根判定は TPI（周囲との相対高度）に基づく近似で、地質・水文学的な定義とは異なる。
  - 集水（flow）は簡易 D8 による相対量で、実流量・氾濫を意味しない。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..dem import DemGrid
from ..mesh import mesh3_code, mesh3_center

# 各指標が「地形計測から何を言えないか」。export/viewer で必ず表示する。
TERRAIN_LIMITATIONS: dict[str, list[str]] = {
    "slope_mean_deg": ["DEM解像度に依存。局所的な造成・擁壁・段々畑は表現されない。"],
    "flat_ratio_lt15": ["傾斜15度未満セルの面積割合。連続性（まとまり）は評価していない。"],
    "flat_ratio_lt8": ["傾斜8度未満セルの面積割合。地盤・地耐力は判定できない。"],
    "relief_m": ["メッシュ内の標高最大差。周囲の山体規模は隣接メッシュを含めていない。"],
    "valley_ratio": ["TPIによる谷地形の近似。氾濫域・地下水位は含まない。"],
    "ridge_ratio": ["TPIによる尾根地形の近似。"],
    "south_face_ratio": ["南向き斜面（斜面方位112.5–247.5度かつ傾斜3度以上）の割合。日照時間そのものではない。"],
    "elev_mean_m": ["メッシュ内平均標高。微気候（冷気湖・霧）は表現しない。"],
    "flow_max": ["簡易D8集水量の相対値。実際の流量・水利権・取水可否は判定できない。"],
    "sea_ratio": ["標高0m未満セルの割合（海の近接の代理）。汀線・港湾機能は含まない。"],
}


def _slope_aspect(dem: DemGrid) -> tuple[np.ndarray, np.ndarray]:
    """傾斜[度]と斜面方位[度, 北=0 時計回り]を Horn 法で算出。"""
    z = dem.elev.astype(np.float64)
    dy_m, dx_m = dem.cell_size_m()
    # NaN を近傍平均で仮補間（縁のみ影響、決定論的）
    if np.isnan(z).any():
        zf = np.where(np.isnan(z), np.nanmean(z), z)
    else:
        zf = z
    gy, gx = np.gradient(zf, dy_m, dx_m)  # gy: 南北方向（行増=南）, gx: 東西
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    # 斜面方位: 下り方向。row増が南なので北向き成分は -gy
    aspect = np.degrees(np.arctan2(gx, gy))  # 0=下りが南方向… 正規化して北0基準へ
    aspect = (aspect + 360.0) % 360.0
    return slope.astype(np.float32), aspect.astype(np.float32)


def _tpi(dem: DemGrid, radius: int = 3) -> np.ndarray:
    """Topographic Position Index: セル標高 - 周囲平均。負=谷, 正=尾根。"""
    z = dem.elev.astype(np.float64)
    zf = np.where(np.isnan(z), np.nanmean(z), z)
    k = 2 * radius + 1
    # 箱型平均（積分画像で高速・決定論的）
    pad = np.pad(zf, radius, mode="edge")
    csum = np.cumsum(np.cumsum(pad, axis=0), axis=1)
    csum = np.pad(csum, ((1, 0), (1, 0)), mode="constant")
    r0 = np.arange(zf.shape[0])
    c0 = np.arange(zf.shape[1])
    R0, C0 = np.meshgrid(r0, c0, indexing="ij")
    A = csum[R0, C0]
    B = csum[R0, C0 + k]
    C = csum[R0 + k, C0]
    D = csum[R0 + k, C0 + k]
    box = (D - B - C + A) / (k * k)
    return (zf - box).astype(np.float32)


def _flow_accum(dem: DemGrid) -> np.ndarray:
    """簡易 D8 集水量（相対）。標高降順にセルを処理し最急降下先へ流す。"""
    z = dem.elev.astype(np.float64)
    zf = np.where(np.isnan(z), np.nanmean(z), z)
    nr, nc = zf.shape
    acc = np.ones(zf.shape, dtype=np.float64)
    order = np.argsort(zf.ravel())[::-1]  # 高い順（決定論的）
    neigh = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for idx in order:
        i, j = divmod(int(idx), nc)
        zc = zf[i, j]
        best = None
        best_drop = 0.0
        for di, dj in neigh:
            ni, nj = i + di, j + dj
            if 0 <= ni < nr and 0 <= nj < nc:
                drop = zc - zf[ni, nj]
                if drop > best_drop:
                    best_drop = drop
                    best = (ni, nj)
        if best is not None:
            acc[best] += acc[i, j]
    return acc.astype(np.float32)


def compute_terrain_mesh(dem: DemGrid) -> pd.DataFrame:
    """DEM → 3次メッシュ別の地形指標 DataFrame。"""
    slope, aspect = _slope_aspect(dem)
    tpi = _tpi(dem)
    flow = _flow_accum(dem)
    z = dem.elev

    nr, nc = dem.nrows, dem.ncols
    rr = np.arange(nr)
    cc = np.arange(nc)
    lat = dem.lat0 - (rr + 0.5) * dem.dlat
    lon = dem.lon0 + (cc + 0.5) * dem.dlon
    LON, LAT = np.meshgrid(lon, lat)

    # 各セルのメッシュコード（ベクトルではなく決定論的ループを避けるため一括計算）
    codes = np.empty((nr, nc), dtype=object)
    for i in range(nr):
        for j in range(nc):
            codes[i, j] = mesh3_code(float(LAT[i, j]), float(LON[i, j]))

    south = ((aspect >= 112.5) & (aspect <= 247.5) & (slope >= 3.0))

    df = pd.DataFrame({
        "mesh": codes.ravel(),
        "elev": z.ravel(),
        "slope": slope.ravel(),
        "tpi": tpi.ravel(),
        "flow": flow.ravel(),
        "south": south.ravel().astype(np.float32),
    })

    def _agg(g: pd.DataFrame) -> pd.Series:
        e = g["elev"].to_numpy()
        s = g["slope"].to_numpy()
        t = g["tpi"].to_numpy()
        return pd.Series({
            "n_cells": len(g),
            "elev_mean_m": float(np.nanmean(e)),
            "elev_min_m": float(np.nanmin(e)),
            "elev_max_m": float(np.nanmax(e)),
            "relief_m": float(np.nanmax(e) - np.nanmin(e)),
            "slope_mean_deg": float(np.nanmean(s)),
            "slope_max_deg": float(np.nanmax(s)),
            "flat_ratio_lt15": float(np.mean(s < 15.0)),
            "flat_ratio_lt8": float(np.mean(s < 8.0)),
            "valley_ratio": float(np.mean(t < -15.0)),
            "ridge_ratio": float(np.mean(t > 15.0)),
            "south_face_ratio": float(g["south"].mean()),
            "flow_max": float(np.nanmax(g["flow"].to_numpy())),
            "sea_ratio": float(np.mean(e < 0.0)),
        })

    out = df.groupby("mesh", sort=True).apply(_agg, include_groups=False).reset_index()
    centers = out["mesh"].map(mesh3_center)
    out["center_lat"] = centers.map(lambda x: x[0])
    out["center_lon"] = centers.map(lambda x: x[1])
    out["dem_source"] = dem.source
    out["synthetic"] = dem.synthetic
    return out
