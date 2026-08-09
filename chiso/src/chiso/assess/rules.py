"""産業適性ルール（YAML）の読み込みと検証（CHISO.md §4 / 原則5 説明可能性）。

規則はコードから分離され `rules/*.yaml` にある。人が書き、直すのにコードを触らない。
各項目は必ず layer を持ち、ESTIMATE/ACTUAL/LEGAL のいずれかに属す（原則1）。
各 signal/corroboration/constraint は limitations を持つことを必須とする（原則3）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..config import RULES_DIR
from ..layers import Layer, assert_no_forbidden_words

VALID_CHECK_TYPES = {
    "metric", "line_within_km", "point_within_km",
    "in_polygon", "polygon_within_km", "establishment_count",
}


@dataclass
class Signal:
    id: str
    layer: Layer
    source: str
    description: str
    check: dict
    weight_hint: str = "mid"
    limitations: list[str] = field(default_factory=list)


@dataclass
class IndustryRule:
    industry: str
    name_ja: str
    description: str
    signals: list[Signal]          # ESTIMATE
    corroboration: list[Signal]    # ACTUAL
    constraints: list[Signal]      # LEGAL
    limitations: list[str]         # 業種全体

    def all_items(self) -> list[Signal]:
        return [*self.signals, *self.corroboration, *self.constraints]


def _parse_signal(d: dict, default_layer: Layer, ctx: str) -> Signal:
    layer = Layer(d.get("layer", default_layer.value))
    check = d.get("check")
    if not isinstance(check, dict) or check.get("type") not in VALID_CHECK_TYPES:
        raise ValueError(f"{ctx}: check.type が不正です: {check!r} (許可: {VALID_CHECK_TYPES})")
    limitations = d.get("limitations") or []
    if not limitations:
        # 原則3: limitations を空にしない
        raise ValueError(f"{ctx}: limitations が空です（CHISO.md 原則3違反）。id={d.get('id')}")
    desc = d.get("description") or d.get("meaning") or ""
    assert_no_forbidden_words(desc)
    for lim in limitations:
        assert_no_forbidden_words(str(lim))
    return Signal(
        id=d["id"], layer=layer, source=d["source"], description=desc,
        check=check, weight_hint=d.get("weight_hint", "mid"),
        limitations=[str(x) for x in limitations],
    )


def load_rule(path: Path) -> IndustryRule:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    ctx = path.name
    signals = [_parse_signal(s, Layer.ESTIMATE, f"{ctx}:signals")
               for s in data.get("signals", [])]
    corr = [_parse_signal(s, Layer.ACTUAL, f"{ctx}:corroboration")
            for s in data.get("corroboration", [])]
    cons = [_parse_signal(s, Layer.LEGAL, f"{ctx}:constraints")
            for s in data.get("constraints", [])]

    # 層の取り違え検査（原則1）
    for s in signals:
        if s.layer != Layer.ESTIMATE:
            raise ValueError(f"{ctx}: signals は ESTIMATE のみ: {s.id}={s.layer}")
    for s in corr:
        if s.layer != Layer.ACTUAL:
            raise ValueError(f"{ctx}: corroboration は ACTUAL のみ: {s.id}={s.layer}")
    for s in cons:
        if s.layer != Layer.LEGAL:
            raise ValueError(f"{ctx}: constraints は LEGAL のみ: {s.id}={s.layer}")

    lims = data.get("limitations") or []
    if not lims:
        raise ValueError(f"{ctx}: 業種の limitations が空です（原則3違反）")
    assert_no_forbidden_words(data.get("description", ""))
    return IndustryRule(
        industry=data["industry"], name_ja=data["name_ja"],
        description=data.get("description", ""),
        signals=signals, corroboration=corr, constraints=cons,
        limitations=[str(x) for x in lims],
    )


def load_all_rules(rules_dir: Path = RULES_DIR) -> list[IndustryRule]:
    paths = sorted(rules_dir.glob("*.yaml"))
    if not paths:
        raise FileNotFoundError(f"ルールが見つかりません: {rules_dir}")
    return [load_rule(p) for p in paths]
