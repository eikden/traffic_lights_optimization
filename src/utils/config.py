from __future__ import annotations

from pathlib import Path
from typing import List, Sequence

try:  # pragma: no cover - optional dependency when loading YAML
    import yaml
except ModuleNotFoundError:  # pragma: no cover - fallback when PyYAML is absent
    yaml = None

try:  # pragma: no cover - optional dependency in constrained environments
    from pydantic import BaseModel, Field
except ModuleNotFoundError:  # pragma: no cover - lightweight stub
    class BaseModel:  # type: ignore
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    def Field(default=None, **_: object):  # type: ignore
        return default


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
    if yaml is None:
        raise ImportError("PyYAML is required to load layout files")
    with file_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return LayoutConfig(**raw)


class NetworkConfig(BaseModel):
    id: str
    intersections: List[LayoutConfig]
    offsets: dict = Field(default_factory=dict)
    corridor_lanes: List[str] = Field(default_factory=list)


def load_network(path: Path | str) -> NetworkConfig:
    file_path = Path(path)
    if yaml is None:
        raise ImportError("PyYAML is required to load network files")
    with file_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    intersections = [LayoutConfig(**item) for item in raw.get("intersections", [])]
    return NetworkConfig(
        id=raw["id"],
        intersections=intersections,
        offsets=raw.get("offsets", {}),
        corridor_lanes=raw.get("corridor_lanes", []),
    )
