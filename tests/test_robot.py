import math

import pytest

from doosan_python.control import robot


def test_joint_delta_validation_accepts_six_bounded_numbers():
    assert robot.validate_joint_deltas([0, 0, 0, 0, 0, 10], 30) == [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        10.0,
    ]


@pytest.mark.parametrize(
    "deltas",
    ([0] * 5, [0, 0, 0, 0, 0, 31], [0, 0, 0, 0, 0, math.nan]),
)
def test_joint_delta_validation_rejects_unsafe_commands(deltas):
    with pytest.raises(ValueError):
        robot.validate_joint_deltas(deltas, 30)


def test_missing_ros_error_links_official_installation(monkeypatch):
    monkeypatch.setattr(robot, "HAS_ROS", False)

    with pytest.raises(RuntimeError, match="doosanrobotics.github.io/.*/installation.html"):
        robot.require_ros()
