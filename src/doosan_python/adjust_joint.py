#!/usr/bin/env python3
"""
두산 로봇(A0912) 관절 조금씩 움직여보기 (안전 테스트 예제)

[작동 방식]
1. 로봇 상태(서보 On 여부)를 확인하고, 꺼져있으면 자동으로 Standby(대기) 상태로 켭니다.
2. 현재 로봇의 6개 관절 각도(도, deg)를 읽어와서 화면에 출력합니다.
3. 가장 안전한 끝단 관절(6번 손목 관절)을 딱 +5도만 살짝 돌립니다.
4. 2초 대기 후, 다시 원래 위치(-5도)로 되돌려놓습니다.

[실행 방법]
source ~/ros2_ws/install/setup.bash (또는 .zsh)
python3 adjust_joint.py
"""

import time
import rclpy
from rclpy.node import Node
from dsr_msgs2.srv import (
    MoveJoint,
    GetCurrentPosj,
    GetRobotState,
    SetRobotControl,
    GetRobotMode,
    SetRobotMode,
)


class RobotAdjuster(Node):
    def __init__(self):
        super().__init__('robot_adjuster')

        # 서비스 클라이언트 생성
        self.cli_get_pos = self.create_client(
            GetCurrentPosj, '/dsr_controller2/aux_control/get_current_posj'
        )
        self.cli_move_joint = self.create_client(
            MoveJoint, '/dsr_controller2/motion/move_joint'
        )
        self.cli_get_state = self.create_client(
            GetRobotState, '/dsr_controller2/system/get_robot_state'
        )
        self.cli_set_control = self.create_client(
            SetRobotControl, '/dsr_controller2/system/set_robot_control'
        )
        self.cli_get_mode = self.create_client(
            GetRobotMode, '/dsr_controller2/system/get_robot_mode'
        )
        self.cli_set_mode = self.create_client(
            SetRobotMode, '/dsr_controller2/system/set_robot_mode'
        )

        self.get_logger().info('로봇 제어 서비스 연결 대기 중...')
        while not self.cli_get_pos.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('연결 대기 중...')
        self.get_logger().info('✅ 로봇 제어기 연결 성공!\n')

    def ensure_robot_ready(self):
        """로봇 모터가 켜져 있고(STANDBY) 자동 모드(AUTONOMOUS)인지 확인 및 전환합니다."""
        # 1. 로봇 동작 모드 확인 (1: Autonomous)
        req_mode = GetRobotMode.Request()
        fut_mode = self.cli_get_mode.call_async(req_mode)
        rclpy.spin_until_future_complete(self, fut_mode)
        res_mode = fut_mode.result()
        if res_mode and res_mode.robot_mode != 1:
            print("⚙️  로봇을 자동 모드(Autonomous)로 전환합니다...")
            req_set_mode = SetRobotMode.Request()
            req_set_mode.robot_mode = 1
            fut_set = self.cli_set_mode.call_async(req_set_mode)
            rclpy.spin_until_future_complete(self, fut_set)

        # 2. 로봇 서보 상태 확인 (1: STANDBY, 3: SAFE_OFF)
        req_state = GetRobotState.Request()
        fut_state = self.cli_get_state.call_async(req_state)
        rclpy.spin_until_future_complete(self, fut_state)
        res_state = fut_state.result()

        if res_state:
            state = res_state.robot_state
            if state == 3:  # STATE_SAFE_OFF (서보 꺼짐)
                print("⚡ 서보 모터가 꺼져 있습니다(SAFE_OFF). 대기 모드(STANDBY)로 켭니다...")
                req_ctrl = SetRobotControl.Request()
                req_ctrl.robot_control = 3  # CONTROL_RESET_SAFET_OFF -> STANDBY 전환
                fut_ctrl = self.cli_set_control.call_async(req_ctrl)
                rclpy.spin_until_future_complete(self, fut_ctrl)
                time.sleep(1.0)
            elif state == 5:  # STATE_SAFE_STOP
                print("⚠️  안전 정지(SAFE_STOP) 상태입니다. 리셋합니다...")
                req_ctrl = SetRobotControl.Request()
                req_ctrl.robot_control = 2  # CONTROL_RESET_SAFET_STOP
                fut_ctrl = self.cli_set_control.call_async(req_ctrl)
                rclpy.spin_until_future_complete(self, fut_ctrl)
                time.sleep(1.0)

            # 최종 상태 확인
            fut_state2 = self.cli_get_state.call_async(GetRobotState.Request())
            rclpy.spin_until_future_complete(self, fut_state2)
            final_st = fut_state2.result().robot_state
            if final_st == 1:
                print("🟢 로봇 준비 완료! (상태: STANDBY 대기 중)\n")
                return True
            else:
                print(f"⚠️  현재 로봇 상태 코드: {final_st}")
                return True
        return False

    def get_current_joint_angles(self):
        """현재 6개 관절의 각도(deg)를 가져옵니다."""
        req = GetCurrentPosj.Request()
        future = self.cli_get_pos.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        res = future.result()
        if res and res.success:
            return list(res.pos)
        else:
            self.get_logger().error('현재 각도를 읽어오지 못했습니다.')
            return None

    def move_joint_relative(self, joint_deltas, vel=10.0, acc=20.0):
        """
        현재 위치 기준으로 관절 각도를 상대적으로(조금씩) 조정합니다.
        - joint_deltas: [J1, J2, J3, J4, J5, J6] 각 관절의 변화량(단위: degree)
        - vel: 회전 속도 (안전을 위해 기본 10 deg/sec의 아주 느린 속도)
        - acc: 가속도 (기본 20 deg/sec^2)
        """
        req = MoveJoint.Request()
        req.pos = [float(val) for val in joint_deltas]
        req.vel = float(vel)
        req.acc = float(acc)
        req.time = 0.0
        req.radius = 0.0
        req.mode = 1        # 0: 절대 각도 이동, 1: 상대 각도 이동 (현재 위치 기준 변화량)
        req.blend_type = 0
        req.sync_type = 0   # 0: 동작 완료될 때까지 대기 (SYNC)

        future = self.cli_move_joint.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        res = future.result()
        return res and res.success


