"""Strict configuration loading for the robot examples."""

import math
from dataclasses import dataclass, fields
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class RobotConfig:
    name: str = "dsr01"
    model: str = "a0912"
    real_host: str = "192.168.137.100"
    virtual_host: str = "127.0.0.1"
    port: int = 12345


@dataclass(frozen=True)
class MotionConfig:
    velocity: float = 10.0
    acceleration: float = 20.0
    max_relative_delta: float = 30.0
    service_timeout_sec: float = 5.0


@dataclass(frozen=True)
class MockModelConfig:
    joint_index: int = 6
    delta_deg: float = 10.0
    prediction_count: int = 2


@dataclass(frozen=True)
class AppConfig:
    robot: RobotConfig
    motion: MotionConfig
    mock_model: MockModelConfig


def _section(cls: type, name: str, raw: Any):
    if not isinstance(raw, dict):
        raise TypeError(f"config section {name} must be a mapping")
    allowed = {field.name for field in fields(cls)}
    unknown = set(raw) - allowed
    if unknown:
        raise ValueError(f"unknown config key: {name}.{min(unknown)}")
    return cls(**raw)


def _positive_number(value: Any, key: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{key} must be a positive number")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{key} must be a positive number")
    return number


def _validate(config: AppConfig) -> AppConfig:
    for key, value in (
        ("robot.name", config.robot.name),
        ("robot.model", config.robot.model),
        ("robot.real_host", config.robot.real_host),
        ("robot.virtual_host", config.robot.virtual_host),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-empty string")
    if (
        isinstance(config.robot.port, bool)
        or not isinstance(config.robot.port, int)
        or not 1 <= config.robot.port <= 65535
    ):
        raise ValueError("robot.port must be between 1 and 65535")

    _positive_number(config.motion.velocity, "motion.velocity")
    _positive_number(config.motion.acceleration, "motion.acceleration")
    limit = _positive_number(
        config.motion.max_relative_delta, "motion.max_relative_delta"
    )
    _positive_number(config.motion.service_timeout_sec, "motion.service_timeout_sec")

    if (
        isinstance(config.mock_model.joint_index, bool)
        or not isinstance(config.mock_model.joint_index, int)
        or not 1 <= config.mock_model.joint_index <= 6
    ):
        raise ValueError("mock_model.joint_index must be between 1 and 6")
    delta = _positive_number(config.mock_model.delta_deg, "mock_model.delta_deg")
    if delta > limit:
        raise ValueError(
            "mock_model.delta_deg must not exceed motion.max_relative_delta"
        )
    if (
        isinstance(config.mock_model.prediction_count, bool)
        or not isinstance(config.mock_model.prediction_count, int)
        or config.mock_model.prediction_count < 1
    ):
        raise ValueError("mock_model.prediction_count must be a positive integer")
    return config


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """Load and validate YAML; use the packaged default when no path is given."""
    if config_path is None:
        text = files("doosan_python").joinpath("default.yaml").read_text(encoding="utf-8")
    else:
        path = Path(config_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        text = path.read_text(encoding="utf-8")

    raw = yaml.safe_load(text) or {}
    if not isinstance(raw, dict):
        raise TypeError("config root must be a mapping")
    allowed = {"robot", "motion", "mock_model"}
    unknown = set(raw) - allowed
    if unknown:
        raise ValueError(f"unknown config key: {min(unknown)}")

    return _validate(
        AppConfig(
            robot=_section(RobotConfig, "robot", raw.get("robot", {})),
            motion=_section(MotionConfig, "motion", raw.get("motion", {})),
            mock_model=_section(
                MockModelConfig, "mock_model", raw.get("mock_model", {})
            ),
        )
    )
