"""詰まり指標（F-04）。市区町村単位で、空き家率・高齢化率・事業所減少率を
**並べたまま**保持する。合成して単一の「詰まり度」を作らない（原則2）。

これらは現況の統計（ACTUAL）に属するが、承継難・停滞の「代理指標」であって、
特定事業が畳むべき/蘇るという断定には使わない（原則4）。
"""
from __future__ import annotations

import pandas as pd

STAGNATION_LIMITATIONS: dict[str, list[str]] = {
    "akiya_rate": [
        "空き家率は住宅・土地統計調査に基づく市区町村単位の値。個々の物件の状態・取引可否は示さない。",
        "別荘・賃貸募集中を含む定義もあり、放置空き家とは一致しない。",
    ],
    "aging_rate": [
        "高齢化率は承継難の代理指標にすぎない。個別事業の後継者有無は分からない。",
    ],
    "estab_change_rate": [
        "事業所数の増減率は業種を問わない集計で、特定業種の盛衰は表さない。",
        "開業・廃業の別、移転による増減は区別していない。",
    ],
}


def compute_stagnation(aux: dict) -> pd.DataFrame:
    """municipalities の stats から詰まり指標表を作る（並置・非合成）。"""
    rows = []
    for m in aux.get("municipalities", []):
        s = m.get("stats", {})
        rows.append({
            "muni_id": m["id"],
            "muni_name": m["name"],
            "layer": "ACTUAL",
            "akiya_rate": s.get("akiya_rate"),
            "aging_rate": s.get("aging_rate"),
            "estab_change_rate": s.get("estab_change_rate"),
            "synthetic": bool(aux.get("synthetic", False)),
        })
    return pd.DataFrame(rows)
