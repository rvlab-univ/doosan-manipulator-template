"""Interactive relative joint control using the shared robot adapter."""

import argparse
import logging

from doosan_python.config import load_config
from doosan_python.control.robot import DoosanRobot

logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactively jog one robot joint.")
    parser.add_argument("--config", help="Custom YAML configuration path")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    robot = None
    try:
        config = load_config(args.config)
        robot = DoosanRobot(
            config.robot.name, config.motion.service_timeout_sec
        )
        robot.connect()
        robot.ensure_ready()

        while True:
            logger.info(
                "Current joint positions (deg): %s", robot.get_joint_positions()
            )
            value = input("joint(1-6) delta_deg, or q: ").strip()
            if value.lower() in {"q", "quit", "exit"}:
                return 0
            parts = value.split()
            if len(parts) != 2:
                print("Enter a joint number and angle, for example: 6 5")
                continue
            try:
                joint = int(parts[0])
                delta = float(parts[1])
                if not 1 <= joint <= 6:
                    raise ValueError("joint must be between 1 and 6")
                movement = [0.0] * 6
                movement[joint - 1] = delta
                if not robot.move_joint_relative(
                    movement,
                    velocity=config.motion.velocity,
                    acceleration=config.motion.acceleration,
                    max_delta=config.motion.max_relative_delta,
                ):
                    raise RuntimeError("relative joint movement failed")
            except ValueError as error:
                print(f"Invalid command: {error}")
    except KeyboardInterrupt:
        if robot is not None:
            robot.stop()
        return 130
    except (FileNotFoundError, RuntimeError, TypeError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")
    finally:
        if robot is not None:
            robot.close()


if __name__ == "__main__":
    raise SystemExit(main())
