# ⚙️ Configuration Guide (설정 가이드)

이 문서는 `configs/default.yaml`의 모든 설정 항목이 코드베이스의 어떤 파이썬 파일과 클래스에 연결되어 동작하는지 설명합니다.

---

## 🗺️ 설정 항목과 파이썬 모듈 매핑 요약

| 설정 항목 (Key) | 매핑 클래스 / 함수 | 소스 코드 파일 | 기본값 | 단위 / 설명 |
| :--- | :--- | :--- | :--- | :--- |
| `robot.ip` | `DoosanRobot.__init__` | [`control/robot.py`](file:///home/ahrism/workspace/doosan_python/src/doosan_python/control/robot.py) | `"192.168.137.100"` | 로봇 제어기 IP 주소 |
| `robot.port` | `DoosanRobot.__init__` | [`control/robot.py`](file:///home/ahrism/workspace/doosan_python/src/doosan_python/control/robot.py) | `12345` | 로봇 제어 포트 |
| `robot.service_prefix` | `DoosanRobot.__init__` | [`control/robot.py`](file:///home/ahrism/workspace/doosan_python/src/doosan_python/control/robot.py) | `"/dsr_controller2"` | ROS 2 서비스 접두어 |
| `robot.home_pose` | `DoosanRobot.move_home` | [`control/robot.py`](file:///home/ahrism/workspace/doosan_python/src/doosan_python/control/robot.py) | `[0, 0, 90, 0, 90, 0]` | 6개 관절 초기 각도 (deg) |
| `robot.default_vel` | `DoosanRobot.move_j/l` | [`control/robot.py`](file:///home/ahrism/workspace/doosan_python/src/doosan_python/control/robot.py) | `30.0` | 기본 속도 (deg/s, mm/s) |
| `robot.default_acc` | `DoosanRobot.move_j/l` | [`control/robot.py`](file:///home/ahrism/workspace/doosan_python/src/doosan_python/control/robot.py) | `60.0` | 기본 가속도 (deg/s², mm/s²) |
| `camera.type` | `CameraStreamer.__init__`| [`models/camera.py`](file:///home/ahrism/workspace/doosan_python/src/doosan_python/models/camera.py) | `"realsense"` | 카메라 드라이버 타입 |
| `camera.width` | `CameraStreamer.__init__`| [`models/camera.py`](file:///home/ahrism/workspace/doosan_python/src/doosan_python/models/camera.py) | `640` | 이미지 가로 해상도 (px) |
| `camera.height` | `CameraStreamer.__init__`| [`models/camera.py`](file:///home/ahrism/workspace/doosan_python/src/doosan_python/models/camera.py) | `480` | 이미지 세로 해상도 (px) |
| `camera.fps` | `CameraStreamer.__init__`| [`models/camera.py`](file:///home/ahrism/workspace/doosan_python/src/doosan_python/models/camera.py) | `30` | 카메라 프레임레이트 (Hz) |
| `model.weights_path` | `ObjectDetector.__init__`| [`models/detector.py`](file:///home/ahrism/workspace/doosan_python/src/doosan_python/models/detector.py) | `"weights/best.pt"` | 딥러닝 모델 가중치 경로 |
| `model.confidence_threshold`| `ObjectDetector.__init__`| [`models/detector.py`](file:///home/ahrism/workspace/doosan_python/src/doosan_python/models/detector.py) | `0.5` | 인식 확신도 임계값 (0.0~1.0) |
| `model.target_class` | `detector.infer` | [`main.py`](file:///home/ahrism/workspace/doosan_python/src/doosan_python/main.py) | `"target_box"` | 검출 및 조작 대상 라벨명 |
| `transforms.cam_to_base_translation`| `cam_to_robot_base` | [`algorithms/transforms.py`](file:///home/ahrism/workspace/doosan_python/src/doosan_python/algorithms/transforms.py)| `[300.0, 0.0, 500.0]` | 카메라→베이스 평행이동 (mm) |
| `transforms.cam_to_base_rotation`| `cam_to_robot_base` | [`algorithms/transforms.py`](file:///home/ahrism/workspace/doosan_python/src/doosan_python/algorithms/transforms.py)| `[0.0, 0.0, 0.0]` | 카메라→베이스 회전 오일러각 (deg) |

---

## 🔍 상세 파라미터 설명

### 1. `robot` 섹션 (로봇 제어기 설정)
두산 협동로봇 제어기와의 통신 및 안전 관련 기본값을 지정합니다.
* **`ip` (문자열)**: 실제 Doosan 로봇 컨트롤러의 네트워크 IP입니다. 
  * 실기기 기본 설정: `"192.168.137.100"`
  * 가상 에뮬레이터/시뮬레이션: `"127.0.0.1"`
* **`service_prefix` (문자열)**: ROS 2 환경에서 두산 드라이버가 게시하는 서비스 네임스페이스입니다. 기본값은 `"/dsr_controller2"`입니다.
* **`home_pose` (실수 리스트 [6])**: 로봇이 작업 시작 전 대기하거나 작업 후 복귀할 6개 관절 각도(단위: degree)입니다.
* **`default_vel` / `default_acc` (실수)**: 안전을 고려한 기본 동작 속도 및 가속도입니다.

### 2. `camera` 섹션 (비전 센서 설정)
RGB-D 카메라(`realsense-python`) 스트리밍 파라미터입니다.
* **`type` (문자열)**: 현재 지원 드라이버는 `"realsense"`이며, 하드웨어가 감지되지 않으면 자동으로 모의 스트림(Mock Frame)으로 전환됩니다.
* **`width` / `height` / `fps` (정수)**: 카메라 해상도 및 초당 프레임 수입니다.

### 3. `model` 섹션 (인공지능 모델 설정)
객체 검출(Object Detection) 및 3D 포즈 추정 모델 설정입니다.
* **`weights_path` (문자열)**: YOLO, PyTorch 등의 가중치 파일 경로입니다.
* **`confidence_threshold` (실수)**: 바운딩 박스를 유효한 물체로 필터링할 최소 확률값입니다.
* **`target_class` (문자열)**: 로봇이 파지(Grasp)해야 할 타겟 클래스 이름입니다.

### 4. `transforms` 섹션 (좌표계 변환 행렬)
Eye-to-Hand(외부 고정 카메라) 환경에서 카메라 3D 좌표계를 로봇 베이스 3D 좌표계로 변환하기 위한 캘리브레이션 값입니다.
* **`cam_to_base_translation`**: 카메라 렌즈 기준 로봇 바닥 베이스 중심까지의 상대 거리 [X, Y, Z] (mm).
* **`cam_to_base_rotation`**: 카메라와 로봇 좌표계 간의 회전 각도 [Rx, Ry, Rz] (deg).

---

## 💻 코드에서 설정 로드 및 사용 방법

파이썬 코드에서는 [`src/doosan_python/config.py`](file:///home/ahrism/workspace/doosan_python/src/doosan_python/config.py)의 `load_config`를 통해 타입 힌트와 자동 완성이 지원되는 `AppConfig` 객체로 로드합니다.

```python
from doosan_python.config import load_config

# 1. 설정 로드 (경로 생략 시 configs/default.yaml 사용)
cfg = load_config("configs/default.yaml")

# 2. 각 모듈에 주입
robot = DoosanRobot(ip=cfg.robot.ip, port=cfg.robot.port)
cam = CameraStreamer(width=cfg.camera.width, height=cfg.camera.height, fps=cfg.camera.fps)
detector = ObjectDetector(weights_path=cfg.model.weights_path, conf_thresh=cfg.model.confidence_threshold)
```

CLI 실행 시 다른 설정 파일을 지정할 수 있습니다:
```bash
python -m doosan_python.main --config configs/simulation.yaml
```
