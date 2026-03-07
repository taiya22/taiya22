"""Formatting utilities for Japanese currency and display."""

from __future__ import annotations


def fmt_jpy(value: float) -> str:
    """Format a value in JPY to proper Japanese units (億円 / 兆円).

    Rules:
    - >= 1兆 (1e12): display as 兆円
    - >= 1億 (1e8):  display as 億円
    - >= 1万 (1e4):  display as 万円
    - else:          display as 円
    """
    abs_val = abs(value)
    sign = "-" if value < 0 else ""

    if abs_val >= 1_0000_0000_0000:  # 1兆
        cho = abs_val / 1_0000_0000_0000
        if cho >= 100:
            return f"{sign}{cho:,.0f}兆円"
        return f"{sign}{cho:,.1f}兆円"
    elif abs_val >= 1_0000_0000:  # 1億
        oku = abs_val / 1_0000_0000
        if oku >= 1000:
            return f"{sign}{oku:,.0f}億円"
        return f"{sign}{oku:,.1f}億円"
    elif abs_val >= 1_0000:
        return f"{sign}{abs_val / 1_0000:,.0f}万円"
    else:
        return f"{sign}{abs_val:,.0f}円"


def fmt_table(value: float) -> str:
    """Compact format for summary table (兆/億 with no 円)."""
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    if abs_val >= 1_0000_0000_0000:
        return f"{sign}{abs_val / 1_0000_0000_0000:.1f}兆"
    elif abs_val >= 1_0000_0000:
        return f"{sign}{abs_val / 1_0000_0000:.0f}億"
    else:
        return f"{sign}{abs_val / 1_0000:,.0f}万"


def to_pct(value: float, decimals: int = 1) -> str:
    """Format a ratio as percentage."""
    return f"{value * 100:.{decimals}f}%"


def format_signal(signal: str) -> str:
    """Format traffic light signal with color indicator."""
    symbols = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
    return symbols.get(signal, "⚪")
