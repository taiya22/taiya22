"""層（レイヤー）の定義。CHISO.md 原則1「三層を混ぜない」の実装上の要。

すべての指標レコードは必ずいずれかの Layer に属する。
異なる層の値を掛け合わせて単一の数値を作ることは、この設計上できない/してはいけない。
"""
from __future__ import annotations

from enum import Enum


class Layer(str, Enum):
    """指標が属する層。値の混合（合成）は禁止。"""

    ESTIMATE = "ESTIMATE"  # 地形から演繹した仮説。証拠ではない
    ACTUAL = "ACTUAL"      # 実在の証拠（センサス、温泉法登録 等）
    LEGAL = "LEGAL"        # やってよいか（保安林、農地区分、警戒区域 等）
    FIELD = "FIELD"        # 作者が現地で確かめた記録（v0.2）

    @property
    def label_ja(self) -> str:
        return {
            "ESTIMATE": "推定層",
            "ACTUAL": "現況層",
            "LEGAL": "法的層",
            "FIELD": "観測層",
        }[self.value]

    @property
    def description_ja(self) -> str:
        return {
            "ESTIMATE": "地形から演繹した仮説。証拠ではない。",
            "ACTUAL": "実際にそうである証拠。",
            "LEGAL": "やってよいかどうか（法規制）。",
            "FIELD": "作者が現地で確かめた記録。",
        }[self.value]


# 断定語の禁止リスト（CHISO.md 原則3 / 第III部 4）。
# システムが自動生成する出力文言にこれらを含めてはならない。
FORBIDDEN_ASSERTION_WORDS_JA = [
    "有望",
    "買うべき",
    "買う べき",
    "おすすめ",
    "お勧め",
    "オススメ",
    "安全",
    "危険",
    "儲かる",
    "値上がり",
    "投資すべき",
    "最適",
    "ベスト",
    "保証",
]


def assert_no_forbidden_words(text: str) -> None:
    """出力文言に断定語が混入していないか検査する。テスト・生成器から呼ぶ。"""
    hits = [w for w in FORBIDDEN_ASSERTION_WORDS_JA if w in text]
    if hits:
        raise ValueError(
            f"断定語が出力に含まれています（CHISO.md 原則3違反）: {hits} / text={text!r}"
        )
