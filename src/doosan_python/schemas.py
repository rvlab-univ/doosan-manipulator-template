"""Standard data contracts shared across modules."""

from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np


@dataclass
class DetectionResult:
    """Output contract from the vision/model layer."""
    label: str
    confidence: float
    bbox: List[int] = field(default_factory=list)  # [x1, y1, x2, y2]
    point_3d_cam: Optional[np.ndarray] = None      # [X, Y, Z] in camera frame (mm or m)


@dataclass
class TargetPose:
    """Robot Cartesian pose representation."""
    position: List[float]     # [X, Y, Z] (mm)
    orientation: List[float]  # [Rx, Ry, Rz] (deg) or quaternion

    def as_list(self) -> List[float]:
        return list(self.position) + list(self.orientation)


@dataclass
class GraspPlan:
    """Trajectory or poses calculated by the grasping algorithm."""
    approach_pose: TargetPose
    pick_pose: TargetPose
    retreat_pose: TargetPose
