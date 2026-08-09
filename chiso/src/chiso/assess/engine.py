"""ルール評価エンジン（F-03）。

メッシュ×業種×項目ごとに、層を保ったまま独立に評価する。
**異なる層の値を掛け合わせて単一の数値を作らない（原則1・2）。**
within-ESTIMATE の合致数（est_matched/est_total）は「推定層の内側で条件に幾つ合致したか」
という等重みの計数であり、他層（ACTUAL/LEGAL）とは決して混ぜない。合成スコアではない。
"""
from __future__ import annotations

import json
import operator

import pandas as pd

from ..geometry import (
    dist_point_to_line_km, dist_point_to_point_km,
    point_in_polygon,
)
from ..layers import Layer
from .rules import IndustryRule, Signal

_OPS = {">=": operator.ge, "<=": operator.le, ">": operator.gt,
        "<": operator.lt, "==": operator.eq}


class World:
    """terrain df と aux をまとめ、幾何・統計の参照を提供する。"""

    def __init__(self, terrain: pd.DataFrame, aux: dict):
        self.terrain = terrain.set_index("mesh", drop=False)
        self.aux = aux
        self.layers = aux.get("layers", {})
        self.munis = aux.get("municipalities", [])

    # --- 幾何アクセサ ---
    def polygons(self, name: str):
        lyr = self.layers.get(name, {})
        return lyr.get("polygons", [])  # list[Polygon]

    def lines(self, name: str):
        return self.layers.get(name, {}).get("lines", [])

    def points(self, name: str):
        return [p["lonlat"] for p in self.layers.get(name, {}).get("points", [])]

    def establishment_count(self, industry: str, muni_id: str | None) -> int:
        by = self.layers.get("establishments", {}).get("by_industry", {})
        if muni_id is None:
            return 0
        return int(by.get(industry, {}).get(muni_id, 0))

    def municipality_of(self, lon: float, lat: float):
        for m in self.munis:
            if point_in_polygon((lon, lat), m["polygon"]):
                return m
        return None


def _eval_check(sig: Signal, world: World, mesh_row: pd.Series,
                lon: float, lat: float, industry: str,
                muni_id: str | None) -> tuple[bool, float | None]:
    c = sig.check
    t = c["type"]
    pt = (lon, lat)

    if t == "metric":
        val = mesh_row.get(c["metric"])
        if val is None or pd.isna(val):
            return False, None
        return bool(_OPS[c["op"]](float(val), float(c["value"]))), float(val)

    if t == "line_within_km":
        lines = world.lines(c["source"])
        if not lines:
            return False, None
        d = min(dist_point_to_line_km(pt, ln) for ln in lines)
        return d <= float(c["km"]), d

    if t == "point_within_km":
        pts = world.points(c["source"])
        if not pts:
            return False, None
        d = min(dist_point_to_point_km(pt, p) for p in pts)
        return d <= float(c["km"]), d

    if t == "in_polygon":
        polys = world.polygons(c["source"])
        hit = any(point_in_polygon(pt, poly) for poly in polys)
        return hit, 1.0 if hit else 0.0

    if t == "polygon_within_km":
        polys = world.polygons(c["source"])
        if not polys:
            return False, None
        if any(point_in_polygon(pt, poly) for poly in polys):
            return True, 0.0
        d = min(dist_point_to_line_km(pt, ring) for poly in polys for ring in poly)
        return d <= float(c["km"]), d

    if t == "establishment_count":
        cnt = world.establishment_count(c.get("industry", industry), muni_id)
        return bool(_OPS[c["op"]](cnt, float(c["value"]))), float(cnt)

    raise ValueError(f"未知の check.type: {t}")


def assess(world: World, rules: list[IndustryRule]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(long, wide) の2表を返す。合成スコアは含まない。"""
    long_rows: list[dict] = []
    wide_rows: list[dict] = []

    kind_of = {}
    for r in rules:
        for s in r.signals:
            kind_of[(r.industry, s.id)] = "signal"
        for s in r.corroboration:
            kind_of[(r.industry, s.id)] = "corroboration"
        for s in r.constraints:
            kind_of[(r.industry, s.id)] = "constraint"

    for mesh, mesh_row in world.terrain.iterrows():
        lat = float(mesh_row["center_lat"])
        lon = float(mesh_row["center_lon"])
        muni = world.municipality_of(lon, lat)
        muni_id = muni["id"] if muni else None
        muni_name = muni["name"] if muni else ""

        for rule in rules:
            est_m = est_t = act_m = act_t = 0
            legal_hits: list[str] = []

            for sig in rule.all_items():
                matched, value = _eval_check(
                    sig, world, mesh_row, lon, lat, rule.industry, muni_id)
                long_rows.append({
                    "mesh": mesh, "center_lat": lat, "center_lon": lon,
                    "industry": rule.industry, "name_ja": rule.name_ja,
                    "item_kind": kind_of[(rule.industry, sig.id)],
                    "layer": sig.layer.value, "item_id": sig.id,
                    "source": sig.source, "description": sig.description,
                    "matched": bool(matched),
                    "value": value,
                    "weight_hint": sig.weight_hint,
                    "limitations": json.dumps(sig.limitations, ensure_ascii=False),
                    "muni_id": muni_id or "", "muni_name": muni_name,
                })
                if sig.layer == Layer.ESTIMATE:
                    est_t += 1
                    est_m += int(matched)
                elif sig.layer == Layer.ACTUAL:
                    act_t += 1
                    act_m += int(matched)
                elif sig.layer == Layer.LEGAL and matched:
                    legal_hits.append(sig.id)

            wide_rows.append({
                "mesh": mesh, "center_lat": lat, "center_lon": lon,
                "muni_id": muni_id or "", "muni_name": muni_name,
                "industry": rule.industry, "name_ja": rule.name_ja,
                # 以下は層ごとに独立。決して掛け合わせない（原則2）。
                "est_matched": est_m, "est_total": est_t,     # ESTIMATE層内の等重み計数
                "act_matched": act_m, "act_total": act_t,     # ACTUAL層の裏づけ数
                "legal_hit_count": len(legal_hits),           # LEGAL層で触れた制約数
                "legal_hit_ids": json.dumps(legal_hits, ensure_ascii=False),
            })

    long_df = pd.DataFrame(long_rows)
    wide_df = pd.DataFrame(wide_rows)
    return long_df, wide_df
