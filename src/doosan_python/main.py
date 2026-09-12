"""Main execution entry point for the robotics vision-and-control pipeline."""

import argparse
import sys
import time

from doosan_python.algorithms.grasp import calculate_grasp_plan
from doosan_python.algorithms.transforms import cam_to_robot_base
from doosan_python.config import load_config
from doosan_python.control.gripper import Gripper
from doosan_python.control.robot import DoosanRobot
from doosan_python.models.camera import CameraStreamer
from doosan_python.models.detector import ObjectDetector
from doosan_python.utils.logger import get_logger, setup_logger

logger = get_logger("pipeline")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Vision-Guided Manipulation Pipeline for Doosan Robotics."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/default.yaml",
        help="Path to YAML configuration file (default: configs/default.yaml)",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Optional file path to persist execution logs",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    setup_logger(name="doosan_python", log_file=args.log_file)

    logger.info("==================================================")
    logger.info("  Doosan Robot Vision-Guided Control Pipeline     ")
    logger.info("==================================================")

    # 1. Load application configuration
    cfg = load_config(args.config)

    # 2. Initialize hardware interfaces and AI models using config
    logger.info("Initializing subsystems with loaded configuration...")
    cam = CameraStreamer(
        width=cfg.camera.width,
        height=cfg.camera.height,
        fps=cfg.camera.fps,
    )
    detector = ObjectDetector(
        weights_path=cfg.model.weights_path,
        conf_thresh=cfg.model.confidence_threshold,
    )
    robot = DoosanRobot(
        ip=cfg.robot.ip,
        port=cfg.robot.port,
        service_prefix=cfg.robot.service_prefix,
    )
    gripper = Gripper()

    # 3. Start hardware communication
    cam.start()
    connected = robot.connect(timeout_sec=3.0)
    if not connected:
        logger.warning(
            f"Robot controller at {cfg.robot.ip} ({cfg.robot.service_prefix}) is unreachable. "
            "Proceeding in perception & trajectory planning preview mode."
        )

    if connected:
        robot.move_home(
            joint_angles=cfg.robot.home_pose,
            vel=cfg.robot.default_vel,
            acc=cfg.robot.default_acc,
        )
    gripper.open()

    logger.info("Entering Vision-Guided Execution Stage...")
    try:
        # Step A: Capture sensory frame
        color_img, depth_img = cam.get_latest_frame(timeout=2.0)
        if color_img is None:
            logger.error("No camera frame received from sensor streamer.")
            return

        # Step B: Model inference
        logger.info(f"Running object detection for target: '{cfg.model.target_class}'...")
        detections = detector.infer(
            color_img,
            depth_img,
            target_label=cfg.model.target_class,
        )
        if not detections:
            logger.info("No target objects detected in scene.")
            return

        target = detections[0]
        logger.info(
            f"Target acquired: '{target.label}' | Confidence: {target.confidence:.2f}"
        )

        # Step C: Coordinate transformation & Grasp planning
        if target.point_3d_cam is not None:
            target_base = cam_to_robot_base(
                target.point_3d_cam,
                translation=cfg.transforms.cam_to_base_translation,
                rotation_matrix=None,  # Or construct rotation from cfg.transforms.cam_to_base_rotation
            )
            logger.info(f"Target coordinate in Robot Base frame: {target_base.round(2)}")

            plan = calculate_grasp_plan(target_base)
            logger.info(f"Calculated Grasp Trajectory: Pick position at {plan.pick_pose.position}")

            # Step D: Robot execution (if hardware connected)
            if connected:
                logger.info("Executing motion sequence on robot...")
                logger.info("1. Moving to approach pose...")
                robot.move_l(plan.approach_pose, vel=cfg.robot.default_vel, acc=cfg.robot.default_acc)

                logger.info("2. Moving to pick pose...")
                robot.move_l(plan.pick_pose, vel=cfg.robot.default_vel * 0.5, acc=cfg.robot.default_acc * 0.5)

                logger.info("3. Gripping object...")
                gripper.close()
                time.sleep(0.5)

                logger.info("4. Retreating with gripped object...")
                robot.move_l(plan.retreat_pose, vel=cfg.robot.default_vel, acc=cfg.robot.default_acc)
                robot.move_home(joint_angles=cfg.robot.home_pose)

                logger.info("5. Releasing object...")
                gripper.open()
            else:
                logger.info("[Preview Mode] Hardware execution skipped as robot controller is not connected.")

        logger.info("Pipeline execution cycle completed successfully.")

    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user. Issuing safety stop...")
        if connected:
            robot.stop()
    except Exception as e:
        logger.error(f"Unexpected pipeline exception: {e}", exc_info=True)
    finally:
        cam.stop()
        if connected:
            robot.disconnect()


if __name__ == "__main__":
    main()
