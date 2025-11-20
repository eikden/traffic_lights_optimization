from src.control.policy import ActuationDecision, DemandResponsiveController
from src.simulation.entities import IntersectionState, LaneState, PhaseState
from src.simulation.observation import DetectorObservation


def build_intersection() -> IntersectionState:
    lanes = {"A": LaneState(id="A", queue=10), "B": LaneState(id="B", queue=0)}
    phases = [PhaseState(name="phase_one", lanes=["A"], min_green=5, max_green=10)]
    return IntersectionState(layout_id="test", phases=phases, lanes=lanes)


def test_extend_within_min_green():
    controller = DemandResponsiveController(vehicle_threshold=5)
    intersection = build_intersection()
    obs = DetectorObservation(vehicles={"A": 1, "B": 0}, pedestrians={"A": 0, "B": 0})

    decision = controller.decide(intersection, obs)
    assert decision == ActuationDecision(switch_phase=False)


def test_switch_when_threshold_reached():
    controller = DemandResponsiveController(vehicle_threshold=5)
    intersection = build_intersection()
    intersection.current_phase.elapsed = 6
    obs = DetectorObservation(vehicles={"A": 12, "B": 0}, pedestrians={"A": 0, "B": 0})

    decision = controller.decide(intersection, obs)
    assert decision == ActuationDecision(switch_phase=True)
