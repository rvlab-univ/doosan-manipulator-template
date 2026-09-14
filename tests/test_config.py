from pathlib import Path

import pytest

from doosan_python.config import load_config


def test_default_config_contains_only_runtime_settings():
    config = load_config()

    assert config.robot.name == "dsr01"
    assert config.robot.model == "a0912"
    assert config.robot.real_host == "192.168.137.100"
    assert config.robot.virtual_host == "127.0.0.1"
    assert config.robot.port == 12345
    assert config.motion.velocity == 10.0
    assert config.motion.acceleration == 20.0
    assert config.motion.max_relative_delta == 30.0
    assert config.motion.service_timeout_sec == 5.0
    assert config.mock_model.joint_index == 6
    assert config.mock_model.delta_deg == 10.0
    assert config.mock_model.prediction_count == 2


def test_config_rejects_unknown_keys(tmp_path: Path):
    path = tmp_path / "bad.yaml"
    path.write_text("robot:\n  typo: value\n", encoding="utf-8")

    with pytest.raises(ValueError, match="unknown config key: robot.typo"):
        load_config(path)


def test_config_rejects_mock_delta_above_motion_limit(tmp_path: Path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        "motion:\n  max_relative_delta: 5\nmock_model:\n  delta_deg: 10\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="mock_model.delta_deg"):
        load_config(path)


def test_config_rejects_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "missing.yaml")
