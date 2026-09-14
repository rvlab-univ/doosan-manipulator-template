from doosan_python.config import load_config
from doosan_python.launch import build_launch_command


def test_virtual_launch_uses_virtual_controller():
    command = build_launch_command(load_config(), "virtual")

    assert command == [
        "ros2",
        "launch",
        "dsr_bringup2",
        "dsr_bringup2_moveit.launch.py",
        "mode:=virtual",
        "model:=a0912",
        "host:=127.0.0.1",
        "port:=12345",
        "name:=dsr01",
    ]


def test_real_launch_uses_real_controller():
    command = build_launch_command(load_config(), "real")

    assert "mode:=real" in command
    assert "host:=192.168.137.100" in command
