"""Gripper hardware interface."""

from doosan_python.utils.logger import get_logger

logger = get_logger("control.gripper")


class Gripper:
    """Interface for robot end-effector / gripper."""

    def __init__(self, port: str = "/dev/ttyUSB0"):
        self.port = port
        logger.info(f"Initialized gripper interface on port: {self.port}")

    def open(self) -> bool:
        """Open the gripper fingers."""
        logger.info("Opening gripper...")
        return True

    def close(self) -> bool:
        """Close the gripper fingers."""
        logger.info("Closing gripper...")
        return True


if __name__ == "__main__":
    gripper = Gripper()
    gripper.open()
    gripper.close()
    logger.info("Gripper standalone test completed.")
