from __future__ import annotations

from pathlib import Path
from typing import List, Sequence

import yaml
from pydantic import BaseModel, Field


class PhaseConfig(BaseModel):
    name: str
    lanes: Sequence[str]
    min_green: int = Field(ge=5)
    max_green: int = Field(ge=5)


class CameraConfig(BaseModel):
    id: str
    lanes: Sequence[str]
    model_path: str


class LoopDetectorConfig(BaseModel):
    id: str
    lane: str


class LayoutConfig(BaseModel):
    id: str
    phases: List[PhaseConfig]
    sensors: dict

    @property
    def cameras(self) -> List[CameraConfig]:
        camera_data = self.sensors.get("cameras", [])
        return [CameraConfig(**item) for item in camera_data]

    @property
    def loop_detectors(self) -> List[LoopDetectorConfig]:
        loop_data = self.sensors.get("loop_detectors", [])
        return [LoopDetectorConfig(**item) for item in loop_data]


def load_layout(path: Path | str) -> LayoutConfig:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return LayoutConfig(**raw)
