"""Pure mathematical and geometrical transformations."""

from typing import Optional, Union, Sequence
import numpy as np

from doosan_python.utils.logger import get_logger

logger = get_logger("algorithms.transforms")


def cam_to_robot_base(
    point_cam: np.ndarray,
    translation: Optional[Union[np.ndarray, Sequence[float]]] = None,
    rotation_matrix: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Transform a 3D point from camera frame to robot base frame.

    Formula: P_base = R * P_cam + T

    Args:
        point_cam: [X, Y, Z] coordinate array in camera frame (mm).
        translation: [Tx, Ty, Tz] offset in mm. Defaults to [300.0, 0.0, 500.0].
        rotation_matrix: 3x3 rotation matrix. Defaults to Identity matrix.

    Returns:
        Transformed 3D point in robot base coordinate frame (mm).
    """
    if point_cam is None:
        raise ValueError("point_cam cannot be None")

    t = np.asarray(translation if translation is not None else [300.0, 0.0, 500.0], dtype=float)
    r = np.asarray(rotation_matrix if rotation_matrix is not None else np.eye(3), dtype=float)

    point_base = r @ np.asarray(point_cam, dtype=float) + t
    logger.debug(f"Transformed point: cam={point_cam} -> base={point_base}")
    return point_base


if __name__ == "__main__":
    test_pt = np.array([10.0, 20.0, 500.0])
    res = cam_to_robot_base(test_pt)
    logger.info(f"Transformed base point: {res}")
    logger.info("Transforms standalone test completed.")
