#!/usr/bin/env python3
"""Run the Taiga Capital Group 30-year simulation."""

from taiga_sim.engines.simulation_runner import SimulationRunner
from taiga_sim.models.simulation import SimulationConfig


def main():
    # Default configuration (all parameters from requirements doc)
    config = SimulationConfig()

    # Run simulation
    runner = SimulationRunner(config=config, seed=42)
    runner.run(years=30)

    # Print summary
    print(runner.print_summary())

    # Export to JSON
    output_path = runner.export_results("data/simulation_results.json")
    print(f"\n結果をエクスポートしました: {output_path}")


if __name__ == "__main__":
    main()
