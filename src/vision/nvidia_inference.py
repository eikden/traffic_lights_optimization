from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

# Placeholder import for TensorRT/DeepStream bindings.
try:  # pragma: no cover - GPU runtime not available in CI
    import tensorrt as trt  # type: ignore
except Exception:  # pragma: no cover - fallback when TensorRT is absent
    trt = None


@dataclass
class Detection:
    label: str
    confidence: float
    lane_id: str


@dataclass
class NvidiaInferenceEngine:
    engine_path: Path

    def load(self) -> None:
        if trt is None:
            return
        self.runtime = trt.Runtime(trt.Logger(trt.Logger.WARNING))
        with self.engine_path.open("rb") as f:
            self.engine = self.runtime.deserialize_cuda_engine(f.read())

    def infer(self, frames: Iterable[bytes]) -> List[Detection]:
        # In production, map detections to lanes via calibration polygons.
        # Here we return stubbed data so the simulator can run without a GPU.
        return [
            Detection(label="vehicle", confidence=0.9, lane_id="N_S"),
            Detection(label="vehicle", confidence=0.85, lane_id="S_N"),
        ]

    def detections_to_counts(self, detections: List[Detection]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for detection in detections:
            counts[detection.lane_id] = counts.get(detection.lane_id, 0) + 1
        return counts
