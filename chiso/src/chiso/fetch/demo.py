"""合成デモ世界の生成（ネットワーク非依存・完全に決定論的）。

目的: GSI 等の外部データに到達できない環境でも、パイプライン全体
（terrain → assess → stagnation → export → viewer）を end-to-end で走らせ、
CHISO.md の受け入れ基準を検証できるようにする。

重要: ここで生成される地形・河川・温泉・法規制・統計はすべて**合成値**であり、
実在の土地を一切表さない。県名は「デモ県（合成・実在しない）」とし、
出力・ビューアには SYNTHETIC の明示を必ず付す（CHISO.md 迷ったときの判断基準）。

乱数は使わない。座標と決定論的な関数（正弦・指数）だけで生成する。
"""
from __future__ import annotations

import json

import numpy as np

from ..config import Prefecture, RAW_DIR
from ..dem import DemGrid
from .sources import append_source

# デモDEMの解像度（度）。1kmメッシュ内に約12x12セルが入るよう設定。
_DEMO_DLAT = (30.0 / 3600.0) / 12.0   # ≒ 77m
_DEMO_DLON = (45.0 / 3600.0) / 12.0


def _dist_to_polyline(U: np.ndarray, V: np.ndarray, verts: list[tuple[float, float]]) -> np.ndarray:
    """パラメータ空間(u,v)での点群と折れ線の最短距離（ベクトル化）。"""
    best = np.full(U.shape, np.inf)
    for (u0, v0), (u1, v1) in zip(verts[:-1], verts[1:]):
        du, dv = u1 - u0, v1 - v0
        seg2 = du * du + dv * dv or 1e-12
        t = ((U - u0) * du + (V - v0) * dv) / seg2
        t = np.clip(t, 0.0, 1.0)
        cx, cy = u0 + t * du, v0 + t * dv
        best = np.minimum(best, np.hypot(U - cx, V - cy))
    return best


# パラメータ空間で定義する主要地物（u:西→東 0..1, v:南→北 0..1）
_VOLCANO = (0.30, 0.72)
_MAIN_RIVER = [(0.58, 1.0), (0.55, 0.7), (0.52, 0.45), (0.60, 0.20), (0.70, 0.0)]
_TRIB_RIVER = [(0.30, 0.72), (0.40, 0.58), (0.50, 0.47), (0.545, 0.45)]  # 火山麓→本流
_COAST_U = 0.85  # これより東は海


def _elevation_field(U: np.ndarray, V: np.ndarray) -> np.ndarray:
    """合成標高場[m]。決定論的。"""
    E = 1400.0 * (1.0 - U)                       # 西高東低
    E += 250.0 * np.sin(2 * np.pi * 2.5 * V)     # 南北うねり（斜面方位を生む）
    E += 200.0 * np.sin(2 * np.pi * 2.0 * U + 1.0)

    # 火山（円錐＋火口）
    r = np.hypot((U - _VOLCANO[0]) * 1.0, (V - _VOLCANO[1]) * 0.9)
    E += 750.0 * np.exp(-(r / 0.10) ** 2)
    E -= 200.0 * np.exp(-(r / 0.03) ** 2)

    # 本流・支流の谷（谷底平野・扇状地・平坦地を生む）
    dm = _dist_to_polyline(U, V, _MAIN_RIVER)
    dt = _dist_to_polyline(U, V, _TRIB_RIVER)
    E -= 380.0 * np.exp(-(dm / 0.045) ** 2)
    E -= 240.0 * np.exp(-(dt / 0.030) ** 2)

    # 東の海（u>coast で海面下へ）
    sea = np.clip(U - _COAST_U, 0.0, None)
    E -= 1600.0 * sea
    return E.astype(np.float32)


def _uv_to_lonlat(pref: Prefecture, u: float, v: float) -> tuple[float, float]:
    lon = pref.bbox_min_lon + u * (pref.bbox_max_lon - pref.bbox_min_lon)
    lat = pref.bbox_min_lat + v * (pref.bbox_max_lat - pref.bbox_min_lat)
    return lon, lat


def _line(pref, verts):
    return [list(_uv_to_lonlat(pref, u, v)) for (u, v) in verts]


def _circle_poly(pref, cu, cv, ru, rv, n=48):
    ring = []
    for k in range(n + 1):
        a = 2 * np.pi * k / n
        ring.append(list(_uv_to_lonlat(pref, cu + ru * np.cos(a), cv + rv * np.sin(a))))
    return [ring]


def _rect_poly(pref, u0, v0, u1, v1):
    pts = [(u0, v0), (u1, v0), (u1, v1), (u0, v1), (u0, v0)]
    return [[list(_uv_to_lonlat(pref, u, v)) for (u, v) in pts]]


