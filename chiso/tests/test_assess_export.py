"""assess→export の end-to-end 検証。受け入れ基準3・4・5を機械的に確かめる。"""
import json

import pytest

from chiso.config import get_prefecture
from chiso.fetch.demo import generate_demo
from chiso.terrain.metrics import compute_terrain_mesh
from chiso.dem import DemGrid
from chiso.assess.rules import load_all_rules
from chiso.assess.engine import World, assess
from chiso.export import writers
from chiso.layers import FORBIDDEN_ASSERTION_WORDS_JA


@pytest.fixture(scope="module")
def pipeline(tmp_path_factory):
    pref = get_prefecture("demo")
    dem, aux = generate_demo(pref)
    # generate_demo が data/raw に書くが、DEM はメモリのものを使う
    terrain = compute_terrain_mesh(dem)
    rules = load_all_rules()
    world = World(terrain, aux)
    long_df, wide_df = assess(world, rules)
    out = tmp_path_factory.mktemp("out")
    g1 = writers.write_mesh_geojson(pref, terrain, wide_df, long_df, out_dir=out)
    g2 = writers.write_layers_geojson(pref, aux, out_dir=out)
    from chiso.stagnation.metrics import compute_stagnation
    stag = compute_stagnation(aux)
    csvs = writers.write_csvs(pref, terrain, long_df, stag, out_dir=out)
    meta = writers.write_meta(pref, rules, out_dir=out)
    return dict(pref=pref, terrain=terrain, long=long_df, wide=wide_df,
               mesh_geojson=g1, layers_geojson=g2, csvs=csvs, meta=meta, out=out)


def test_layers_are_only_the_three_valid(pipeline):
    layers = set(pipeline["long"]["layer"].unique())
    assert layers <= {"ESTIMATE", "ACTUAL", "LEGAL"}


def test_no_composite_score_columns(pipeline):
    # 受け入れ基準3: 合成された総合スコアが存在しない。
    # wide 表は層ごとに独立した列のみを持ち、掛け合わせた列を持たない。
    cols = set(pipeline["wide"].columns)
    forbidden_like = {"score", "total_score", "overall", "rank", "ranking", "composite"}
    assert not (cols & forbidden_like)
    # est/act/legal は別列として並存する（混ざっていない）
    for c in ["est_matched", "act_matched", "legal_hit_count"]:
        assert c in cols


def test_geojson_has_layer_and_limitations_and_synthetic(pipeline):
    fc = json.loads(pipeline["mesh_geojson"].read_text(encoding="utf-8"))
    assert fc["chiso"]["synthetic"] is True
    f = fc["features"][0]["properties"]
    assert "assess" in f
    a = next(iter(f["assess"].values()))
    # 三層が別々のキーとして存在する
    assert set(a) >= {"estimate", "actual", "legal"}
    # meta に limitations 辞書がある
    meta = json.loads(pipeline["meta"].read_text(encoding="utf-8"))
    assert meta["terrain_limitations"]
    for ind in meta["industries"]:
        assert ind["limitations"]
        for s in ind["estimate_signals"]:
            assert s["limitations"]


def test_no_forbidden_words_in_any_output(pipeline):
    # 受け入れ基準5: 断定語が出力に含まれない。
    texts = []
    texts.append(pipeline["mesh_geojson"].read_text(encoding="utf-8"))
    texts.append(pipeline["layers_geojson"].read_text(encoding="utf-8"))
    texts.append(pipeline["meta"].read_text(encoding="utf-8"))
    for c in pipeline["csvs"]:
        texts.append(c.read_text(encoding="utf-8"))
    blob = "\n".join(texts)
    for w in FORBIDDEN_ASSERTION_WORDS_JA:
        assert w not in blob, f"断定語 {w!r} が出力に含まれている"


def test_assessment_csv_carries_layer_and_limitations(pipeline):
    csv = next(p for p in pipeline["csvs"] if p.name.startswith("assessment_"))
    head = csv.read_text(encoding="utf-8").splitlines()[0]
    assert "layer" in head and "limitations" in head


def test_onsen_estimate_differentiates_space(pipeline):
    # 受け入れ基準7の前提: 場所ごとに推定が異なり、選べること。
    w = pipeline["wide"]
    onsen = w[w["industry"] == "onsen_ryokan"]
    assert onsen["est_matched"].nunique() > 1
    # ACTUAL(温泉近接/宿泊業)の裏づけがある区域が存在する
    assert (onsen["act_matched"] > 0).any()
