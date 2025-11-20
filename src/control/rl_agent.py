from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import torch
import torch.nn as nn

from src.simulation.entities import IntersectionState
from src.simulation.observation import DetectorObservation


class SimplePolicyNet(nn.Module):
    def __init__(self, lanes: int, hidden: int = 32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(lanes * 2, hidden),
            nn.ReLU(),
            nn.Linear(hidden, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # pragma: no cover - sample only
        return self.net(x)


@dataclass
class ReinforcementLearningAgent:
    model: SimplePolicyNet

    def decide(self, intersection: IntersectionState, observation: DetectorObservation) -> Tuple[int, float]:
        # Example forward pass; training loop should be added for real experiments.
        lanes = list(observation.vehicles.keys())
        vehicle_tensor = torch.tensor([observation.vehicles[l] for l in lanes], dtype=torch.float32)
        pedestrian_tensor = torch.tensor([observation.pedestrians[l] for l in lanes], dtype=torch.float32)
        state = torch.cat([vehicle_tensor, pedestrian_tensor]).unsqueeze(0)
        logits = self.model(state)
        probabilities = torch.softmax(logits, dim=-1)
        action = torch.argmax(probabilities, dim=-1).item()
        return action, probabilities[0, action].item()
