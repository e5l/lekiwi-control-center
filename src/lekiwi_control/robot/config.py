# ABOUTME: Configuration dataclasses for LeKiwi robot
# ABOUTME: Defines robot, camera, and motor configuration parameters

from dataclasses import dataclass, field

from lekiwi_control.cameras.configs import CameraConfig
from lekiwi_control.cameras.opencv.configuration_opencv import Cv2Rotation, OpenCVCameraConfig


@dataclass
class LeKiwiConfig:
    """LeKiwi robot configuration."""

    # Motor bus configuration
    port: str = "/dev/ttyACM0"

    # Safety: limit relative movement distance per command
    max_relative_target: float | dict[str, float] | None = None

    # Torque management
    disable_torque_on_disconnect: bool = True

    # Use degrees for normalization (for backward compatibility)
    use_degrees: bool = False

    # Camera configuration
    cameras: dict[str, CameraConfig] = field(
        default_factory=lambda: {
            "front": OpenCVCameraConfig(
                index_or_path="/dev/video0", rotation=Cv2Rotation.ROTATE_180
            ),
            "wrist": OpenCVCameraConfig(
                index_or_path="/dev/video2", rotation=Cv2Rotation.ROTATE_90
            ),
        }
    )
