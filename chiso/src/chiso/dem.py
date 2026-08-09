"""DEM（数値標高モデル）の共通コンテナ。実データ取得・合成デモの双方が生成する。"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np


@dataclass
class DemGrid:
    """規則格子状の標高データ。

    elev[i, j] が (lat0 - i*dlat の緯度帯, lon0 + j*dlon の経度帯) の標高[m]。
    行 i は北から南へ増える（画像座標系）。欠測は np.nan。
    """

    elev: np.ndarray      # shape (nrows, ncols), float32, m
    lat0: float           # 最北端（row=0 の上辺）の緯度
    lon0: float           # 最西端（col=0 の左辺）の経度
    dlat: float           # 1行あたりの緯度差（正の値、南へ進むと緯度は減る）
    dlon: float           # 1列あたりの経度差（正の値）
    source: str           # 由来（"gsi_dem10b" / "synthetic_demo" 等）
    synthetic: bool       # 合成データか

    @property
    def nrows(self) -> int:
        return self.elev.shape[0]

    @property
    def ncols(self) -> int:
        return self.elev.shape[1]

    def cell_center(self, i: int, j: int) -> tuple[float, float]:
        lat = self.lat0 - (i + 0.5) * self.dlat
        lon = self.lon0 + (j + 0.5) * self.dlon
        return lat, lon

    def cell_size_m(self) -> tuple[float, float]:
        """セルの概略の物理サイズ(縦, 横)[m]。傾斜計算に使う。"""
        mid_lat = self.lat0 - self.nrows * self.dlat / 2
        m_per_deg_lat = 111_320.0
        m_per_deg_lon = 111_320.0 * np.cos(np.radians(mid_lat))
        return self.dlat * m_per_deg_lat, self.dlon * m_per_deg_lon

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        meta = {k: v for k, v in asdict(self).items() if k != "elev"}
        np.savez_compressed(
            path,
            elev=self.elev.astype(np.float32),
            **{k: np.array(v) for k, v in meta.items()},
        )

    @classmethod
    def load(cls, path: Path) -> "DemGrid":
        z = np.load(path, allow_pickle=False)
        return cls(
            elev=z["elev"].astype(np.float32),
            lat0=float(z["lat0"]),
            lon0=float(z["lon0"]),
            dlat=float(z["dlat"]),
            dlon=float(z["dlon"]),
            source=str(z["source"]),
            synthetic=bool(z["synthetic"]),
        )
