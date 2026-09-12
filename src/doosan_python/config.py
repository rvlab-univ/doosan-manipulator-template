"""Type-safe configuration parser for pipeline settings."""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import List, Optional, Union
import yaml

from doosan_python.utils.logger import get_logger

logger = get_logger("config")


@dataclass
class RobotConfig:
    """Robot connection and basic motion defaults."""
    ip: str = "192.168.137.100"
    port: int = 12345
    service_prefix: str = "/dsr_controller2"
    home_pose: List[float] = field(default_factory=lambda: [0.0, 0.0, 90.0, 0.0, 90.0, 0.0])  # deg (Joint angles)
    default_vel: float = 30.0                                                                    # deg/s or mm/s
    default_acc: float = 60.0                                                                    # deg/s^2 or mm/s^2


@dataclass
class CameraConfig:
    """Vision capture parameters."""
    type: str = "realsense"
    width: int = 640
    height: int = 480
    fps: int = 30


@dataclass
class ModelConfig:
    """Detection / AI model parameters."""
    weights_path: str = "weights/best.pt"
    confidence_threshold: float = 0.5
    target_class: str = "target"


@dataclass
class TransformConfig:
    """Extrinsic calibration parameters (Camera -> Robot Base)."""
    cam_to_base_translation: List[float] = field(default_factory=lambda: [300.0, 0.0, 500.0])  # mm
    cam_to_base_rotation: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])         # [Rx, Ry, Rz] in deg


@dataclass
class AppConfig:
    """Root configuration contract."""
    robot: RobotConfig = field(default_factory=RobotConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    transforms: TransformConfig = field(default_factory=TransformConfig)


def load_config(config_path: Optional[Union[str, Path]] = None) -> AppConfig:
    """Load configuration from a YAML file, falling back to defaults if not found.

    Args:
        config_path: Path to YAML config file. If None or non-existent, default values are used.

    Returns:
        Populated AppConfig dataclass.
    """
    if config_path is None:
        config_path = "configs/default.yaml"

    path = Path(config_path)
    if not path.exists():
        logger.warning(f"Config file not found at '{path}'. Falling back to built-in default configuration.")
        return AppConfig()

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f) or {}

        robot_data = raw_data.get("robot", {})
        camera_data = raw_data.get("camera", {})
        model_data = raw_data.get("model", {})
        transforms_data = raw_data.get("transforms", {})

        cfg = AppConfig(
            robot=RobotConfig(**{k: v for k, v in robot_data.items() if hasattr(RobotConfig, k)}),
            camera=CameraConfig(**{k: v for k, v in camera_data.items() if hasattr(CameraConfig, k)}),
            model=ModelConfig(**{k: v for k, v in model_data.items() if hasattr(ModelConfig, k)}),
            transforms=TransformConfig(**{k: v for k, v in transforms_data.items() if hasattr(TransformConfig, k)}),
        )
        logger.info(f"Loaded configuration successfully from '{path}'.")
        return cfg
    except Exception as e:
        logger.error(f"Error reading configuration file '{path}': {e}. Using fallback defaults.")
        return AppConfig()
