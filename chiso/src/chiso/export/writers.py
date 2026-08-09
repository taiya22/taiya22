"""GeoJSON / CSV / meta 書き出し（F-05）。

原則:
  - 各出力に layer と limitations を含める（原則1・3）。
  - 合成した総合スコアを一切書かない（原則2）。
  - 合成デモは synthetic=true を全物件に明示する（誤認防止 / 判断基準）。
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ..config import OUTPUT_DIR, Prefecture
from ..layers import Layer
from ..mesh import mesh3_bbox
from ..terrain.metrics import TERRAIN_LIMITATIONS
from ..stagnation.metrics import STAGNATION_LIMITATIONS

_TERRAIN_COLS = [
    "elev_mean_m", "elev_min_m", "elev_max_m", "relief_m",
    "slope_mean_deg", "slope_max_deg", "flat_ratio_lt15", "flat_ratio_lt8",
    "valley_ratio", "ridge_ratio", "south_face_ratio", "flow_max", "sea_ratio",
]


def _mesh_polygon(code: str) -> list[list[list[float]]]:
    b = mesh3_bbox(code)
    return [[
        [b.min_lon, b.min_lat], [b.max_lon, b.min_lat],
        [b.max_lon, b.max_lat], [b.min_lon, b.max_lat],
        [b.min_lon, b.min_lat],
    ]]


def _round(v, n=4):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return round(float(v), n)


def write_mesh_geojson(pref: Prefecture, terrain: pd.DataFrame,
                       wide: pd.DataFrame, long_df: pd.DataFrame,
                       out_dir: Path = OUTPUT_DIR) -> Path:
    """メッシュポリゴン + 地形指標 + 業種別サマリ（層別・非合成）。

    ビューアの重みスライダー用に、ESTIMATE層の各条件の合致(matched)を
    メッシュ×業種ごとに埋め込む。ただし他層とは決して混ぜない。
    """
    # 各項目の matched を (mesh, industry, item_kind) 別に収集（層別の説明可能性）
    items_by: dict[tuple, list] = {}
    for _, r in long_df.iterrows():
        items_by.setdefault((r["mesh"], r["industry"], r["item_kind"]), []).append(
            {"id": r["item_id"], "matched": bool(r["matched"]),
             "value": _round(r["value"]), "weight_hint": r["weight_hint"]})

    def _det(mesh, ind, kind):
        return items_by.get((mesh, ind, kind), [])

    wide_by_mesh: dict[str, dict] = {}
    for _, r in wide.iterrows():
        m, ind = r["mesh"], r["industry"]
        wide_by_mesh.setdefault(m, {})[ind] = {
            "name_ja": r["name_ja"],
            # 層ごとに独立。掛け合わせない（原則2）。
            "estimate": {"matched": int(r["est_matched"]), "total": int(r["est_total"]),
                         "signals": _det(m, ind, "signal"),
                         "_note": "ESTIMATE層内の等重み計数。合成スコアではない。"},
            "actual": {"matched": int(r["act_matched"]), "total": int(r["act_total"]),
                       "items": _det(m, ind, "corroboration")},
            "legal": {"hit_count": int(r["legal_hit_count"]),
                      "hit_ids": json.loads(r["legal_hit_ids"]),
                      "items": _det(m, ind, "constraint")},
        }

    features = []
    for _, tr in terrain.iterrows():
        code = tr["mesh"]
        props = {
            "mesh": code,
            "synthetic": bool(tr.get("synthetic", False)),
            "dem_source": tr.get("dem_source", ""),
            "terrain_layer": Layer.ESTIMATE.value + "(原料は一次計測)",
            **{k: _round(tr.get(k)) for k in _TERRAIN_COLS},
            "assess": wide_by_mesh.get(code, {}),
        }
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": _mesh_polygon(code)},
            "properties": props,
        })

    fc = {
        "type": "FeatureCollection",
        "chiso": {"kind": "mesh", "pref": pref.key, "pref_name_ja": pref.name_ja,
                  "synthetic": pref.synthetic},
        "features": features,
    }
    out = out_dir / f"mesh_{pref.key}.geojson"
    out.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    return out


_LAYER_TAGS = {
    "rivers": ("ACTUAL", "河川（合成の可能性あり）"),
    "onsen_points": ("ACTUAL", "温泉（登録の代理）"),
    "volcanic_geology": ("ESTIMATE", "火山地質（推定の原料）"),
    "sediment_disaster_area": ("LEGAL", "土砂災害警戒区域（相当）"),
    "protected_forest": ("LEGAL", "保安林（相当）"),
    "natural_park": ("LEGAL", "自然公園地域（相当）"),
    "agri_zone": ("LEGAL", "農用地区域（相当）"),
    "sea": ("ACTUAL", "海域"),
    "ports": ("ACTUAL", "港湾"),
    "stations": ("ACTUAL", "鉄道駅"),
}


def write_layers_geojson(pref: Prefecture, aux: dict,
                         out_dir: Path = OUTPUT_DIR) -> Path:
    """補助レイヤー（河川・温泉・法規制ポリゴン等）を層タグ付きで出力。"""
    features = []
    layers = aux.get("layers", {})
    synthetic = bool(aux.get("synthetic", False))

    def feat(geom, name, layer, label):
        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {"chiso_layer": layer, "name": name,
                           "label": label, "synthetic": synthetic},
        })

    for name, (layer, label) in _LAYER_TAGS.items():
        lyr = layers.get(name, {})
        kind = lyr.get("kind")
        if kind == "polygons":
            for poly in lyr.get("polygons", []):
                feat({"type": "Polygon", "coordinates": poly}, name, layer, label)
        elif kind == "lines":
            for ln in lyr.get("lines", []):
                feat({"type": "LineString", "coordinates": ln}, name, layer, label)
        elif kind == "points":
            for p in lyr.get("points", []):
                feat({"type": "Point", "coordinates": p["lonlat"]},
                     p.get("name", name), layer, label)

    for m in aux.get("municipalities", []):
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": m["polygon"]},
            "properties": {"chiso_layer": "ACTUAL", "name": m["name"],
                           "label": "市区町村（合成）", "muni_id": m["id"],
                           "stats": m.get("stats", {}), "synthetic": synthetic},
        })

    fc = {"type": "FeatureCollection",
          "chiso": {"kind": "layers", "pref": pref.key, "synthetic": synthetic},
          "features": features}
    out = out_dir / f"layers_{pref.key}.geojson"
    out.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    return out


def write_csvs(pref: Prefecture, terrain: pd.DataFrame, long_df: pd.DataFrame,
               stagnation: pd.DataFrame, out_dir: Path = OUTPUT_DIR) -> list[Path]:
    paths = []
    p = out_dir / f"terrain_{pref.key}.csv"
    terrain.to_csv(p, index=False)
    paths.append(p)
    p = out_dir / f"assessment_{pref.key}.csv"  # long form: layer と limitations を含む
    long_df.to_csv(p, index=False)
    paths.append(p)
    p = out_dir / f"stagnation_{pref.key}.csv"
    stagnation.to_csv(p, index=False)
    paths.append(p)
    return paths


def write_meta(pref: Prefecture, rules, out_dir: Path = OUTPUT_DIR) -> Path:
    """ビューア用メタ: 層凡例・限界辞書・業種一覧・SYNTHETIC 明示。"""
    def _items(items):
        return [{"id": s.id, "layer": s.layer.value, "source": s.source,
                 "description": s.description, "weight_hint": s.weight_hint,
                 "limitations": s.limitations} for s in items]

    industries = [{"industry": r.industry, "name_ja": r.name_ja,
                   "description": r.description, "limitations": r.limitations,
                   "estimate_signals": _items(r.signals),
                   "actual_items": _items(r.corroboration),
                   "legal_items": _items(r.constraints)}
                  for r in rules]
    meta = {
        "pref": pref.key, "pref_name_ja": pref.name_ja,
        "synthetic": pref.synthetic,
        "synthetic_notice": (
            "この成果物は合成（架空）データです。実在の土地・地形・統計を表しません。"
            if pref.synthetic else ""
        ),
        "layers": [
            {"key": l.value, "label_ja": l.label_ja, "desc": l.description_ja}
            for l in (Layer.ESTIMATE, Layer.ACTUAL, Layer.LEGAL)
        ],
        "principles": [
            "三層(ESTIMATE/ACTUAL/LEGAL)を混ぜない。合成した総合スコアは持たない。",
            "各指標に limitations を併記する。推奨や優劣を示す断定的な語は出力しない。",
        ],
        "terrain_limitations": TERRAIN_LIMITATIONS,
        "stagnation_limitations": STAGNATION_LIMITATIONS,
        "industries": industries,
    }
    out = out_dir / f"meta_{pref.key}.json"
    out.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
