"""原則の作り込み（層の分離・断定語の禁止・limitations 必須）の検証。"""
import pytest

from chiso.layers import Layer, assert_no_forbidden_words
from chiso.assess.rules import load_all_rules
from chiso.config import RULES_DIR


def test_forbidden_words_detected():
    with pytest.raises(ValueError):
        assert_no_forbidden_words("この土地は有望です")
    with pytest.raises(ValueError):
        assert_no_forbidden_words("買うべき土地")
    # 通常の説明文は通る
    assert_no_forbidden_words("傾斜と起伏から地形の素地を推定する")


def test_all_rules_load_and_are_layer_pure():
    rules = load_all_rules(RULES_DIR)
    assert len(rules) == 6
    for r in rules:
        assert r.signals and r.corroboration and r.constraints
        for s in r.signals:
            assert s.layer == Layer.ESTIMATE
        for s in r.corroboration:
            assert s.layer == Layer.ACTUAL
        for s in r.constraints:
            assert s.layer == Layer.LEGAL


def test_every_item_has_limitations():
    # 原則3: すべての指標に limitations（空でない）
    for r in load_all_rules(RULES_DIR):
        assert r.limitations
        for s in r.all_items():
            assert s.limitations, f"{r.industry}:{s.id} に limitations が無い"


def test_no_forbidden_words_anywhere_in_rules():
    for r in load_all_rules(RULES_DIR):
        assert_no_forbidden_words(r.description)
        for s in r.all_items():
            assert_no_forbidden_words(s.description)
            for lim in s.limitations:
                assert_no_forbidden_words(lim)


def test_six_expected_industries():
    got = {r.industry for r in load_all_rules(RULES_DIR)}
    assert got == {
        "onsen_ryokan", "fermentation", "forestry_woodwork",
        "orchard", "seafood_processing", "mountain_tourism",
    }
