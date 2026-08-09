"""data/SOURCES.md の台帳追記（F-01）。取得日時・URL・ライセンスを記録する。"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

from ..config import SOURCES_MD

_HEADER = """# データ出典・ライセンス台帳（SOURCES.md）

このファイルは `chiso fetch` が自動追記する。すべて公開データ。
生データそのものはリポジトリに含めない（`.gitignore`）。取得はスクリプトで再現する。

| 取得日時(UTC) | 種別 | 提供元 | URL | ライセンス | 備考 |
|---|---|---|---|---|---|
"""


def append_source(
    kind: str,
    provider: str,
    url: str,
    license_: str,
    note: str = "",
    *,
    now: _dt.datetime | None = None,
) -> None:
    """SOURCES.md に1行追記する。now を渡せば決定論的にできる（テスト用）。"""
    SOURCES_MD.parent.mkdir(parents=True, exist_ok=True)
    if not SOURCES_MD.exists():
        SOURCES_MD.write_text(_HEADER, encoding="utf-8")

    ts = (now or _dt.datetime.now(_dt.timezone.utc)).strftime("%Y-%m-%d %H:%M")
    row = f"| {ts} | {kind} | {provider} | {url} | {license_} | {note} |\n"
    with SOURCES_MD.open("a", encoding="utf-8") as f:
        f.write(row)
