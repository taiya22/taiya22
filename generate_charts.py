#!/usr/bin/env python3
"""Generate line charts for Taiga Capital Group simulation results."""

import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# Run simulation and collect data
from taiga_sim.engines.simulation_runner import SimulationRunner
from taiga_sim.models.simulation import SimulationConfig

config = SimulationConfig()
runner = SimulationRunner(config=config, seed=42)
reports = runner.run(years=30)

years = [r.year for r in reports]
revenue = [r.revenue / 1_0000_0000 for r in reports]  # 億円
ebitda = [r.ebitda / 1_0000_0000 for r in reports]
ev = [r.enterprise_value / 1_0000_0000 for r in reports]
fcf_data = [r.fcf / 1_0000_0000 for r in reports]
headcount = [r.headcount for r in reports]
num_companies = [r.num_companies for r in reports]
moic = [r.seed_investor_moic for r in reports]
founder_pct = [r.founder_ownership_pct * 100 for r in reports]

# Target values from requirements (億円)
target_years = [0, 1, 3, 5, 7, 10, 15, 20, 25, 30]
target_revenue = [0, 10, 30, 70, 200, 1000, 2000, 5000, 12000, 30000]
target_ebitda = [0, 1.5, 5, 20, 50, 150, 400, 1000, 2500, 6000]
target_ev = [50, 6, 25, 120, 350, 1200, 3600, 10000, 25000, 60000]

plt.rcParams.update({
    "font.size": 11,
    "figure.facecolor": "white",
    "axes.grid": True,
    "grid.alpha": 0.3,
})

fig, axes = plt.subplots(3, 2, figsize=(16, 18))
fig.suptitle("Taiga Capital Group - 30-Year Simulation vs Targets", fontsize=16, fontweight="bold", y=0.98)

# 1. Revenue
ax = axes[0, 0]
ax.plot(years, revenue, "b-o", markersize=3, linewidth=2, label="Simulation")
ax.plot(target_years, target_revenue, "r--^", markersize=5, linewidth=1.5, label="Target", alpha=0.8)
ax.set_title("Revenue (Oku JPY)", fontweight="bold")
ax.set_xlabel("Year")
ax.set_ylabel("Oku JPY")
ax.legend()
ax.set_yscale("log")
ax.set_ylim(bottom=1)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

# 2. EBITDA
ax = axes[0, 1]
ax.plot(years, ebitda, "g-o", markersize=3, linewidth=2, label="Simulation")
ax.plot(target_years, target_ebitda, "r--^", markersize=5, linewidth=1.5, label="Target", alpha=0.8)
ax.set_title("EBITDA (Oku JPY)", fontweight="bold")
ax.set_xlabel("Year")
ax.set_ylabel("Oku JPY")
ax.legend()
ax.set_yscale("log")
ax.set_ylim(bottom=1)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

# 3. Enterprise Value
ax = axes[1, 0]
ax.plot(years, ev, "purple", marker="o", markersize=3, linewidth=2, label="Simulation")
ax.plot(target_years, target_ev, "r--^", markersize=5, linewidth=1.5, label="Target", alpha=0.8)
ax.set_title("Enterprise Value (Oku JPY)", fontweight="bold")
ax.set_xlabel("Year")
ax.set_ylabel("Oku JPY")
ax.legend()
ax.set_yscale("log")
ax.set_ylim(bottom=1)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

# 4. Number of Companies + Headcount
ax = axes[1, 1]
ax2 = ax.twinx()
p1 = ax.bar(years, num_companies, color="steelblue", alpha=0.6, label="Companies")
p2, = ax2.plot(years, headcount, "orange", marker="o", markersize=3, linewidth=2, label="Headcount")
ax.set_title("Portfolio & Headcount", fontweight="bold")
ax.set_xlabel("Year")
ax.set_ylabel("Number of Companies", color="steelblue")
ax2.set_ylabel("Headcount", color="orange")
lines = [p1, p2]
labels = [l.get_label() for l in lines]
ax.legend(lines, labels, loc="upper left")

# 5. Seed Investor MOIC
ax = axes[2, 0]
ax.plot(years, moic, "darkgreen", marker="o", markersize=3, linewidth=2)
ax.set_title("Seed Investor MOIC", fontweight="bold")
ax.set_xlabel("Year")
ax.set_ylabel("MOIC (x)")
ax.axhline(y=10, color="gray", linestyle="--", alpha=0.5, label="10x")
ax.axhline(y=100, color="gray", linestyle=":", alpha=0.5, label="100x")
ax.legend()

# 6. Founder Ownership %
ax = axes[2, 1]
ax.plot(years, founder_pct, "darkred", marker="o", markersize=3, linewidth=2)
ax.fill_between(years, founder_pct, alpha=0.15, color="red")
ax.axhline(y=33.4, color="orange", linestyle="--", alpha=0.7, label="Veto Power (33.4%)")
ax.axhline(y=50, color="green", linestyle="--", alpha=0.7, label="Majority (50%)")
ax.set_title("Founder Ownership %", fontweight="bold")
ax.set_xlabel("Year")
ax.set_ylabel("%")
ax.set_ylim(0, 100)
ax.legend()

# Add phase annotations
phase_boundaries = [(0, "P0"), (1, "P1"), (4, "P2"), (7, "P3"), (11, "P4"), (16, "P5"), (21, "P6")]
for ax_row in axes:
    for ax in ax_row:
        for yr, label in phase_boundaries:
            ax.axvline(x=yr, color="gray", linestyle=":", alpha=0.2)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig("/home/user/taiya22/data/simulation_charts.png", dpi=150, bbox_inches="tight")
print("Chart saved to data/simulation_charts.png")
