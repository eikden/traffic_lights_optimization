from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class DetectorObservation:
    vehicles: Dict[str, int]
    pedestrians: Dict[str, int]
