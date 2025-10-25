# ABOUTME: Camera configuration classes and enums
# ABOUTME: Defines base configuration for camera devices with color modes and rotation options

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path


class ColorMode(IntEnum):
    """Color mode for camera image output."""
    RGB = 0
    BGR = 1


class Cv2Rotation(IntEnum):
    """OpenCV rotation codes for image transformation."""
    NO_ROTATION = -1  # No rotation
    NONE = -1  # Alias for NO_ROTATION
    ROTATE_90 = 0  # 90 degrees clockwise
    ROTATE_90_CLOCKWISE = 0  # Alias
    ROTATE_180 = 1  # 180 degrees
    ROTATE_270 = 2  # 270 degrees clockwise (90 CCW)
    ROTATE_90_COUNTERCLOCKWISE = 2  # Alias


@dataclass
class CameraConfig:
    """Base configuration class for camera devices.

    All camera-specific configurations should inherit from this class.
    """

    fps: int | None = field(default=None)
    width: int | None = field(default=None)
    height: int | None = field(default=None)

    @classmethod
    def register_subclass(cls, name: str):
        """Decorator to register camera configuration subclasses."""
        def decorator(subclass):
            return subclass
        return decorator
