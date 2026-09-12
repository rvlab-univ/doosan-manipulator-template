"""Model inference layer for object detection and pose estimation."""

from typing import List, Optional
import numpy as np

from doosan_python.schemas import DetectionResult
from doosan_python.utils.logger import get_logger

logger = get_logger("models.detector")


class ObjectDetector:
    """Wrapper for AI/Vision model inference (e.g. YOLO, Mask R-CNN, etc.)."""

    def __init__(self, weights_path: str = "weights/best.pt", conf_thresh: float = 0.5):
        self.weights_path = weights_path
        self.conf_thresh = conf_thresh
        logger.info(f"Initialized ObjectDetector with weights='{self.weights_path}', conf_thresh={self.conf_thresh}")

    def infer(
        self,
        color_image: np.ndarray,
        depth_image: Optional[np.ndarray] = None,
        target_label: Optional[str] = None,
    ) -> List[DetectionResult]:
        """Perform inference on input frames and return structured detections."""
        if color_image is None:
            logger.warning("Empty color image passed to detector. Skipping inference.")
            return []

        # Mock detection result for prototyping and baseline verification
        logger.debug(f"Running inference (target_label={target_label})...")
        results = [
            DetectionResult(
                label=target_label or "target_object",
                confidence=0.92,
                bbox=[100, 120, 200, 250],
                point_3d_cam=np.array([120.0, -50.0, 650.0]),  # mm in camera coordinate
            )
        ]
        logger.info(f"Detector found {len(results)} object(s). Primary: {results[0].label} (conf: {results[0].confidence:.2f})")
        return results


if __name__ == "__main__":
    detector = ObjectDetector()
    dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = detector.infer(dummy_img, target_label="can")
    logger.info(f"Detections output: {detections}")
    logger.info("ObjectDetector standalone test completed.")
