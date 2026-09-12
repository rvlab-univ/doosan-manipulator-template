#!/usr/bin/env bash
# Doosan Robot (A0912) ROS 2 환경 설정 및 실행 스크립트
#
# [사용법]
#   1. 환경만 로드 (기본, 실행 X):
#      source env.sh
#
#   2. 환경 로드 후 즉시 로봇 실행:
#      source env.sh -real       (실물 로봇: 192.168.137.100)
#      source env.sh -virtual    (가상 시뮬레이션: 127.0.0.1)
#      (직접 실행: ./env.sh -real 도 지원)
#
#   3. 환경 로드 후 언제든 단축 명령어 사용:
#      dsr_launch -real
#      dsr_launch -virtual

# 인자 판별 (-real, -virtual)
LAUNCH_MODE=""
if [ "$1" = "-real" ] || [ "$1" = "--real" ] || [ "$1" = "real" ]; then
    LAUNCH_MODE="-real"
elif [ "$1" = "-virtual" ] || [ "$1" = "--virtual" ] || [ "$1" = "virtual" ]; then
    LAUNCH_MODE="-virtual"
fi

# 0. 인자 없이 직접 실행(./env.sh) 방지 안내
if [ -z "$LAUNCH_MODE" ]; then
    if [ -n "$ZSH_VERSION" ]; then
        if [[ "$ZSH_EVAL_CONTEXT" == "toplevel" ]]; then
            echo "❌ 환경을 현재 터미널에 적용하려면 'source env.sh'로 실행해야 합니다."
            echo ""
            echo "💡 사용법:"
            echo "   - 환경만 로드:          source env.sh"
            echo "   - 실물 로봇 즉시 실행:  source env.sh -real   (또는 ./env.sh -real)"
            echo "   - 가상 로봇 즉시 실행:  source env.sh -virtual (또는 ./env.sh -virtual)"
            return 1 2>/dev/null || exit 1
        fi
    elif [ -n "$BASH_VERSION" ]; then
        if [ "${BASH_SOURCE[0]}" = "$0" ]; then
            echo "❌ 환경을 현재 터미널에 적용하려면 'source env.sh'로 실행해야 합니다."
            echo ""
            echo "💡 사용법:"
            echo "   - 환경만 로드:          source env.sh"
            echo "   - 실물 로봇 즉시 실행:  source env.sh -real   (또는 ./env.sh -real)"
            echo "   - 가상 로봇 즉시 실행:  source env.sh -virtual (또는 ./env.sh -virtual)"
            return 1 2>/dev/null || exit 1
        fi
    fi
fi

# 스크립트 디렉토리 감지
if [ -n "$ZSH_VERSION" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${(%):-%N}")" 2>/dev/null && pwd)"
else
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
fi

# 1. 이미 활성화된 가상환경이 있다면 정리 (중복/충돌 방지)
if type deactivate >/dev/null 2>&1; then
    deactivate
fi

# 2. 가상환경 활성화 (ROS 2 설정 전에 활성화)
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# 3. ROS 2 및 워크스페이스 환경 로드
if [ -n "$ZSH_VERSION" ]; then
    # ZSH 환경
    [ -f "/opt/ros/jazzy/setup.zsh" ] && source /opt/ros/jazzy/setup.zsh
    [ -f "$HOME/ros2_ws/install/setup.zsh" ] && source "$HOME/ros2_ws/install/setup.zsh"
else
    # Bash 환경
    [ -f "/opt/ros/jazzy/setup.bash" ] && source /opt/ros/jazzy/setup.bash
    [ -f "$HOME/ros2_ws/install/setup.bash" ] && source "$HOME/ros2_ws/install/setup.bash"
fi

# 4. 단축 실행 함수 정의
dsr_launch() {
    local target="${1:--real}"
    case "$target" in
        -real|--real|real)
            echo "🤖 Launching Doosan A0912 MoveIt (REAL mode @ 192.168.137.100)..."
            ros2 launch dsr_bringup2 dsr_bringup2_moveit.launch.py mode:=real model:=a0912 host:=192.168.137.100 "${@:2}"
            ;;
        -virtual|--virtual|virtual)
            echo "🎮 Launching Doosan A0912 MoveIt (VIRTUAL mode @ 127.0.0.1)..."
            ros2 launch dsr_bringup2 dsr_bringup2_moveit.launch.py mode:=virtual model:=a0912 host:=127.0.0.1 "${@:2}"
            ;;
        *)
            echo "사용법: dsr_launch [-real | -virtual]"
            ;;
    esac
}
alias launch_robot="dsr_launch"

echo "✅ Environment ready!"
echo "   - Python:    $(which python3 2>/dev/null || which python 2>/dev/null)"
echo "   - ROS 2:     $(which ros2 2>/dev/null || echo 'NOT FOUND')"
echo "   - Shortcuts: 'dsr_launch -real' 또는 'dsr_launch -virtual'"

# 5. 인자로 -real 또는 -virtual이 주어진 경우 즉시 실행
if [ -n "$LAUNCH_MODE" ]; then
    dsr_launch "$LAUNCH_MODE" "${@:2}"
fi
