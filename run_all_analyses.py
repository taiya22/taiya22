#!/usr/bin/env python3
"""Run all 3 analyses: saves charts to data/ directory.

Reuses base trial data for path anatomy and risk metrics.
Sensitivity analysis runs its own varied configs.
"""

import subprocess
import sys
import time


def run(script: str, n: int):
    print(f"\n{'='*60}")
    print(f"Running: {script} {n}")
    print(f"{'='*60}")
    t0 = time.time()
    result = subprocess.run(
        [sys.executable, script, str(n)],
        cwd="/home/user/taiya22",
    )
    elapsed = time.time() - t0
    print(f"Finished {script} in {elapsed:.0f}s (exit={result.returncode})")
    return result.returncode


def main():
    # Path anatomy and risk metrics: 100 trials each (~8 min each)
    run("generate_path_anatomy.py", 100)
    run("generate_risk_metrics.py", 100)
    # Sensitivity: 20 trials per config (~30 min)
    run("generate_sensitivity.py", 20)


if __name__ == "__main__":
    main()
