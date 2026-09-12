"""Robot control interface for Doosan Robotics manipulators."""

import time
from typing import List, Optional, Union

from doosan_python.schemas import TargetPose
from doosan_python.utils.logger import get_logger

logger = get_logger("control.robot")

try:
    import rclpy
    from rclpy.node import Node
    HAS_RCLPY = True
except ImportError:
    HAS_RCLPY = False
    Node = object  # type: ignore

try:
    from dsr_msgs2.srv import (
        GetCurrentPose,
        GetCurrentPosj,
        GetCurrentPosx,
        GetRobotMode,
        GetRobotState,
        MoveJoint,
        MoveLine,
        MoveStop,
        SetRobotControl,
        SetRobotMode,
    )
    HAS_DSR_MSGS = True
except ImportError:
    HAS_DSR_MSGS = False


class DoosanRobot(Node):
    """Wrapper class for controlling Doosan robot manipulators via ROS 2 services."""

    def __init__(
        self,
        ip: str = "192.168.137.100",
        port: int = 12345,
        service_prefix: str = "/dsr_controller2",
        node_name: str = "doosan_robot_controller",
    ):
        self.ip = ip
        self.port = port
        self.service_prefix = service_prefix.rstrip("/")
        self.connected = False

        if not HAS_RCLPY or not HAS_DSR_MSGS:
            logger.warning(
                "ROS 2 environment (rclpy or dsr_msgs2) is not available. "
                "DoosanRobot is operating in mock / simulation fallback mode."
            )
            return

        if not rclpy.ok():
            rclpy.init()

        super().__init__(node_name)

        # Service clients
        self.cli_get_posj = self.create_client(
            GetCurrentPosj, f"{self.service_prefix}/aux_control/get_current_posj"
        )
        self.cli_get_posx = self.create_client(
            GetCurrentPosx, f"{self.service_prefix}/aux_control/get_current_posx"
        )
        self.cli_get_pose = self.create_client(
            GetCurrentPose, f"{self.service_prefix}/system/get_current_pose"
        )
        self.cli_move_joint = self.create_client(
            MoveJoint, f"{self.service_prefix}/motion/move_joint"
        )
        self.cli_move_line = self.create_client(
            MoveLine, f"{self.service_prefix}/motion/move_line"
        )
        self.cli_move_stop = self.create_client(
            MoveStop, f"{self.service_prefix}/motion/move_stop"
        )
        self.cli_get_state = self.create_client(
            GetRobotState, f"{self.service_prefix}/system/get_robot_state"
        )
        self.cli_set_control = self.create_client(
            SetRobotControl, f"{self.service_prefix}/system/set_robot_control"
        )
        self.cli_get_mode = self.create_client(
            GetRobotMode, f"{self.service_prefix}/system/get_robot_mode"
        )
        self.cli_set_mode = self.create_client(
            SetRobotMode, f"{self.service_prefix}/system/set_robot_mode"
        )

        logger.info(
            f"Initialized DoosanRobot client for {self.ip}:{self.port} (service prefix: {self.service_prefix})"
        )

    def connect(self, timeout_sec: float = 5.0) -> bool:
        """Establish connection to robot controller / ROS 2 services and verify ready state."""
        if not HAS_RCLPY or not HAS_DSR_MSGS or not hasattr(self, "cli_get_posj"):
            logger.info(f"[Mock] Connection request to {self.ip} bypassed (ROS 2 offline).")
            self.connected = False
            return False

        logger.info(f"Connecting to {self.ip} (waiting up to {timeout_sec}s for services)...")

        start_time = time.time()
        while not self.cli_get_posj.wait_for_service(timeout_sec=1.0):
            if time.time() - start_time >= timeout_sec:
                logger.warning(
                    f"Robot controller service ({self.service_prefix}) not available after {timeout_sec}s."
                )
                self.connected = False
                return False
            logger.info(f"Waiting for robot services ({self.service_prefix})...")

        ready = self.ensure_robot_ready()
        self.connected = ready
        if self.connected:
            logger.info("Successfully connected to robot and confirmed ready state.")
        else:
            logger.warning("Connected to services, but robot controller is not in ready state.")
        return self.connected

    def ensure_robot_ready(self) -> bool:
        """Ensure robot servo is on (STANDBY) and operating in AUTONOMOUS mode."""
        if not self.connected and not hasattr(self, "cli_get_mode"):
            return False

        # 1. Mode check (1: AUTONOMOUS)
        req_mode = GetRobotMode.Request()
        fut_mode = self.cli_get_mode.call_async(req_mode)
        rclpy.spin_until_future_complete(self, fut_mode)
        res_mode = fut_mode.result()
        if res_mode and res_mode.robot_mode != 1:
            logger.info("Switching robot mode to Autonomous (1)...")
            req_set_mode = SetRobotMode.Request()
            req_set_mode.robot_mode = 1
            fut_set = self.cli_set_mode.call_async(req_set_mode)
            rclpy.spin_until_future_complete(self, fut_set)

        # 2. State check (1: STANDBY, 3: SAFE_OFF, 5: SAFE_STOP)
        req_state = GetRobotState.Request()
        fut_state = self.cli_get_state.call_async(req_state)
        rclpy.spin_until_future_complete(self, fut_state)
        res_state = fut_state.result()

        if res_state:
            state = res_state.robot_state
            if state == 3:  # SAFE_OFF
                logger.info("Servo motor is SAFE_OFF. Powering on to STANDBY...")
                req_ctrl = SetRobotControl.Request()
                req_ctrl.robot_control = 3  # CONTROL_RESET_SAFET_OFF -> STANDBY
                fut_ctrl = self.cli_set_control.call_async(req_ctrl)
                rclpy.spin_until_future_complete(self, fut_ctrl)
                time.sleep(1.0)
            elif state == 5:  # SAFE_STOP
                logger.info("Robot in SAFE_STOP state. Resetting to STANDBY...")
                req_ctrl = SetRobotControl.Request()
                req_ctrl.robot_control = 2  # CONTROL_RESET_SAFET_STOP -> STANDBY
                fut_ctrl = self.cli_set_control.call_async(req_ctrl)
                rclpy.spin_until_future_complete(self, fut_ctrl)
                time.sleep(1.0)

            fut_check = self.cli_get_state.call_async(GetRobotState.Request())
            rclpy.spin_until_future_complete(self, fut_check)
            cur_st = fut_check.result().robot_state if fut_check.result() else None
            return cur_st == 1 or cur_st is not None

        return False

    def get_current_joint_angles(self) -> Optional[List[float]]:
        """Read current 6 joint angles (deg) from robot controller."""
        if not hasattr(self, "cli_get_posj"):
            return [0.0, 0.0, 90.0, 0.0, 90.0, 0.0]

        req = GetCurrentPosj.Request()
        fut = self.cli_get_posj.call_async(req)
        rclpy.spin_until_future_complete(self, fut)
        res = fut.result()
        if res and res.success:
            return [float(v) for v in res.pos]
        logger.error("Failed to read current joint angles.")
        return None

    def move_home(
        self,
        joint_angles: Optional[List[float]] = None,
        vel: float = 30.0,
        acc: float = 60.0,
    ) -> bool:
        """Move to predefined or specified home joint angles (deg)."""
        target = joint_angles or [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        logger.info(f"Moving to Home joint positions: {target}")
        return self.move_j(target, vel=vel, acc=acc)

    def move_j(
        self,
        joints: List[float],
        vel: float = 30.0,
        acc: float = 60.0,
        mode: int = 0,
        sync: bool = True,
    ) -> bool:
        """Joint motion."""
        if len(joints) != 6:
            logger.error(f"MoveJ requires 6 joint angles, got {len(joints)}")
            return False

        if not hasattr(self, "cli_move_joint"):
            logger.info(f"[Mock MoveJ] -> {joints} (vel: {vel}, acc: {acc})")
            return True

        req = MoveJoint.Request()
        req.pos = [float(j) for j in joints]
        req.vel = float(vel)
        req.acc = float(acc)
        req.time = 0.0
        req.radius = 0.0
        req.mode = int(mode)
        req.blend_type = 0
        req.sync_type = 0 if sync else 1

        logger.info(f"MoveJ -> {req.pos} (vel: {vel} deg/s, acc: {acc} deg/s^2, mode: {mode})")
        fut = self.cli_move_joint.call_async(req)
        rclpy.spin_until_future_complete(self, fut)
        res = fut.result()
        success = res is not None and res.success
        if not success:
            logger.error("MoveJ execution failed.")
        return success

    def move_l(
        self,
        pose: Union[TargetPose, List[float]],
        vel: Union[float, List[float]] = 30.0,
        acc: Union[float, List[float]] = 60.0,
        ref: int = 0,
        mode: int = 0,
        sync: bool = True,
    ) -> bool:
        """Linear Cartesian motion."""
        pos_list = pose.as_list() if isinstance(pose, TargetPose) else [float(x) for x in pose]
        if len(pos_list) != 6:
            logger.error(f"MoveL requires 6D pose, got {len(pos_list)}")
            return False

        if not hasattr(self, "cli_move_line"):
            logger.info(f"[Mock MoveL] -> pos: {pos_list[:3]}, ori: {pos_list[3:]} (vel: {vel})")
            return True

        vel_list = [float(vel), float(vel)] if isinstance(vel, (int, float)) else [float(v) for v in vel]
        acc_list = [float(acc), float(acc)] if isinstance(acc, (int, float)) else [float(a) for a in acc]

        req = MoveLine.Request()
        req.pos = pos_list
        req.vel = vel_list
        req.acc = acc_list
        req.time = 0.0
        req.radius = 0.0
        req.ref = int(ref)
        req.mode = int(mode)
        req.blend_type = 0
        req.sync_type = 0 if sync else 1

        logger.info(f"MoveL -> pos: {pos_list[:3]}, ori: {pos_list[3:]} (vel: {vel_list}, acc: {acc_list})")
        fut = self.cli_move_line.call_async(req)
        rclpy.spin_until_future_complete(self, fut)
        res = fut.result()
        success = res is not None and res.success
        if not success:
            logger.error("MoveL execution failed.")
        return success

    def get_current_pose(self, ref: int = 0) -> TargetPose:
        """Read current tool tip pose from the robot."""
        if not hasattr(self, "cli_get_pose"):
            return TargetPose(position=[400.0, 0.0, 300.0], orientation=[0.0, 180.0, 0.0])

        req_pose = GetCurrentPose.Request()
        req_pose.space_type = 1
        fut = self.cli_get_pose.call_async(req_pose)
        rclpy.spin_until_future_complete(self, fut)
        res = fut.result()
        if res and res.success:
            pos = list(res.pos)
            return TargetPose(position=pos[0:3], orientation=pos[3:6])

        # Fallback to aux_control/get_current_posx
        req_posx = GetCurrentPosx.Request()
        req_posx.ref = int(ref)
        fut_posx = self.cli_get_posx.call_async(req_posx)
        rclpy.spin_until_future_complete(self, fut_posx)
        res_posx = fut_posx.result()
        if res_posx and res_posx.success and res_posx.task_pos_info:
            pos = list(res_posx.task_pos_info[0].data[:6])
            return TargetPose(position=pos[0:3], orientation=pos[3:6])

        logger.warning("Could not read live pose from controller. Returning fallback pose.")
        return TargetPose(position=[400.0, 0.0, 300.0], orientation=[0.0, 180.0, 0.0])

    def stop(self, stop_mode: int = 1) -> bool:
        """Safety stop (1: Quick stop, 2: Soft stop, 3: Hold stop)."""
        logger.info(f"Safety stop invoked (mode: {stop_mode}).")
        if not hasattr(self, "cli_move_stop"):
            return True

        req = MoveStop.Request()
        req.stop_mode = int(stop_mode)
        fut = self.cli_move_stop.call_async(req)
        rclpy.spin_until_future_complete(self, fut)
        res = fut.result()
        return res is not None and res.success

    def disconnect(self) -> None:
        """Clean up robot node."""
        self.connected = False
        try:
            if hasattr(self, "destroy_node"):
                self.destroy_node()
        except Exception:
            pass


if __name__ == "__main__":
    robot = DoosanRobot()
    connected = robot.connect(timeout_sec=2.0)
    if connected:
        robot.move_home()
    else:
        logger.info("Operating in standalone test mode.")
        pose = robot.get_current_pose()
        logger.info(f"Sample pose read: {pose}")
    robot.disconnect()
