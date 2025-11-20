from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping

from src.control.policy import ActuationDecision, DemandResponsiveController
from src.simulation.entities import IntersectionState
from src.simulation.observation import DetectorObservation
from src.simulation.simulator import (
    apply_discharge,
    build_intersection,
    capture_observations,
    simulate_arrivals,
    simulate_pedestrians,
)
from src.utils.config import LayoutConfig


@dataclass
class TrafficNetwork:
    intersections: Dict[str, IntersectionState]
    offsets: Dict[str, int]
    time: int = 0
    history: List[dict] = field(default_factory=list)

    def record(self) -> None:
        snapshot = {
            "time": self.time,
            "intersections": {
                inter_id: {
                    "phase": inter.current_phase.name,
                    "queues": {lane: lane_state.queue for lane, lane_state in inter.lanes.items()},
                }
                for inter_id, inter in self.intersections.items()
            },
        }
        self.history.append(snapshot)


def build_network(layouts: Iterable[LayoutConfig], offsets: Mapping[str, int] | None = None) -> TrafficNetwork:
    intersections = {layout.id: build_intersection(layout) for layout in layouts}
    offset_map = {layout.id: 0 for layout in layouts}
    if offsets:
        offset_map.update(offsets)
    return TrafficNetwork(intersections=intersections, offsets=offset_map)


class CoordinatedSignalManager:
    """Synchronize multiple intersections to favor a corridor green-wave."""

    def __init__(
        self,
        corridor_lanes: Iterable[str],
        cycle_length: int = 90,
        green_band: int = 30,
    ) -> None:
        self.corridor_lanes = set(corridor_lanes)
        self.cycle_length = cycle_length
        self.green_band = green_band
        self.local_controllers: Dict[str, DemandResponsiveController] = {}

    def _corridor_phase(self, intersection: IntersectionState) -> str | None:
        for phase in intersection.phases:
            if any(lane in self.corridor_lanes for lane in phase.lanes):
                return phase.name
        return None

    def _within_green_band(self, network_time: int, offset: int) -> bool:
        return ((network_time + offset) % self.cycle_length) < self.green_band

    def sync_and_decide(
        self,
        network: TrafficNetwork,
        observations: Mapping[str, DetectorObservation],
    ) -> Dict[str, ActuationDecision]:
        corridor_pressure = sum(
            obs.vehicles.get(lane, 0)
            for obs in observations.values()
            for lane in self.corridor_lanes
        )
        cross_pressure = sum(
            count
            for obs in observations.values()
            for lane, count in obs.vehicles.items()
            if lane not in self.corridor_lanes
        )

        prioritize_corridor = corridor_pressure >= cross_pressure
        decisions: Dict[str, ActuationDecision] = {}

        for inter_id, intersection in network.intersections.items():
            obs = observations[inter_id]
            controller = self.local_controllers.setdefault(inter_id, DemandResponsiveController())
            target_phase = self._corridor_phase(intersection)

            if prioritize_corridor and target_phase:
                if self._within_green_band(network.time, network.offsets.get(inter_id, 0)):
                    if intersection.current_phase.name != target_phase:
                        intersection.set_phase(target_phase)
                    decisions[inter_id] = ActuationDecision(switch_phase=False)
                    continue

            decisions[inter_id] = controller.decide(intersection, obs)

        return decisions


def run_network_simulation(
    layouts: Iterable[LayoutConfig],
    coordinator: CoordinatedSignalManager,
    steps: int = 240,
    arrival_intensity: float = 0.8,
    crossing_rate: float = 0.15,
    offsets: Mapping[str, int] | None = None,
) -> TrafficNetwork:
    network = build_network(layouts, offsets=offsets)

    for _ in range(steps):
        for intersection in network.intersections.values():
            simulate_arrivals(intersection.lanes.values(), intensity=arrival_intensity)
            simulate_pedestrians(intersection.lanes.values(), crossing_rate=crossing_rate)

        observations = {
            inter_id: capture_observations(intersection)
            for inter_id, intersection in network.intersections.items()
        }

        decisions = coordinator.sync_and_decide(network, observations)
        for inter_id, decision in decisions.items():
            if decision.switch_phase:
                network.intersections[inter_id].switch_phase()

        for intersection in network.intersections.values():
            apply_discharge(intersection)
            intersection.record()
            intersection.tick()

        network.record()
        network.time += 1

    return network
