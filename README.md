# Doosan ROS 2 Python Research Template

두산 협동로봇에서 **모델 출력 → 명령 검증 → ROS 2 관절 제어** 흐름을
시작하기 위한 최소 Python 보일러플레이트입니다. 기본 모델은 6번 관절에
`+10°`, `-10°` 상대 이동을 차례로 예측하며, 실제 이동은 명시적으로
승인한 경우에만 실행됩니다.

## 요구사항

- Ubuntu 24.04
- Python 3.12 이상과 [uv](https://docs.astral.sh/uv/)
- ROS 2 Jazzy와 Doosan `doosan-robot2`
- virtual 모드에서는 Docker 기반 DRCF emulator

ROS와 Doosan 패키지는 [공식 설치 가이드](https://doosanrobotics.github.io/doosan-robotics-ros-manual/jazzy/installation.html)를
따라 `~/ros2_ws`에 설치합니다. 다른 workspace를 사용한다면
`DOOSAN_ROS_WS=/path/to/workspace`를 지정하세요.

```bash
uv sync --all-extras
uv run pytest
```

## 설정

기본 설정은 [`src/doosan_python/default.yaml`](src/doosan_python/default.yaml)에
있습니다. 각 항목의 사용 위치와 단위를 파일 안의 주석으로 설명합니다.
별도 설정은 모든 CLI의 `--config PATH`로 전달할 수 있습니다.

- `robot`: ROS namespace, 로봇 모델, real/virtual host, controller port
- `motion`: 속도, 가속도, 한 번에 허용할 최대 상대 이동량, service timeout
- `mock_model`: 예제 모델이 움직일 관절, 각도, 예측 횟수

알 수 없는 키, 잘못된 값 또는 없는 설정 파일은 오류로 처리됩니다.

## virtual/real 실행

첫 번째 터미널에서 ROS controller와 MoveIt을 시작합니다. `-virtual`은
Doosan의 `mode:=virtual`과 localhost를 사용해 emulator를 실행합니다.

```bash
# Virtual controller
source env.sh -virtual

# 실제 A0912 controller
source env.sh -real
```

launch 인자는 설정의 `name`, `model`, `host`, `port`에서 생성됩니다.
자세한 모드 차이는 [공식 operation modes 문서](https://doosanrobotics.github.io/doosan-robotics-ros-manual/jazzy/tutorials/operation_modes.html)를
참고하세요.

두 번째 터미널에서 같은 환경을 불러오고 예제를 실행합니다.

```bash
source env.sh

# 모델 예측만 출력
uv run doosan-main

# 예측한 +10°/-10° 상대 이동을 실제 controller에 전송
uv run doosan-main --execute

# 고정 왕복 동작 미리보기 또는 실행
uv run doosan-adjust
uv run doosan-adjust --execute

# 관절 번호와 상대 각도를 직접 입력해 이동
uv run doosan-jog
```

`doosan-main`과 `doosan-adjust`는 `--execute`가 없으면 움직이지 않습니다.
`doosan-jog`는 사용자가 입력한 각 명령을 즉시 실행하지만
`motion.max_relative_delta`를 넘는 값은 거부합니다.

## 실제 모델 연결

[`MockPolicy.predict()`](src/doosan_python/models/policy.py)는 다음 계약을
보여주는 최소 예제입니다.

```python
def predict(current_joints: Sequence[float]) -> list[float]:
    # input: 현재 6개 관절각 [deg]
    # output: 다음 6개 상대 관절 이동량 [deg]
    ...
```

실제 모델로 교체할 때 이 입출력 계약만 유지하세요. 모델은 ROS나 하드웨어를
직접 호출하지 않습니다. 모든 출력은 공통 제어 계층에서 길이, 유한값,
최대 이동량을 검사한 뒤 전송됩니다.

## 구조

```text
src/doosan_python/
├── config.py             # 주석 있는 YAML을 엄격하게 로드·검증
├── default.yaml          # 실험자가 조정하는 단일 기본 설정
├── launch.py             # 설정을 공식 dsr_bringup2 launch 인자로 변환
├── main.py               # mock 모델 → 검증 → 선택적 실행
├── interactive_jog.py    # 대화형 상대 관절 이동
├── adjust_joint.py       # 한 번의 관절 왕복 예제
├── control/robot.py      # 세 CLI가 공유하는 ROS 2 service adapter
└── models/policy.py      # 실제 모델로 교체할 최소 mock 정책
```

## License

[MIT](LICENSE)