def build_demo_dem(pref: Prefecture) -> DemGrid:
    lat_span = pref.bbox_max_lat - pref.bbox_min_lat
    lon_span = pref.bbox_max_lon - pref.bbox_min_lon
    nrows = int(round(lat_span / _DEMO_DLAT))
    ncols = int(round(lon_span / _DEMO_DLON))

    # row=0 が北端。v は南→北なので row 0 → v=1
    rows = np.arange(nrows)
    cols = np.arange(ncols)
    lat = pref.bbox_max_lat - (rows + 0.5) * _DEMO_DLAT
    lon = pref.bbox_min_lon + (cols + 0.5) * _DEMO_DLON
    LON, LAT = np.meshgrid(lon, lat)
    U = (LON - pref.bbox_min_lon) / lon_span
    V = (LAT - pref.bbox_min_lat) / lat_span
    elev = _elevation_field(U, V)

    append_source(
        kind="DEM(合成デモ・実在しない)",
        provider="CHISO synthetic generator",
        url="(local, deterministic)",
        license_="N/A (合成データ)",
        note=f"{pref.name_ja} grid={nrows}x{ncols} SYNTHETIC",
    )
    return DemGrid(
        elev=elev, lat0=pref.bbox_max_lat, lon0=pref.bbox_min_lon,
        dlat=_DEMO_DLAT, dlon=_DEMO_DLON,
        source="synthetic_demo", synthetic=True,
    )


def build_demo_aux(pref: Prefecture) -> dict:
    """河川・温泉・地質・法規制・接続・統計の合成レイヤー一式。"""
    munis = [
        {
            "id": "W", "name": "山あい町（合成）",
            "polygon": _rect_poly(pref, 0.0, 0.0, 0.34, 1.0),
            "stats": {"akiya_rate": 0.28, "aging_rate": 0.46, "estab_change_rate": -0.22},
        },
        {
            "id": "C", "name": "谷あい市（合成）",
            "polygon": _rect_poly(pref, 0.34, 0.0, 0.66, 1.0),
            "stats": {"akiya_rate": 0.17, "aging_rate": 0.34, "estab_change_rate": -0.08},
        },
        {
            "id": "E", "name": "海べ町（合成）",
            "polygon": _rect_poly(pref, 0.66, 0.0, 1.0, 1.0),
            "stats": {"akiya_rate": 0.21, "aging_rate": 0.39, "estab_change_rate": -0.15},
        },
    ]

    establishments = {
        # ACTUAL: 合成の事業所数（現況層の裏づけ用）
        "onsen_ryokan":        {"W": 6, "C": 2, "E": 0},
        "fermentation":        {"W": 1, "C": 3, "E": 1},
        "forestry_woodwork":   {"W": 5, "C": 2, "E": 0},
        "orchard":             {"W": 2, "C": 4, "E": 1},
        "seafood_processing":  {"W": 0, "C": 0, "E": 4},
        "mountain_tourism":    {"W": 3, "C": 1, "E": 0},
    }

    aux = {
        "synthetic": True,
        "pref": pref.key,
        "pref_name_ja": pref.name_ja,
        "layers": {
            "volcanic_geology": {"kind": "polygons",
                                 "polygons": [_circle_poly(pref, *_VOLCANO, 0.11, 0.10)]},
            "rivers": {"kind": "lines",
                       "lines": [_line(pref, _MAIN_RIVER), _line(pref, _TRIB_RIVER)]},
            "onsen_points": {"kind": "points", "points": [
                {"lonlat": list(_uv_to_lonlat(pref, 0.36, 0.66)), "name": "合成温泉A"},
                {"lonlat": list(_uv_to_lonlat(pref, 0.42, 0.60)), "name": "合成温泉B"},
                {"lonlat": list(_uv_to_lonlat(pref, 0.33, 0.75)), "name": "合成温泉C"},
            ]},
            "sediment_disaster_area": {"kind": "polygons", "polygons": [
                _circle_poly(pref, 0.34, 0.70, 0.06, 0.06),
                _circle_poly(pref, 0.55, 0.30, 0.05, 0.07),
            ]},
            "protected_forest": {"kind": "polygons",
                                 "polygons": [_rect_poly(pref, 0.0, 0.40, 0.33, 1.0)]},
            "natural_park": {"kind": "polygons",
                             "polygons": [_circle_poly(pref, *_VOLCANO, 0.18, 0.17)]},
            "agri_zone": {"kind": "polygons",
                          "polygons": [_rect_poly(pref, 0.45, 0.30, 0.66, 0.75)]},
            "sea": {"kind": "polygons",
                    "polygons": [_rect_poly(pref, _COAST_U, 0.0, 1.0, 1.0)]},
            "ports": {"kind": "points", "points": [
                {"lonlat": list(_uv_to_lonlat(pref, 0.88, 0.10)), "name": "合成港"}]},
            "stations": {"kind": "points", "points": [
                {"lonlat": list(_uv_to_lonlat(pref, 0.50, 0.45)), "name": "合成中央駅"},
                {"lonlat": list(_uv_to_lonlat(pref, 0.20, 0.60)), "name": "合成山駅"}]},
            "establishments": {"kind": "muni_counts", "by_industry": establishments},
        },
        "municipalities": munis,
    }
    return aux


def generate_demo(pref: Prefecture) -> tuple[DemGrid, dict]:
    dem = build_demo_dem(pref)
    aux = build_demo_aux(pref)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dem.save(RAW_DIR / f"dem_{pref.key}.npz")
    (RAW_DIR / f"aux_{pref.key}.json").write_text(
        json.dumps(aux, ensure_ascii=False, indent=2), encoding="utf-8")
    append_source(
        kind="補助レイヤー(合成デモ)", provider="CHISO synthetic generator",
        url="(local, deterministic)", license_="N/A (合成データ)",
        note=f"{pref.name_ja} rivers/onsen/geology/legal/stats SYNTHETIC",
    )
    return dem, aux
