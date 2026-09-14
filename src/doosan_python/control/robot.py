"""Shared Doosan ROS 2 service client used by every example."""

import logging
import math
import time
from collections.abc import Sequence

from doosan_python.launch import ROS_INSTALL_URL

logger = logging.getLogger(__name__)

try:
    import rclpy
    from dsr_msgs2.srv import (
        GetCurrentPosj,
        GetRobotMode,
        GetRobotState,
        MoveJoint,
        MoveStop,
        SetRobotControl,
        SetRobotMode,
    )
    from rclpy.node import Node

    HAS_ROS = True
except ImportError:
    HAS_ROS = False
    Node = object


def require_ros() -> None:
    """Raise a useful error instead of silently using fake hardware."""
    if not HAS_ROS:
        raise RuntimeError(
            f"ROS 2 or dsr_msgs2 is unavailable. Install it from {ROS_INSTALL_URL}"
        )


def validate_joint_deltas(
    deltas: Sequence[float], max_delta: float
) -> list[float]:
    """Validate a model or user command before it reaches ROS."""
    if len(deltas) != 6:
        raise ValueError("relative movement requires 6 joint deltas")
    values = [float(value) for value in deltas]
    if not all(math.isfinite(value) for value in values):
        raise ValueError("joint deltas must be finite numbers")
    if any(abs(value) > max_delta for value in values):
        raise ValueError(f"joint delta exceeds configured limit of {max_delta} deg")
    return values


class DoosanRobot(Node):
    """Small ROS service adapter for basic joint control."""

    def __init__(self, name: str = "dsr01", service_timeout_sec: float = 5.0):
        require_ros()
        self._owns_ros_context = not rclpy.ok()
        if self._owns_ros_context:
            rclpy.init()
        super().__init__("doosan_python_controller")
        self.service_timeout_sec = service_timeout_sec
        prefix = f"/{name.strip('/')}"
        self._get_pos = self.create_client(
            GetCurrentPosj, f"{prefix}/aux_control/get_current_posj"
        )
        self._move_joint = self.create_client(
            MoveJoint, f"{prefix}/motion/move_joint"
        )
        self._move_stop = self.create_client(MoveStop, f"{prefix}/motion/move_stop")
        self._get_state = self.create_client(
            GetRobotState, f"{prefix}/system/get_robot_state"
        )
        self._set_control = self.create_client(
            SetRobotControl, f"{prefix}/system/set_robot_control"
        )
        self._get_mode = self.create_client(
            GetRobotMode, f"{prefix}/system/get_robot_mode"
        )
        self._set_mode = self.create_client(
            SetRobotMode, f"{prefix}/system/set_robot_mode"
        )

    def connect(self) -> None:
        """Wait for the controller service or fail with a launch hint."""
        if not self._get_pos.wait_for_service(timeout_sec=self.service_timeout_sec):
            raise RuntimeError(
                "Doosan ROS services are unavailable. Start them with "
                "'source env.sh -virtual' or 'source env.sh -real'."
            )

    def _call(self, client, request):
        future = client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        result = future.result()
        if result is None:
            raise RuntimeError("Doosan ROS service call failed")
        return result

    def ensure_ready(self) -> None:
        """Switch to autonomous mode and recover supported standby states."""
        mode = self._call(self._get_mode, GetRobotMode.Request())
        if mode.robot_mode != 1:
            request = SetRobotMode.Request()
            request.robot_mode = 1
            self._call(self._set_mode, request)

        state = self._call(self._get_state, GetRobotState.Request()).robot_state
        reset = {3: 3, 5: 2}.get(state)
        if reset is not None:
            request = SetRobotControl.Request()
            request.robot_control = reset
            self._call(self._set_control, request)
            time.sleep(1.0)
        final_state = self._call(
            self._get_state, GetRobotState.Request()
        ).robot_state
        if final_state != 1:
            raise RuntimeError(f"robot is not in STANDBY state: {final_state}")

    def get_joint_positions(self) -> list[float]:
        """Return the current six joint angles in degrees."""
        result = self._call(self._get_pos, GetCurrentPosj.Request())
        if not result.success:
            raise RuntimeError("failed to read current joint positions")
        return [float(value) for value in result.pos]

    def move_joint_relative(
        self,
        deltas: Sequence[float],
        *,
        velocity: float,
        acceleration: float,
        max_delta: float,
    ) -> bool:
        """Send one validated relative joint movement."""
        request = MoveJoint.Request()
        request.pos = validate_joint_deltas(deltas, max_delta)
        request.vel = float(velocity)
        request.acc = float(acceleration)
        request.time = 0.0
        request.radius = 0.0
        request.mode = 1
        request.blend_type = 0
        request.sync_type = 0
        result = self._call(self._move_joint, request)
        return bool(result.success)

    def stop(self, stop_mode: int = 1) -> bool:
        request = MoveStop.Request()
        request.stop_mode = stop_mode
        return bool(self._call(self._move_stop, request).success)

    def close(self) -> None:
        self.destroy_node()
        if self._owns_ros_context and rclpy.ok():
            rclpy.shutdown()
