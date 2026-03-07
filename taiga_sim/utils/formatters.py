"""Formatting utilities for Japanese currency and display."""

from __future__ import annotations


def to_oku(value: float) -> str:
    """Format a value in JPY to 億円 display."""
    oku = value / 1_0000_0000
    if abs(oku) >= 10000:
        return f"{oku / 10000:,.1f}兆円"
    elif abs(oku) >= 1:
        return f"{oku:,.1f}億円"
    elif abs(value) >= 10000:
        return f"{value / 10000:,.0f}万円"
    else:
        return f"{value:,.0f}円"


def to_pct(value: float, decimals: int = 1) -> str:
    """Format a ratio as percentage."""
    return f"{value * 100:.{decimals}f}%"


def format_signal(signal: str) -> str:
    """Format traffic light signal with color indicator."""
    symbols = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
    return symbols.get(signal, "⚪")
