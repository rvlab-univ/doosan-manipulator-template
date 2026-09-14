"""Show a small relative joint movement using the shared robot adapter."""

import argparse
import logging

from doosan_python.config import load_config
from doosan_python.control.robot import DoosanRobot

logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview or execute one joint round trip.")
    parser.add_argument("--config", help="Custom YAML configuration path")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Send the two movements to the connected robot",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    robot = None
    try:
        config = load_config(args.config)
        robot = DoosanRobot(
            config.robot.name, config.motion.service_timeout_sec
        )
        robot.connect()
        current = robot.get_joint_positions()
        logger.info("Current joint positions (deg): %s", current)

        forward = [0.0] * 6
        forward[config.mock_model.joint_index - 1] = config.mock_model.delta_deg
        movements = (forward, [-value for value in forward])
        if args.execute:
            robot.ensure_ready()
        for movement in movements:
            logger.info("Relative movement (deg): %s", movement)
            if args.execute and not robot.move_joint_relative(
                movement,
                velocity=config.motion.velocity,
                acceleration=config.motion.acceleration,
                max_delta=config.motion.max_relative_delta,
            ):
                raise RuntimeError("relative joint movement failed")
        return 0
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
