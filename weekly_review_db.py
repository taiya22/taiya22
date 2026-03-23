"""Weekly Review Database Manager

振り返りデータをSQLiteに蓄積し、Markdownレポートを生成する。
"""

import sqlite3
import json
from datetime import date, datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "weekly_reviews.db"
REVIEWS_DIR = Path(__file__).parent / "reviews"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS weekly_reviews (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        week_start      TEXT NOT NULL,          -- YYYY-MM-DD (月曜)
        week_end        TEXT NOT NULL,          -- YYYY-MM-DD (日曜)
        created_at      TEXT NOT NULL DEFAULT (datetime('now')),

        -- セクション1: 学びTOP3
        learning_1      TEXT,
        learning_2      TEXT,
        learning_3      TEXT,

        -- セクション2: 仕事の基本チェック (1-5)
        score_horenso       INTEGER,
        score_time_mgmt     INTEGER,
        score_email_chat    INTEGER,
        score_appearance    INTEGER,
        score_listen_first  INTEGER,  -- NULL = N/A

        -- セクション2: 具体的メモ
        note_horenso        TEXT,
        note_time_mgmt      TEXT,
        note_email_chat     TEXT,
        note_appearance     TEXT,
        note_listen_first   TEXT,

        -- セクション3: 人との関わり
        new_people          TEXT,    -- JSON array
        notable_people      TEXT,    -- JSON array of {name, note}
        give_actions        TEXT,    -- JSON array
        ask_for_help        TEXT,    -- JSON array

        -- セクション4: スキル進捗
        skill_bookkeeping   TEXT,
        skill_toeic         TEXT,
        skill_excel         TEXT,
        skill_powerpoint    TEXT,
        skill_financial_mod TEXT,

        -- セクション5: Purpose照合
        purpose_aligned     TEXT,    -- 'yes' / 'partial' / 'no'
        purpose_note        TEXT,
        capm_progress       TEXT,
        hive_progress       TEXT,

        -- セクション6: 弱みチェック
        weakness_trust      TEXT,    -- 人に頼れなかった場面
        weakness_act_first  TEXT,    -- 考える前に動いた場面
        weakness_rigid      TEXT,    -- 堅くなった場面

        -- セクション7: 来週のアクション
        next_action_1       TEXT,
        next_action_2       TEXT,
        next_action_3       TEXT,

        -- セクション8: 一言
        free_comment        TEXT,

        UNIQUE(week_start)
    );

    CREATE TABLE IF NOT EXISTS monthly_scores (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        month       TEXT NOT NULL,   -- YYYY-MM
        created_at  TEXT NOT NULL DEFAULT (datetime('now')),

        -- 月間平均は weekly_reviews から自動算出するが、手動メモ用
        growth_summary  TEXT,
        theme           TEXT,
        actions         TEXT,       -- JSON array

        UNIQUE(month)
    );
    """)
    conn.commit()
    conn.close()


def insert_review(data: dict) -> int:
    """週次レビューをDBに挿入する。dataはカラム名をキーとするdict。"""
    init_db()
    conn = get_connection()

    # JSON化が必要なフィールド
    json_fields = ["new_people", "notable_people", "give_actions", "ask_for_help"]
    for f in json_fields:
        if f in data and isinstance(data[f], (list, dict)):
            data[f] = json.dumps(data[f], ensure_ascii=False)

    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    values = list(data.values())

    cursor = conn.execute(
        f"INSERT OR REPLACE INTO weekly_reviews ({columns}) VALUES ({placeholders})",
        values,
    )
    conn.commit()
    review_id = cursor.lastrowid
    conn.close()
    return review_id


def get_review(week_start: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM weekly_reviews WHERE week_start = ?", (week_start,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_reviews() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM weekly_reviews ORDER BY week_start ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_score_trends() -> list[dict]:
    """基本チェックのスコア推移を取得する。"""
    conn = get_connection()
    rows = conn.execute("""
        SELECT week_start, week_end,
               score_horenso, score_time_mgmt, score_email_chat,
               score_appearance, score_listen_first
        FROM weekly_reviews
        ORDER BY week_start ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def generate_markdown_report(data: dict) -> str:
    """dictからMarkdownレポートを生成する。"""

    def _parse_json(val):
        if val is None:
            return []
        if isinstance(val, str):
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return [val]
        return val

    new_people = _parse_json(data.get("new_people"))
    notable_people = _parse_json(data.get("notable_people"))
    give_actions = _parse_json(data.get("give_actions"))
    ask_for_help = _parse_json(data.get("ask_for_help"))

    def _score_str(val):
        return f"{val}/5" if val is not None else "N/A"

    lines = [
        f"# Weekly Review: {data['week_start']}〜{data['week_end']}",
        "",
        "---",
        "",
        "## 1. 今週の学び TOP3",
        "",
    ]
    for i in range(1, 4):
        v = data.get(f"learning_{i}", "")
        lines.append(f"{i}. {v or '—'}")

    lines += [
        "",
        "---",
        "",
        "## 2. 仕事の基本チェック",
        "",
        "| 項目 | 今週の自己評価 | 具体的な出来事・改善点 |",
        "|------|:---:|------|",
        f"| 報連相 | {_score_str(data.get('score_horenso'))} | {data.get('note_horenso', '') or ''} |",
        f"| 時間管理 | {_score_str(data.get('score_time_mgmt'))} | {data.get('note_time_mgmt', '') or ''} |",
        f"| メール・チャット | {_score_str(data.get('score_email_chat'))} | {data.get('note_email_chat', '') or ''} |",
        f"| 身だしなみ | {_score_str(data.get('score_appearance'))} | {data.get('note_appearance', '') or ''} |",
        f"| 聞いてから動く | {_score_str(data.get('score_listen_first'))} | {data.get('note_listen_first', '') or ''} |",
        "",
        "---",
        "",
        "## 3. 人との関わり",
        "",
        "- **今週新しく話した人：**",
    ]
    for p in new_people:
        lines.append(f"  - {p}")
    if not new_people:
        lines.append("  - —")

    lines.append("- **印象に残った人・面白かった人：**")
    for p in notable_people:
        if isinstance(p, dict):
            lines.append(f"  - {p.get('name', '')} ── {p.get('note', '')}")
        else:
            lines.append(f"  - {p}")
    if not notable_people:
        lines.append("  - —")

    lines.append("- **自分がGiveできたこと：**")
    for g in give_actions:
        lines.append(f"  - {g}")
    if not give_actions:
        lines.append("  - —")

    lines.append("- **誰かに頼れたこと：**")
    for a in ask_for_help:
        lines.append(f"  - {a}")
    if not ask_for_help:
        lines.append("  - —")

    lines += [
        "",
        "---",
        "",
        "## 4. スキル進捗",
        "",
        "| スキル | 今週やったこと |",
        "|--------|---------------|",
        f"| 簿記 | {data.get('skill_bookkeeping', '') or '—'} |",
        f"| TOEIC | {data.get('skill_toeic', '') or '—'} |",
        f"| Excel | {data.get('skill_excel', '') or '—'} |",
        f"| PowerPoint | {data.get('skill_powerpoint', '') or '—'} |",
        f"| 財務モデリング | {data.get('skill_financial_mod', '') or '—'} |",
        "",
        "---",
        "",
        "## 5. Purpose照合",
        "",
        f"- **Purposeに沿っていたか：** {data.get('purpose_aligned', '—')}",
        f"- **メモ：** {data.get('purpose_note', '') or '—'}",
        f"- **CAPM：** {data.get('capm_progress', '') or '—'}",
        f"- **Hive Hokkaido：** {data.get('hive_progress', '') or '—'}",
        "",
        "---",
        "",
        "## 6. 弱みチェック",
        "",
        f"- **人に頼れなかった場面：** {data.get('weakness_trust', '') or 'なし'}",
        f"- **考える前に動いた場面：** {data.get('weakness_act_first', '') or 'なし'}",
        f"- **堅くなった場面：** {data.get('weakness_rigid', '') or 'なし'}",
        "",
        "---",
        "",
        "## 7. 来週の重点アクション",
        "",
    ]
    for i in range(1, 4):
        v = data.get(f"next_action_{i}", "")
        if v:
            lines.append(f"{i}. {v}")

    lines += [
        "",
        "---",
        "",
        "## 8. 一言",
        "",
        data.get("free_comment", "") or "—",
        "",
        "---",
    ]

    return "\n".join(lines)


def save_review_and_report(data: dict) -> tuple[int, Path]:
    """DBに保存し、Markdownレポートも生成・保存する。"""
    review_id = insert_review(data)

    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REVIEWS_DIR / f"{data['week_end']}_weekly_review.md"
    report_content = generate_markdown_report(data)
    report_path.write_text(report_content, encoding="utf-8")

    return review_id, report_path


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
