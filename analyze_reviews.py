"""Weekly Review Analyzer

蓄積された振り返りデータからトレンド分析・サマリーを生成する。
"""

import json
from pathlib import Path
from weekly_review_db import get_all_reviews, get_score_trends, get_connection

REPORTS_DIR = Path(__file__).parent / "data"

SCORE_FIELDS = [
    ("score_horenso", "報連相"),
    ("score_time_mgmt", "時間管理"),
    ("score_email_chat", "メール・チャット"),
    ("score_appearance", "身だしなみ"),
    ("score_listen_first", "聞いてから動く"),
]


def compute_score_summary(reviews: list[dict]) -> dict:
    """各スコアの推移・平均・トレンドを計算する。"""
    summary = {}
    for field, label in SCORE_FIELDS:
        scores = [
            (r["week_start"], r[field])
            for r in reviews
            if r.get(field) is not None
        ]
        if not scores:
            summary[label] = {"data": [], "avg": None, "trend": "—"}
            continue

        values = [s[1] for s in scores]
        avg = sum(values) / len(values)

        if len(values) >= 2:
            recent = values[-1]
            previous = values[-2]
            if recent > previous:
                trend = "↑"
            elif recent < previous:
                trend = "↓"
            else:
                trend = "→"
        else:
            trend = "—"

        summary[label] = {
            "data": scores,
            "avg": round(avg, 1),
            "trend": trend,
        }
    return summary


def count_new_people(reviews: list[dict]) -> list[tuple[str, int]]:
    """週ごとの新しく会った人数を集計する。"""
    result = []
    for r in reviews:
        raw = r.get("new_people")
        if raw is None:
            result.append((r["week_start"], 0))
            continue
        if isinstance(raw, str):
            try:
                people = json.loads(raw)
            except json.JSONDecodeError:
                people = [raw] if raw.strip() else []
        else:
            people = raw
        result.append((r["week_start"], len(people)))
    return result


def count_give_actions(reviews: list[dict]) -> list[tuple[str, int]]:
    """週ごとのGiveアクション数を集計する。"""
    result = []
    for r in reviews:
        raw = r.get("give_actions")
        if raw is None:
            result.append((r["week_start"], 0))
            continue
        if isinstance(raw, str):
            try:
                actions = json.loads(raw)
            except json.JSONDecodeError:
                actions = [raw] if raw.strip() else []
        else:
            actions = raw
        result.append((r["week_start"], len(actions)))
    return result


def weakness_frequency(reviews: list[dict]) -> dict:
    """弱みが顔を出した回数を集計する。"""
    fields = [
        ("weakness_trust", "人に頼れなかった"),
        ("weakness_act_first", "考える前に動いた"),
        ("weakness_rigid", "堅くなった"),
    ]
    counts = {}
    for field, label in fields:
        count = sum(
            1
            for r in reviews
            if r.get(field) and r[field].strip() and r[field].strip() != "なし"
        )
        counts[label] = count
    return counts


def purpose_alignment_ratio(reviews: list[dict]) -> dict:
    """Purpose照合の比率を算出する。"""
    total = len(reviews)
    if total == 0:
        return {"yes": 0, "partial": 0, "no": 0}
    counts = {"yes": 0, "partial": 0, "no": 0}
    for r in reviews:
        val = r.get("purpose_aligned", "")
        if val in counts:
            counts[val] += 1
    return {k: round(v / total * 100, 1) for k, v in counts.items()}


def generate_trend_report(reviews: list[dict]) -> str:
    """蓄積データからトレンド分析レポート（Markdown）を生成する。"""
    if not reviews:
        return "# トレンド分析\n\nデータがありません。週次レビューを蓄積してください。\n"

    lines = [
        "# 振り返りトレンド分析",
        "",
        f"> 対象期間: {reviews[0]['week_start']} 〜 {reviews[-1]['week_end']}（{len(reviews)}週分）",
        "",
        "---",
        "",
        "## 1. 仕事の基本チェック：スコア推移",
        "",
        "| 項目 |",
    ]

    # Build score table header
    score_summary = compute_score_summary(reviews)
    week_labels = [r["week_start"] for r in reviews]

    header = "| 項目 | " + " | ".join([w[5:] for w in week_labels]) + " | 平均 | 傾向 |"
    sep = "|------|" + "|".join(["---:"] * len(week_labels)) + "|---:|---:|"
    lines = lines[:-2]  # remove placeholder
    lines += [header, sep]

    for field, label in SCORE_FIELDS:
        row = f"| {label} |"
        for r in reviews:
            val = r.get(field)
            row += f" {val if val is not None else '—'} |"
        s = score_summary[label]
        row += f" {s['avg'] if s['avg'] else '—'} | {s['trend']} |"
        lines.append(row)

    # People & Give
    lines += [
        "",
        "---",
        "",
        "## 2. 人との関わり",
        "",
        "| 週 | 新しく会った人数 | Giveアクション数 |",
        "|------|---:|---:|",
    ]
    people_counts = count_new_people(reviews)
    give_counts = count_give_actions(reviews)
    for (week, pc), (_, gc) in zip(people_counts, give_counts):
        lines.append(f"| {week} | {pc} | {gc} |")

    total_people = sum(c for _, c in people_counts)
    total_give = sum(c for _, c in give_counts)
    lines.append(f"| **合計** | **{total_people}** | **{total_give}** |")

    # Purpose alignment
    lines += [
        "",
        "---",
        "",
        "## 3. Purpose照合",
        "",
    ]
    pa = purpose_alignment_ratio(reviews)
    lines.append(f"- Yes: {pa['yes']}% / 部分的: {pa['partial']}% / No: {pa['no']}%")

    # Weakness frequency
    lines += [
        "",
        "---",
        "",
        "## 4. 弱みの出現頻度",
        "",
        "| 弱み | 出現回数 | 出現率 |",
        "|------|---:|---:|",
    ]
    wf = weakness_frequency(reviews)
    for label, count in wf.items():
        rate = round(count / len(reviews) * 100, 1)
        lines.append(f"| {label} | {count}/{len(reviews)}週 | {rate}% |")

    # Learnings collection
    lines += [
        "",
        "---",
        "",
        "## 5. 学びアーカイブ",
        "",
    ]
    for r in reviews:
        lines.append(f"### {r['week_start']}〜{r['week_end']}")
        for i in range(1, 4):
            v = r.get(f"learning_{i}", "")
            if v:
                lines.append(f"- {v}")
        lines.append("")

    # Free comments
    lines += [
        "---",
        "",
        "## 6. 一言アーカイブ",
        "",
    ]
    for r in reviews:
        comment = r.get("free_comment", "")
        if comment:
            lines.append(f"- **{r['week_start']}:** {comment}")

    lines.append("")
    return "\n".join(lines)


def run_analysis():
    """分析を実行してレポートを保存する。"""
    reviews = get_all_reviews()
    report = generate_trend_report(reviews)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / "review_trend_analysis.md"
    output_path.write_text(report, encoding="utf-8")
    print(f"Trend analysis saved to {output_path}")
    print(f"Total reviews in DB: {len(reviews)}")
    return output_path


if __name__ == "__main__":
    run_analysis()
