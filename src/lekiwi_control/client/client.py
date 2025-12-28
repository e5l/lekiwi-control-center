# ABOUTME: Python client for interacting with LeKiwi Control Center API
# ABOUTME: Provides a simple interface with automatic value clamping for motor positions

from typing import Any

import requests


class LeKiwiClient:
    """Simple client for interacting with LeKiwi Control Center API.

    Automatically clamps motor values to safe ranges before sending commands.
    """

    # Motor position limits (measured values)
    MOTOR_LIMITS = {
        "arm_shoulder_pan": (-100.0, 100.0),
        "arm_shoulder_lift": (-100.0, 100.0),
        "arm_elbow_flex": (-95.0, 99.0),
        "arm_wrist_flex": (-60.0, 60.0),
        "arm_wrist_roll": (-100.0, 100.0),
        "arm_gripper": (0.0, 100.0),
    }

    def __init__(self, base_url: str = "http://pi.local:8000"):
        """Initialize the LeKiwi client.

        Args:
            base_url: Base URL of the LeKiwi Control Center API
        """
        self.base_url = base_url.rstrip("/")

    @classmethod
    def _clamp_value(cls, value: float, motor_name: str) -> float:
        """Clamp a motor value to its safe range.

        Args:
            value: The value to clamp
            motor_name: Name of the motor (e.g., 'arm_shoulder_pan')

        Returns:
            Clamped value within the motor's safe range
        """
        if motor_name not in cls.MOTOR_LIMITS:
            return value

        min_val, max_val = cls.MOTOR_LIMITS[motor_name]
        return max(min_val, min(max_val, value))

    def health_check(self) -> dict[str, Any]:
        """Check if the server is healthy."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def get_status(self) -> dict[str, Any]:
        """Get robot connection status."""
        response = requests.get(f"{self.base_url}/status")
        response.raise_for_status()
        return response.json()

    def connect(self) -> dict[str, Any]:
        """Connect to the robot."""
        response = requests.post(f"{self.base_url}/robot/connect")
        response.raise_for_status()
        return response.json()

    def disconnect(self) -> dict[str, Any]:
        """Disconnect from the robot."""
        response = requests.post(f"{self.base_url}/robot/disconnect")
        response.raise_for_status()
        return response.json()

    def get_motors_state(self) -> dict[str, Any]:
        """Get current motor positions and velocities."""
        response = requests.get(f"{self.base_url}/motors/state")
        response.raise_for_status()
        return response.json()

    def set_arm_position(
        self,
        shoulder_pan: float,
        shoulder_lift: float,
        elbow_flex: float,
        wrist_flex: float,
        wrist_roll: float,
        gripper: float,
    ) -> dict[str, Any]:
        """Set arm motor positions with automatic value clamping.

        Values are automatically clamped to safe ranges:
        - shoulder_pan: -100.0 to 100.0
        - shoulder_lift: -100.0 to 100.0
        - elbow_flex: -95.0 to 99.0
        - wrist_flex: -60.0 to 60.0
        - wrist_roll: -100.0 to 100.0
        - gripper: 0.0 to 100.0

        Args:
            shoulder_pan: Shoulder rotation position
            shoulder_lift: Shoulder elevation position
            elbow_flex: Elbow joint position
            wrist_flex: Wrist pitch position
            wrist_roll: Wrist rotation position
            gripper: Gripper position (0=open, 100=closed)

        Returns:
            API response with success status
        """
        payload = {
            "arm_shoulder_pan": self._clamp_value(shoulder_pan, "arm_shoulder_pan"),
            "arm_shoulder_lift": self._clamp_value(shoulder_lift, "arm_shoulder_lift"),
            "arm_elbow_flex": self._clamp_value(elbow_flex, "arm_elbow_flex"),
            "arm_wrist_flex": self._clamp_value(wrist_flex, "arm_wrist_flex"),
            "arm_wrist_roll": self._clamp_value(wrist_roll, "arm_wrist_roll"),
            "arm_gripper": self._clamp_value(gripper, "arm_gripper"),
        }
        response = requests.post(f"{self.base_url}/motors/arm/position", json=payload)
        response.raise_for_status()
        return response.json()

    def set_base_velocity(self, x: float = 0.0, y: float = 0.0, theta: float = 0.0) -> dict[str, Any]:
        """Set base velocities.

        Args:
            x: Forward/backward velocity (m/s)
            y: Lateral velocity (m/s)
            theta: Rotational velocity (deg/s)

        Returns:
            API response with success status
        """
        payload = {"x": x, "y": y, "theta": theta}
        response = requests.post(f"{self.base_url}/motors/base/velocity", json=payload)
        response.raise_for_status()
        return response.json()

    def stop(self) -> dict[str, Any]:
        """Emergency stop (base motors only)."""
        response = requests.post(f"{self.base_url}/motors/stop")
        response.raise_for_status()
        return response.json()

    def list_cameras(self) -> dict[str, Any]:
        """List available cameras."""
        response = requests.get(f"{self.base_url}/cameras/list")
        response.raise_for_status()
        return response.json()

    def get_camera_frame(self, camera_id: str, save_path: str | None = None) -> bytes:
        """Get a single frame from camera.

        Args:
            camera_id: Camera identifier (e.g., 'front', 'wrist')
            save_path: Optional path to save the image to disk

        Returns:
            Raw JPEG image bytes
        """
        response = requests.get(f"{self.base_url}/cameras/{camera_id}/frame")
        response.raise_for_status()

        if save_path:
            with open(save_path, "wb") as f:
                f.write(response.content)

        return response.content
