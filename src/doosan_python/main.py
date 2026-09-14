"""Run the minimal model-to-joint-command example."""

import argparse
import logging

from doosan_python.config import load_config
from doosan_python.control.robot import DoosanRobot, validate_joint_deltas
from doosan_python.models.policy import MockPolicy

logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the model-to-joint control example.")
    parser.add_argument("--config", help="Custom YAML configuration path")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Send predicted movements to the connected robot",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    robot = None
    moving = False
    try:
        config = load_config(args.config)
        policy = MockPolicy(
            config.mock_model.joint_index, config.mock_model.delta_deg
        )
        robot = DoosanRobot(
            config.robot.name, config.motion.service_timeout_sec
        )
        robot.connect()
        if args.execute:
            robot.ensure_ready()

        for _ in range(config.mock_model.prediction_count):
            current_joints = robot.get_joint_positions()
            prediction = validate_joint_deltas(
                policy.predict(current_joints),
                config.motion.max_relative_delta,
            )
            logger.info("Model prediction (relative deg): %s", prediction)
            if args.execute:
                moving = True
                if not robot.move_joint_relative(
                    prediction,
                    velocity=config.motion.velocity,
                    acceleration=config.motion.acceleration,
                    max_delta=config.motion.max_relative_delta,
                ):
                    raise RuntimeError("relative joint movement failed")
                moving = False
        return 0
    except KeyboardInterrupt:
        if moving and robot is not None:
            robot.stop()
        return 130
    except (FileNotFoundError, RuntimeError, TypeError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")
    finally:
        if robot is not None:
            robot.close()


if __name__ == "__main__":
    raise SystemExit(main())
