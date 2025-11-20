from __future__ import annotations

import random
from typing import Dict, Iterable, List

from src.control.policy import ActuationDecision, PhaseController
from src.simulation.entities import IntersectionState, LaneState, PhaseState
from src.simulation.observation import DetectorObservation
from src.utils.config import LayoutConfig


def build_intersection(layout: LayoutConfig) -> IntersectionState:
    lanes = {lane: LaneState(id=lane) for phase in layout.phases for lane in phase.lanes}
    phases = [
        PhaseState(
            name=phase.name,
            lanes=list(phase.lanes),
            min_green=phase.min_green,
            max_green=phase.max_green,
        )
        for phase in layout.phases
    ]
    return IntersectionState(layout_id=layout.id, phases=phases, lanes=lanes)


def simulate_arrivals(lanes: Iterable[LaneState], intensity: float = 0.7) -> None:
    for lane in lanes:
        arrivals = max(0, int(random.gauss(mu=intensity * 3, sigma=1)))
        lane.add_vehicle(arrivals)


def simulate_pedestrians(lanes: Iterable[LaneState], crossing_rate: float = 0.2) -> None:
    for lane in lanes:
        if random.random() < crossing_rate:
            lane.pedestrians += 1


def capture_observations(intersection: IntersectionState) -> DetectorObservation:
    vehicles = {lane_id: lane.queue for lane_id, lane in intersection.lanes.items()}
    pedestrians = {lane_id: lane.pedestrians for lane_id, lane in intersection.lanes.items()}
    return DetectorObservation(vehicles=vehicles, pedestrians=pedestrians)


def apply_discharge(intersection: IntersectionState, saturation_flow: int = 5) -> Dict[str, int]:
    phase = intersection.current_phase
    discharged: Dict[str, int] = {}
    for lane_id in phase.lanes:
        lane = intersection.lanes[lane_id]
        discharged[lane_id] = lane.clear_with_capacity(saturation_flow)
    for lane in intersection.lanes.values():
        lane.pedestrians = max(0, lane.pedestrians - 1)
    return discharged


def run_simulation(
    layout: LayoutConfig,
    controller: PhaseController,
    steps: int = 120,
    arrival_intensity: float = 0.7,
    crossing_rate: float = 0.2,
) -> IntersectionState:
    intersection = build_intersection(layout)
    for _ in range(steps):
        simulate_arrivals(intersection.lanes.values(), intensity=arrival_intensity)
        simulate_pedestrians(intersection.lanes.values(), crossing_rate=crossing_rate)

        observation = capture_observations(intersection)
        decision: ActuationDecision = controller.decide(intersection, observation)
        if decision.switch_phase:
            intersection.switch_phase()

        apply_discharge(intersection)
        intersection.record()
        intersection.tick()

    return intersection
