#!/usr/bin/env bash
# Source this file to activate Python and ROS 2:
#   source env.sh
#   source env.sh -virtual
#   source env.sh -real

ROS_INSTALL_URL="https://doosanrobotics.github.io/doosan-robotics-ros-manual/jazzy/installation.html"

if [ -n "$ZSH_VERSION" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${(%):-%N}")" && pwd)"
    SETUP_EXT="zsh"
else
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    SETUP_EXT="bash"
fi

if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

ROS_DISTRO="${ROS_DISTRO:-jazzy}"
ROS_SETUP="/opt/ros/$ROS_DISTRO/setup.$SETUP_EXT"
if [ ! -f "$ROS_SETUP" ]; then
    echo "error: ROS 2 $ROS_DISTRO is unavailable. Install it from $ROS_INSTALL_URL"
    return 1 2>/dev/null || exit 1
fi
source "$ROS_SETUP"

DOOSAN_ROS_WS="${DOOSAN_ROS_WS:-$HOME/ros2_ws}"
WORKSPACE_SETUP="$DOOSAN_ROS_WS/install/setup.$SETUP_EXT"
if [ ! -f "$WORKSPACE_SETUP" ]; then
    echo "error: Doosan ROS 2 workspace is unavailable. Install it from $ROS_INSTALL_URL"
    return 1 2>/dev/null || exit 1
fi
source "$WORKSPACE_SETUP"

dsr_launch() {
    case "$1" in
        -real|--real|real)
            python -m doosan_python.launch --mode real "${@:2}"
            ;;
        -virtual|--virtual|virtual)
            python -m doosan_python.launch --mode virtual "${@:2}"
            ;;
        *)
            echo "usage: dsr_launch [-real | -virtual] [--config PATH]"
            return 2
            ;;
    esac
}

case "$1" in
    -real|--real|real|-virtual|--virtual|virtual)
        dsr_launch "$@"
        ;;
    "")
        ;;
    *)
        echo "usage: source env.sh [-real | -virtual]"
        return 2 2>/dev/null || exit 2
        ;;
esac
