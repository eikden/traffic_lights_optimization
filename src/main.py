from __future__ import annotations

import argparse
from pathlib import Path

from src.control.policy import DemandResponsiveController
from src.simulation.simulator import run_simulation
from src.utils.config import load_layout


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Traffic light optimization simulator")
    parser.add_argument("--layout", type=Path, required=True, help="Path to intersection layout YAML")
    parser.add_argument("--steps", type=int, default=120, help="Number of simulation steps")
    parser.add_argument("--arrival_intensity", type=float, default=0.7, help="Traffic arrival intensity")
    parser.add_argument("--crossing_rate", type=float, default=0.2, help="Pedestrian crossing rate")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    layout = load_layout(args.layout)
    controller = DemandResponsiveController()

    intersection = run_simulation(
        layout=layout,
        controller=controller,
        steps=args.steps,
        arrival_intensity=args.arrival_intensity,
        crossing_rate=args.crossing_rate,
    )

    print(f"Simulation complete for {layout.id} after {intersection.time} seconds")
    print(f"Final phase: {intersection.current_phase.name}")
    avg_queue = sum(lane.queue for lane in intersection.lanes.values()) / len(intersection.lanes)
    print(f"Average queue length: {avg_queue:.2f} vehicles")


if __name__ == "__main__":
    main()
