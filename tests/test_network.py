import json

from src.simulation.network import (
    CoordinatedSignalManager,
    build_network,
    run_network_simulation,
)
from src.simulation.observation import DetectorObservation
from src.simulation.omniverse import export_omniverse_synthetic_data
from src.utils.config import LayoutConfig, PhaseConfig


def build_layout(layout_id: str) -> LayoutConfig:
    return LayoutConfig(
        id=layout_id,
        phases=[
            PhaseConfig(name="main_corridor", lanes=["N_S"], min_green=5, max_green=10),
            PhaseConfig(name="side_street", lanes=["E_W"], min_green=5, max_green=10),
        ],
        sensors={},
    )


def test_corridor_alignment_switches_to_green_band():
    layouts = [build_layout("A"), build_layout("B")]
    network = build_network(layouts, offsets={"A": 0, "B": 5})
    coordinator = CoordinatedSignalManager(corridor_lanes=["N_S"], cycle_length=60, green_band=15)

    network.intersections["B"].set_phase("side_street")
    observations = {
        "A": DetectorObservation(vehicles={"N_S": 15, "E_W": 0}, pedestrians={"N_S": 0, "E_W": 0}),
        "B": DetectorObservation(vehicles={"N_S": 10, "E_W": 0}, pedestrians={"N_S": 0, "E_W": 0}),
    }

    network.time = 3
    decisions = coordinator.sync_and_decide(network, observations)

    assert network.intersections["B"].current_phase.name == "main_corridor"
    assert all(decision.switch_phase is False for decision in decisions.values())


def test_omniverse_export_contains_frames(tmp_path):
    layouts = [build_layout("A"), build_layout("B")]
    network = run_network_simulation(
        layouts=layouts,
        coordinator=CoordinatedSignalManager(corridor_lanes=["N_S"], cycle_length=30, green_band=10),
        steps=5,
        arrival_intensity=0.1,
        crossing_rate=0.0,
    )

    output_file = tmp_path / "synthetic.json"
    export_omniverse_synthetic_data(network.intersections.values(), output_file)

    with output_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["frames"], "Expected synthetic frames in export"
    assert data["metadata"]["simulator"] == "traffic_lights_optimization"
