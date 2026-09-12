"""Camera capture interface utilizing rvlab-univ/realsense-python."""

import threading
import time
from typing import Optional, Tuple
import numpy as np

from doosan_python.utils.logger import get_logger

logger = get_logger("models.camera")

try:
    import realsense_capture.camera as rs_cam
    from realsense_capture.camera import Camera, Frames
    HAS_REALSENSE = True
except ImportError:
    HAS_REALSENSE = False


class CameraStreamer:
    """Camera streamer wrapping realsense_capture with fallback and threaded buffering."""

    def __init__(self, width: int = 640, height: int = 480, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps

        self._camera: Optional[Camera] = None
        self._running = False
        self._lock = threading.Lock()
        self._latest_color: Optional[np.ndarray] = None
        self._latest_depth: Optional[np.ndarray] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start camera streaming. Falls back to mock generator if device not found."""
        self._running = True

        if HAS_REALSENSE:
            try:
                self._camera = rs_cam.start("color", "depth", width=self.width, height=self.height, fps=self.fps)
                logger.info("RealSense hardware camera stream started successfully.")
            except Exception as e:
                logger.warning(f"Failed to open RealSense device ({e}). Falling back to synthetic mock frames.")
                self._camera = None
        else:
            logger.info("realsense_capture library not found. Operating in mock camera mode.")

        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()

    def _update_loop(self) -> None:
        """Background thread loop: grab real frames or mock data."""
        while self._running:
            if self._camera is not None:
                try:
                    frames: Frames = self._camera.read()
                    color_frame = frames.rgb
                    depth_frame = frames.depth
                except Exception as e:
                    logger.debug(f"Frame read exception: {e}")
                    time.sleep(0.01)
                    continue
            else:
                # Mock frames when hardware is not connected
                color_frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                depth_frame = np.zeros((self.height, self.width), dtype=np.uint16)
                time.sleep(1.0 / self.fps)

            with self._lock:
                self._latest_color = color_frame
                self._latest_depth = depth_frame

    def get_latest_frame(self, timeout: float = 2.0) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Retrieve the most recent (color, depth) frame pair, waiting if necessary."""
        start_t = time.time()
        while time.time() - start_t < timeout:
            with self._lock:
                if self._latest_color is not None:
                    return self._latest_color, self._latest_depth
            time.sleep(0.01)

        with self._lock:
            return self._latest_color, self._latest_depth

    def stop(self) -> None:
        """Stop capture loop and release camera resource."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        if self._camera is not None:
            try:
                self._camera.stop()
            except Exception as e:
                logger.debug(f"Error during camera stop: {e}")
            self._camera = None

        logger.info("Camera streamer stopped.")


if __name__ == "__main__":
    cam = CameraStreamer()
    cam.start()
    c, d = cam.get_latest_frame()
    logger.info(f"Color shape: {c.shape if c is not None else None}")
    logger.info(f"Depth shape: {d.shape if d is not None else None}")
    cam.stop()
    logger.info("CameraStreamer standalone test completed.")
