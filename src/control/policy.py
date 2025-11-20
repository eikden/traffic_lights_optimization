from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.simulation.entities import IntersectionState
from src.simulation.observation import DetectorObservation


@dataclass
class ActuationDecision:
    switch_phase: bool


class PhaseController(Protocol):
    def decide(self, intersection: IntersectionState, observation: DetectorObservation) -> ActuationDecision:
        ...


@dataclass
class DemandResponsiveController:
    vehicle_threshold: int = 12
    pedestrian_priority: bool = True

    def decide(self, intersection: IntersectionState, observation: DetectorObservation) -> ActuationDecision:
        phase = intersection.current_phase
        total_queue = sum(observation.vehicles[lane] for lane in phase.lanes)
        pedestrian_pressure = sum(observation.pedestrians[lane] for lane in phase.lanes)

        if phase.must_extend:
            return ActuationDecision(switch_phase=False)

        if self.pedestrian_priority and pedestrian_pressure > 0:
            return ActuationDecision(switch_phase=False)

        if total_queue < self.vehicle_threshold and phase.can_extend:
            return ActuationDecision(switch_phase=False)

        return ActuationDecision(switch_phase=True)
