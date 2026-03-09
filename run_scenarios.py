#!/usr/bin/env python3
"""Run Bear / Base / Bull scenario analysis."""

from taiga_sim.scenario_analysis import (
    format_comparison_table,
    format_yearly_comparison,
    run_scenarios,
)


def main():
    print("シナリオ分析を実行中...")
    results = run_scenarios(years=30, seed=42)

    print(format_comparison_table(results))
    print(format_yearly_comparison(results, metric="ev"))
    print(format_yearly_comparison(results, metric="revenue"))


if __name__ == "__main__":
    main()
