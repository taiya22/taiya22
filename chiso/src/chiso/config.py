"""パス・対象県の設定。乱数・環境依存を排し再現性を保つ。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# リポジトリ内の chiso/ 直下を基準にする
PACKAGE_ROOT = Path(__file__).resolve().parents[2]  # .../chiso

RULES_DIR = PACKAGE_ROOT / "rules"
DATA_DIR = PACKAGE_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
DERIVED_DIR = DATA_DIR / "derived"
OUTPUT_DIR = PACKAGE_ROOT / "output"
VIEWER_DIR = PACKAGE_ROOT / "viewer"
SOURCES_MD = DATA_DIR / "SOURCES.md"


@dataclass(frozen=True)
class Prefecture:
    """対象県の定義。bbox は概略の外接矩形（デモ・取得範囲の指定に使う）。"""

    key: str          # ファイル名等に使う英字キー
    name_ja: str
    jis_code: str     # 都道府県コード（e-Stat 等で使用）
    bbox_min_lat: float
    bbox_min_lon: float
    bbox_max_lat: float
    bbox_max_lon: float
    synthetic: bool = False  # True の場合、地形が合成データであることを示す


# CHISO.md §1.1 の初期候補。加えて、ネットワーク非依存で
# パイプライン全体を再現するための合成デモ県を用意する。
PREFECTURES: dict[str, Prefecture] = {
    "nagano": Prefecture(
        key="nagano", name_ja="長野県", jis_code="20",
        bbox_min_lat=35.20, bbox_min_lon=137.33,
        bbox_max_lat=37.03, bbox_max_lon=138.75,
    ),
    "oita": Prefecture(
        key="oita", name_ja="大分県", jis_code="44",
        bbox_min_lat=32.71, bbox_min_lon=130.80,
        bbox_max_lat=33.74, bbox_max_lon=132.07,
    ),
    "yamagata": Prefecture(
        key="yamagata", name_ja="山形県", jis_code="06",
        bbox_min_lat=37.73, bbox_min_lon=139.52,
        bbox_max_lat=39.22, bbox_max_lon=140.65,
    ),
    # --- 温泉地スケールの実在地域（§10「既知の温泉地と規則を照合」用） ---
    # 温泉街スケールの小さな bbox に絞ることで DEM タイル取得を軽量・高速にする。
    # 実行には GSI（国土地理院）標高タイルへのネットワーク到達が必要。
    "yudanaka": Prefecture(
        key="yudanaka", name_ja="湯田中・渋温泉郷（長野県山ノ内町）", jis_code="20",
        bbox_min_lat=36.70, bbox_min_lon=138.38,
        bbox_max_lat=36.80, bbox_max_lon=138.49,
    ),
    "hakone": Prefecture(
        key="hakone", name_ja="箱根温泉郷（神奈川県箱根町）", jis_code="14",
        bbox_min_lat=35.17, bbox_min_lon=138.98,
        bbox_max_lat=35.29, bbox_max_lon=139.14,
    ),
    "arima": Prefecture(
        key="arima", name_ja="有馬温泉（兵庫県神戸市北区）", jis_code="28",
        bbox_min_lat=34.76, bbox_min_lon=135.21,
        bbox_max_lat=34.83, bbox_max_lon=135.29,
    ),
    # 合成デモ県: ネットワーク不要で end-to-end に走らせるための架空の土地。
    # 地形・統計はすべて決定論的に生成した合成値であり、実在しない。
    "demo": Prefecture(
        key="demo", name_ja="デモ県（合成・実在しない）", jis_code="00",
        # 小さな範囲（約 0.22° 四方 ≒ 20km）に限定して高速に走らせる
        bbox_min_lat=36.60, bbox_min_lon=138.30,
        bbox_max_lat=36.82, bbox_max_lon=138.55,
        synthetic=True,
    ),
}

# 「長野」の解釈: 箱根・有馬と並ぶ温泉地として、志賀高原ふもとの
# 湯田中・渋温泉郷（山ノ内町）を採った。長野市や長野県全域を指す場合は
# key を変えて bbox を差し替えればよい。


def get_prefecture(key: str) -> Prefecture:
    if key not in PREFECTURES:
        raise KeyError(
            f"未知の県キー: {key!r}. 選択肢: {', '.join(PREFECTURES)}"
        )
    return PREFECTURES[key]


def ensure_dirs() -> None:
    for d in (RAW_DIR, DERIVED_DIR, OUTPUT_DIR):
        d.mkdir(parents=True, exist_ok=True)
