from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List

from src.simulation.entities import IntersectionState


def synthesize_frames(intersections: Iterable[IntersectionState]) -> List[Dict]:
    frames: List[Dict] = []
    for intersection in intersections:
        for sample in intersection.history:
            frames.append(
                {
                    "time": sample["time"],
                    "intersection": intersection.layout_id,
                    "phase": sample["phase"],
                    "queues": sample["queues"],
                    "pedestrians": sample["pedestrians"],
                }
            )
    return sorted(frames, key=lambda f: (f["time"], f["intersection"]))


def export_omniverse_synthetic_data(
    intersections: Iterable[IntersectionState],
    output_path: Path,
    metadata: Dict | None = None,
) -> Path:
    """Prepare synthetic sensor traces for Omniverse digital twins."""

    frames = synthesize_frames(intersections)
    payload = {
        "metadata": metadata or {"simulator": "traffic_lights_optimization", "unit": "seconds"},
        "frames": frames,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return output_path
