#!/usr/bin/env python3
"""
두산 로봇(A0912) 대화형 관절 미세 조정 프로그램 (Interactive Jog)

[설명]
터미널에서 원하는 관절 번호(1~6)와 움직일 각도(예: +5 또는 -5)를
직접 입력하면서 실시간으로 조금씩 로봇을 조정해볼 수 있습니다.
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


class InteractiveJogger(Node):
    def __init__(self):
        super().__init__('interactive_jogger')
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

        while not self.cli_get_pos.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('로봇 제어기 연결 대기 중...')

    def ensure_robot_ready(self):
        """로봇 모터가 켜져 있고(STANDBY) 자동 모드(AUTONOMOUS)인지 확인 및 전환합니다."""
        req_mode = GetRobotMode.Request()
        fut_mode = self.cli_get_mode.call_async(req_mode)
        rclpy.spin_until_future_complete(self, fut_mode)
        res_mode = fut_mode.result()
        if res_mode and res_mode.robot_mode != 1:
            req_set_mode = SetRobotMode.Request()
            req_set_mode.robot_mode = 1
            fut_set = self.cli_set_mode.call_async(req_set_mode)
            rclpy.spin_until_future_complete(self, fut_set)

        req_state = GetRobotState.Request()
        fut_state = self.cli_get_state.call_async(req_state)
        rclpy.spin_until_future_complete(self, fut_state)
        res_state = fut_state.result()

        if res_state:
            state = res_state.robot_state
            if state == 3:  # SAFE_OFF
                print("⚡ 서보 모터가 꺼져 있어 대기 모드(STANDBY)로 켭니다...")
                req_ctrl = SetRobotControl.Request()
                req_ctrl.robot_control = 3
                fut_ctrl = self.cli_set_control.call_async(req_ctrl)
                rclpy.spin_until_future_complete(self, fut_ctrl)
                time.sleep(1.0)
            elif state == 5:  # SAFE_STOP
                req_ctrl = SetRobotControl.Request()
                req_ctrl.robot_control = 2
                fut_ctrl = self.cli_set_control.call_async(req_ctrl)
                rclpy.spin_until_future_complete(self, fut_ctrl)
                time.sleep(1.0)
        return True

    def print_current_angles(self):
        req = GetCurrentPosj.Request()
        future = self.cli_get_pos.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        res = future.result()
        if res and res.success:
            print("\n" + "-" * 50)
            print("📍 현재 로봇 관절 각도:")
            for i, val in enumerate(res.pos, start=1):
                print(f"  [Joint {i}] : {val:7.2f}°", end="  ")
                if i % 3 == 0:
                    print()
            print("-" * 50)
            return list(res.pos)
        return None

    def move_single_joint(self, joint_idx, delta_deg, vel=10.0, acc=20.0):
        deltas = [0.0] * 6
        deltas[joint_idx - 1] = float(delta_deg)

        req = MoveJoint.Request()
        req.pos = deltas
        req.vel = float(vel)    # 안전 저속 (10 deg/sec)
        req.acc = float(acc)
        req.time = 0.0
        req.radius = 0.0
        req.mode = 1           # 1: 상대 이동 (Relative)
        req.blend_type = 0
        req.sync_type = 0

        print(f"⚙️  Joint {joint_idx}번을 {delta_deg:+0.1f}° 회전 중... (안전 저속)")
        future = self.cli_move_joint.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        res = future.result()
        if res and res.success:
            print("✅ 이동 완료!")
        else:
            print("❌ 이동 실패 (티치 펜던트의 서보 On 상태 또는 비상 정지 해제 여부를 확인해주세요)")


def main():
    rclpy.init()
    jogger = InteractiveJogger()
    jogger.ensure_robot_ready()

    print("=" * 55)
    print(" 🤖 두산 협동로봇 관절 미세 조정 콘솔")
    print(" (종료하려면 'q'를 입력하세요)")
    print("=" * 55)

    try:
        while rclpy.ok():
            jogger.print_current_angles()
            user_input = input("\n움직일 [관절번호(1~6)]와 [각도(도)]를 입력하세요 (예: 6 5 또는 6 -5) -> ").strip()
            
            if user_input.lower() in ['q', 'quit', 'exit']:
                print("프로그램을 종료합니다.")
                break

            parts = user_input.split()
            if len(parts) != 2:
                print("⚠️  입력 형식 오류! '관절번호 각도' 형태로 띄어쓰기로 구분해 입력해주세요 (예: 6 5)")
                continue

            try:
                joint_num = int(parts[0])
                delta = float(parts[1])

                if not (1 <= joint_num <= 6):
                    print("⚠️  관절 번호는 1부터 6까지만 가능합니다.")
                    continue

                if abs(delta) > 30.0:
                    print(f"⚠️  안전을 위해 1회 입력 시 30도 이내로만 조정 가능합니다. (입력값: {delta}°)")
                    continue

                jogger.move_single_joint(joint_num, delta)

            except ValueError:
                print("⚠️  숫자를 올바르게 입력해주세요.")

    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
    finally:
        jogger.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
