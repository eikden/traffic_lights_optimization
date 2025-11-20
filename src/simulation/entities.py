from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class LaneState:
    id: str
    queue: int = 0
    pedestrians: int = 0

    def add_vehicle(self, count: int) -> None:
        self.queue = max(0, self.queue + count)

    def clear_with_capacity(self, capacity: int) -> int:
        cleared = min(self.queue, capacity)
        self.queue -= cleared
        return cleared


@dataclass
class PhaseState:
    name: str
    lanes: List[str]
    min_green: int
    max_green: int
    elapsed: int = 0

    def reset(self) -> None:
        self.elapsed = 0

    def tick(self) -> None:
        self.elapsed += 1

    @property
    def can_extend(self) -> bool:
        return self.elapsed < self.max_green

    @property
    def must_extend(self) -> bool:
        return self.elapsed < self.min_green


@dataclass
class IntersectionState:
    layout_id: str
    phases: List[PhaseState]
    lanes: Dict[str, LaneState]
    current_phase_index: int = 0
    time: int = 0
    history: List[dict] = field(default_factory=list)

    @property
    def current_phase(self) -> PhaseState:
        return self.phases[self.current_phase_index]

    def switch_phase(self) -> None:
        self.current_phase_index = (self.current_phase_index + 1) % len(self.phases)
        self.current_phase.reset()

    def tick(self, dt: int = 1) -> None:
        self.time += dt
        self.current_phase.tick()

    def record(self) -> None:
        snapshot = {
            "time": self.time,
            "phase": self.current_phase.name,
            "queues": {lane_id: lane.queue for lane_id, lane in self.lanes.items()},
            "pedestrians": {lane_id: lane.pedestrians for lane_id, lane in self.lanes.items()},
        }
        self.history.append(snapshot)
