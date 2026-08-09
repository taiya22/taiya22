"""実在温泉地の「既知の事実」だけを手作業で投入する補助レイヤー（出典明記）。

CHISO.md §3.4 は「出典明記のうえ手動投入可」を認める。ここで投入するのは、
**地形ではない**、公知かつ引用可能な事実に限る:
  - 地質分類（第四紀火山か否か）… ESTIMATE の原料（地域スケールの概略）
  - 温泉の存在（著名な温泉地であること）… ACTUAL の裏づけ（点・事業所）

投入しないもの（精度・誤認の観点から手作業では入れない）:
  - 法規制ポリゴン（LEGAL は「やってよいか」に直結するため、概略の手描きはしない）
  - 河川の詳細形状 / 空き家率・高齢化率などの統計（捏造しない。空のままにする）

地形そのもの（傾斜・起伏・谷底）は GSI DEM から算出する。手作業では触らない。
"""
from __future__ import annotations

from ..config import Prefecture
from .sources import append_source


def _bbox_poly(p: Prefecture):
    return [[
        [p.bbox_min_lon, p.bbox_min_lat], [p.bbox_max_lon, p.bbox_min_lat],
        [p.bbox_max_lon, p.bbox_max_lat], [p.bbox_min_lon, p.bbox_max_lat],
        [p.bbox_min_lon, p.bbox_min_lat],
    ]]


# 温泉地ごとの既知事実。geology_volcanic は産総研シームレス地質図・各温泉の成因に基づく概略。
# onsen は著名な源泉・温泉街の概略座標（公知）。
_KNOWN = {
    "yudanaka": {
        "geology_volcanic": True,   # 志賀高原・横手山など第四紀火山帯のふもと
        "geology_note": "志賀火山群（第四紀火山）のふもと。火山性温泉。",
        "geology_source": "産総研 20万分の1日本シームレス地質図 / 一般に第四紀火山帯",
        "onsen": [
            {"lonlat": [138.410, 36.744], "name": "湯田中温泉"},
            {"lonlat": [138.416, 36.744], "name": "渋温泉"},
            {"lonlat": [138.435, 36.732], "name": "上林温泉"},
        ],
    },
    "hakone": {
        "geology_volcanic": True,   # 箱根火山（カルデラ・中央火口丘）
        "geology_note": "箱根火山（第四紀・活火山）のカルデラ内外。火山性温泉。",
        "geology_source": "産総研 シームレス地質図 / 気象庁 活火山（箱根山）",
        "onsen": [
            {"lonlat": [139.106, 35.232], "name": "箱根湯本温泉"},
            {"lonlat": [139.045, 35.248], "name": "強羅温泉"},
            {"lonlat": [139.015, 35.265], "name": "仙石原温泉"},
            {"lonlat": [139.020, 35.215], "name": "芦之湯温泉"},
        ],
    },
    "arima": {
        "geology_volcanic": False,  # 六甲花崗岩。非火山性の「有馬型温泉」（深部起源）
        "geology_note": "六甲山地の花崗岩体。近傍に第四紀火山なし。非火山性（有馬型）温泉。",
        "geology_source": "産総研 シームレス地質図 / 有馬型深部流体（非火山性温泉）の知見",
        "onsen": [
            {"lonlat": [135.2477, 34.7975], "name": "有馬温泉"},
        ],
    },
}


def has_known(pref_key: str) -> bool:
    return pref_key in _KNOWN


def build_known_aux(pref: Prefecture) -> dict:
    """DEM とは独立に、既知事実だけの aux を返す（引用付き・手動投入）。"""
    k = _KNOWN[pref.key]

    volcanic_polys = [_bbox_poly(pref)] if k["geology_volcanic"] else []

    aux = {
        "synthetic": False,
        "hand_authored": True,
        "pref": pref.key,
        "pref_name_ja": pref.name_ja,
        "notice": (
            "地質分類と温泉の存在のみを引用付きで手動投入。地形は GSI DEM から算出。"
            "法規制・河川・統計は未投入（空）。"
        ),
        "layers": {
            "volcanic_geology": {"kind": "polygons", "polygons": volcanic_polys,
                                 "note": k["geology_note"], "source": k["geology_source"]},
            "onsen_points": {"kind": "points", "points": k["onsen"]},
            "rivers": {"kind": "lines", "lines": []},
            "sediment_disaster_area": {"kind": "polygons", "polygons": []},
            "protected_forest": {"kind": "polygons", "polygons": []},
            "natural_park": {"kind": "polygons", "polygons": []},
            "agri_zone": {"kind": "polygons", "polygons": []},
            "sea": {"kind": "polygons", "polygons": []},
            "ports": {"kind": "points", "points": []},
            "stations": {"kind": "points", "points": []},
            "establishments": {"kind": "muni_counts", "by_industry": {
                # 温泉宿が実在することのみ既知事実として投入。他業種は未投入(0)。
                "onsen_ryokan": {pref.key: 1},
                "fermentation": {pref.key: 0}, "forestry_woodwork": {pref.key: 0},
                "orchard": {pref.key: 0}, "seafood_processing": {pref.key: 0},
                "mountain_tourism": {pref.key: 0},
            }},
        },
        # 統計（空き家率等）は投入しない。捏造しないため None のまま。
        "municipalities": [{
            "id": pref.key, "name": pref.name_ja,
            "polygon": _bbox_poly(pref),
            "stats": {"akiya_rate": None, "aging_rate": None, "estab_change_rate": None},
        }],
    }

    append_source(
        kind="既知事実(地質分類・温泉存在, 手動投入)",
        provider="産総研シームレス地質図 ほか（公知）",
        url="https://gbank.gsj.jp/seamless/",
        license_="出典明記のうえ引用（概略分類）",
        note=f"{pref.name_ja} volcanic={k['geology_volcanic']} / {k['geology_note']}",
    )
    return aux
