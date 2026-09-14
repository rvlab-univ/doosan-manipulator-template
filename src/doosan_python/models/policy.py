"""Minimal model contract for joint-control experiments."""

from collections.abc import Sequence


class MockPolicy:
    """Example policy that alternates one relative joint command.

    Replace this class with a real model while keeping ``predict`` unchanged:
    input is six current joint angles in degrees, output is six relative joint
    deltas in degrees. Models must not call ROS or hardware directly.
    """

    def __init__(self, joint_index: int = 6, delta_deg: float = 10.0):
        if not 1 <= joint_index <= 6:
            raise ValueError("joint_index must be between 1 and 6")
        self.joint_index = joint_index
        self.delta_deg = float(delta_deg)
        self._direction = 1.0

    def predict(self, current_joints: Sequence[float]) -> list[float]:
        """Return the next six-axis relative joint command in degrees."""
        if len(current_joints) != 6:
            raise ValueError("current_joints must contain 6 joint angles")
        deltas = [0.0] * 6
        deltas[self.joint_index - 1] = self._direction * self.delta_deg
        self._direction *= -1.0
        return deltas
