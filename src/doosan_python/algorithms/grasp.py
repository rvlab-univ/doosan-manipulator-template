"""Grasp planning and approach trajectory logic."""

from typing import List, Optional, Union
import numpy as np

from doosan_python.schemas import GraspPlan, TargetPose
from doosan_python.utils.logger import get_logger

logger = get_logger("algorithms.grasp")


def calculate_grasp_plan(
    target_base_pos: Union[np.ndarray, List[float]],
    approach_offset_z: float = 100.0,
    default_orientation: Optional[List[float]] = None,
) -> GraspPlan:
    """Compute approach, pick, and retreat poses based on the target position.

    Args:
        target_base_pos: [X, Y, Z] target position in robot base frame (mm).
        approach_offset_z: Vertical clearance distance above target for approach and retreat (mm).
        default_orientation: End-effector orientation [Rx, Ry, Rz] in degrees. Default pointing downward [0, 180, 0].

    Returns:
        GraspPlan containing approach, pick, and retreat TargetPoses.
    """
    ori = default_orientation or [0.0, 180.0, 0.0]

    x, y, z = float(target_base_pos[0]), float(target_base_pos[1]), float(target_base_pos[2])

    approach = TargetPose(position=[x, y, z + approach_offset_z], orientation=ori)
    pick = TargetPose(position=[x, y, z], orientation=ori)
    retreat = TargetPose(position=[x, y, z + approach_offset_z], orientation=ori)

    plan = GraspPlan(approach_pose=approach, pick_pose=pick, retreat_pose=retreat)
    logger.debug(f"Computed GraspPlan: Pick={pick.position}, Offset={approach_offset_z}mm")
    return plan


if __name__ == "__main__":
    plan = calculate_grasp_plan(np.array([400.0, 100.0, 150.0]))
    logger.info(f"Approach pose: {plan.approach_pose}")
    logger.info(f"Pick pose:     {plan.pick_pose}")
    logger.info(f"Retreat pose:  {plan.retreat_pose}")
    logger.info("Grasp plan standalone test completed.")
