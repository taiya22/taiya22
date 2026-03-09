#!/usr/bin/env python3
"""Run Monte Carlo simulation (1,000 trials)."""

import sys
import time

from taiga_sim.monte_carlo import format_monte_carlo_summary, run_monte_carlo


def main():
    n_trials = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

    print(f"モンテカルロ・シミュレーション開始 ({n_trials:,}回試行)...")
    t0 = time.time()
    result = run_monte_carlo(n_trials=n_trials, years=30)
    elapsed = time.time() - t0
    print(f"完了: {elapsed:.1f}秒\n")

    print(format_monte_carlo_summary(result))


if __name__ == "__main__":
    main()
