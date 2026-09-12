"""Unit tests for core algorithms and configuration pipeline."""

import numpy as np
import pytest

from doosan_python.algorithms.grasp import calculate_grasp_plan
from doosan_python.algorithms.transforms import cam_to_robot_base
from doosan_python.config import load_config, AppConfig
from doosan_python.models.detector import ObjectDetector
from doosan_python.schemas import TargetPose


def test_config_loading():
    """Test loading default configuration and verify fallback contracts."""
    cfg = load_config("configs/default.yaml")
    assert isinstance(cfg, AppConfig)
    assert cfg.robot.port == 12345
    assert cfg.camera.width == 640
    assert cfg.camera.height == 480
    assert len(cfg.robot.home_pose) == 6
    assert len(cfg.transforms.cam_to_base_translation) == 3


def test_cam_to_robot_base_transformation():
    """Test 3D coordinate transformation mathematics."""
    cam_point = np.array([100.0, 50.0, 500.0])
    translation = [300.0, 0.0, 500.0]
    
    # Translation only with identity rotation
    base_point = cam_to_robot_base(cam_point, translation=translation)
    expected = np.array([400.0, 50.0, 1000.0])
    np.testing.assert_allclose(base_point, expected)


def test_grasp_plan_calculation():
    """Test grasp trajectory calculations."""
    target_pos = np.array([400.0, 100.0, 200.0])
    plan = calculate_grasp_plan(target_pos, approach_offset_z=120.0)

    assert isinstance(plan.pick_pose, TargetPose)
    assert plan.pick_pose.position == [400.0, 100.0, 200.0]
    # Approach and retreat should have offset added on Z axis
    assert plan.approach_pose.position == [400.0, 100.0, 320.0]
    assert plan.retreat_pose.position == [400.0, 100.0, 320.0]


def test_object_detector_infer():
    """Test detector inference on synthetic image input."""
    detector = ObjectDetector(weights_path="weights/best.pt", conf_thresh=0.5)
    dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
    results = detector.infer(dummy_img, target_label="target_box")

    assert len(results) > 0
    assert results[0].label == "target_box"
    assert results[0].confidence >= 0.5
    assert results[0].point_3d_cam is not None
