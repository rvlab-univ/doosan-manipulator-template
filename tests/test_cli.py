import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "module",
    (
        "doosan_python.main",
        "doosan_python.interactive_jog",
        "doosan_python.adjust_joint",
        "doosan_python.launch",
    ),
)
def test_cli_help_does_not_require_ros(module):
    result = subprocess.run(
        [sys.executable, "-m", module, "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_main_without_ros_points_to_installation():
    result = subprocess.run(
        [sys.executable, "-m", "doosan_python.main"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "doosanrobotics.github.io" in result.stderr
    assert "installation.html" in result.stderr


def test_env_script_without_ros_points_to_installation():
    root = Path(__file__).parents[1]
    result = subprocess.run(
        ["bash", "-c", "ROS_DISTRO=missing source env.sh -virtual"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "doosanrobotics.github.io" in result.stdout + result.stderr
    assert "installation.html" in result.stdout + result.stderr


def test_main_reports_invalid_config_without_traceback(tmp_path):
    config = tmp_path / "bad.yaml"
    config.write_text("robot: []\n", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "doosan_python.main",
            "--config",
            str(config),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "error: config section robot must be a mapping" in result.stderr
    assert "Traceback" not in result.stderr
