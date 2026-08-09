"""地形指標算出の健全性と決定性の検証。"""
import numpy as np

from chiso.config import get_prefecture
from chiso.fetch.demo import build_demo_dem
from chiso.terrain.metrics import compute_terrain_mesh


def _demo_terrain():
    dem = build_demo_dem(get_prefecture("demo"))
    return dem, compute_terrain_mesh(dem)


def test_terrain_columns_and_ranges():
    _, df = _demo_terrain()
    for col in ["slope_mean_deg", "relief_m", "flat_ratio_lt15",
                "valley_ratio", "south_face_ratio", "sea_ratio",
                "center_lat", "center_lon", "synthetic"]:
        assert col in df.columns
    assert (df["slope_mean_deg"] >= 0).all()
    assert df["flat_ratio_lt15"].between(0, 1).all()
    assert df["valley_ratio"].between(0, 1).all()
    assert bool(df["synthetic"].iloc[0]) is True


def test_terrain_is_deterministic():
    # 同じ入力から同じ出力（CHISO.md §6 再現性・乱数不使用）
    _, a = _demo_terrain()
    _, b = _demo_terrain()
    cols = ["slope_mean_deg", "relief_m", "valley_ratio", "sea_ratio"]
    assert np.allclose(a[cols].to_numpy(), b[cols].to_numpy())


def test_demo_world_has_sea_and_mountains():
    _, df = _demo_terrain()
    # 東の海（標高<0）と、西の起伏の両方が生成されている
    assert (df["sea_ratio"] > 0).any()
    assert (df["relief_m"] > 150).any()