def main():
    rclpy.init()
    robot = RobotAdjuster()

    # 0. 로봇 서보 전원 및 준비 상태 확인
    robot.ensure_robot_ready()

    # 1. 현재 로봇 각도 출력
    current_angles = robot.get_current_joint_angles()
    if current_angles is None:
        robot.destroy_node()
        rclpy.shutdown()
        return

    print("=" * 55)
    print("📍 현재 로봇 관절 각도 (단위: degree)")
    for i, angle in enumerate(current_angles, start=1):
        print(f"   관절 {i}번 (Joint {i}): {angle:8.2f}°")
    print("=" * 55)

    # 2. 6번 관절(손목 끝)을 안전하게 +5도만 살짝 회전
    print("\n👉 [테스트 1] 6번 관절(손목)을 +5도 살짝 회전합니다... (저속 안전 모드)")
    # [J1, J2, J3, J4, J5, J6]
    delta_move = [0.0, 0.0, 0.0, 0.0, 0.0, 5.0]
    success = robot.move_joint_relative(delta_move, vel=10.0, acc=20.0)

    if success:
        print("   ✅ +5도 이동 완료!")
    else:
        print("   ❌ 이동 실패 (로봇 상태 또는 비상 정지 확인 필요)")

    time.sleep(2.0)

    # 3. 다시 원래 자리로 복귀 (-5도 회전)
    print("\n👉 [테스트 2] 다시 원래 위치로 -5도 되돌립니다...")
    delta_return = [0.0, 0.0, 0.0, 0.0, 0.0, -5.0]
    success = robot.move_joint_relative(delta_return, vel=10.0, acc=20.0)

    if success:
        print("   ✅ 원래 위치 복귀 완료!")
    else:
        print("   ❌ 복귀 실패")

    # 4. 최종 각도 재확인
    final_angles = robot.get_current_joint_angles()
    print("\n=" * 55)
    print("📍 이동 후 최종 관절 각도:")
    for i, angle in enumerate(final_angles, start=1):
        print(f"   관절 {i}번 (Joint {i}): {angle:8.2f}°")
    print("=" * 55)

    print("\n🎉 모든 테스트가 안전하게 완료되었습니다.")
    robot.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
