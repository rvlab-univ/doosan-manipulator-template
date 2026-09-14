"""Launch the configured Doosan ROS 2 MoveIt stack."""

import argparse
import shutil
import subprocess
from typing import Literal

from doosan_python.config import AppConfig, load_config

ROS_INSTALL_URL = (
    "https://doosanrobotics.github.io/doosan-robotics-ros-manual/jazzy/installation.html"
)


def build_launch_command(
    config: AppConfig, mode: Literal["real", "virtual"]
) -> list[str]:
    """Build the official dsr_bringup2 MoveIt launch command."""
    if mode not in {"real", "virtual"}:
        raise ValueError("mode must be real or virtual")
    host = config.robot.real_host if mode == "real" else config.robot.virtual_host
    return [
        "ros2",
        "launch",
        "dsr_bringup2",
        "dsr_bringup2_moveit.launch.py",
        f"mode:={mode}",
        f"model:={config.robot.model}",
        f"host:={host}",
        f"port:={config.robot.port}",
        f"name:={config.robot.name}",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch Doosan ROS 2 with project settings.")
    parser.add_argument("--mode", choices=("real", "virtual"), required=True)
    parser.add_argument("--config", help="Custom YAML configuration path")
    args = parser.parse_args()

    if shutil.which("ros2") is None:
        parser.exit(1, f"error: ROS 2 is unavailable. Install it from {ROS_INSTALL_URL}\n")
    try:
        command = build_launch_command(load_config(args.config), args.mode)
    except (FileNotFoundError, TypeError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
