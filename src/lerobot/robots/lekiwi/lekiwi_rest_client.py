# ABOUTME: LeRobot Robot adapter for the REST-based LeKiwiClient
# ABOUTME: Enables SmolVLA policy execution via HTTP API instead of direct motor control

import logging
from functools import cached_property
from io import BytesIO
from typing import Any

import numpy as np
from PIL import Image

from lerobot.motors import MotorCalibration
from lerobot.utils.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError

from lekiwi_control.client import LeKiwiClient

from ..robot import Robot
from .config_lekiwi import LeKiwiConfig

logger = logging.getLogger(__name__)


class LeKiwiRestClient(Robot):
    """
    LeRobot Robot adapter for controlling LeKiwi via REST API.

    This adapter wraps the simple LeKiwiClient (HTTP client) to provide
    the full Robot interface needed by LeRobot policies like SmolVLA.

    Unlike the direct LeKiwi class which controls motors via serial bus,
    this class sends commands over HTTP to the LeKiwi Control Center API
    server running on the robot.
    """

    config_class = LeKiwiConfig
    name = "lekiwi_rest"

    def __init__(self, config: LeKiwiConfig, base_url: str = "http://pi.local:8000"):
        """Initialize the REST client adapter.

        Args:
            config: LeKiwi configuration (used for camera specs, feature definitions)
            base_url: Base URL of the LeKiwi Control Center API server
        """
        super().__init__(config)
        self.config = config
        self.base_url = base_url
        self.client = LeKiwiClient(base_url)
        self._connected = False
        self._camera_names = list(config.cameras.keys())

    @property
    def _state_ft(self) -> dict[str, type]:
        """Define state feature structure (arm positions + base velocities)."""
        return dict.fromkeys(
            (
                "arm_shoulder_pan.pos",
                "arm_shoulder_lift.pos",
                "arm_elbow_flex.pos",
                "arm_wrist_flex.pos",
                "arm_wrist_roll.pos",
                "arm_gripper.pos",
                "x.vel",
                "y.vel",
                "theta.vel",
            ),
            float,
        )

    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        """Define camera feature structure from config."""
        return {
            cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3)
            for cam in self._camera_names
        }

    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        """Observation structure: state features + camera images."""
        return {**self._state_ft, **self._cameras_ft}

    @cached_property
    def action_features(self) -> dict[str, type]:
        """Action structure: same as state features (positions + velocities)."""
        return self._state_ft

    @property
    def is_connected(self) -> bool:
        """Check if connected to the robot via API."""
        if not self._connected:
            return False

        try:
            status = self.client.get_status()
            return status.get("connected", False)
        except Exception as e:
            logger.warning(f"Connection check failed: {e}")
            return False

    def connect(self, calibrate: bool = True) -> None:
        """Connect to the robot via REST API.

        Args:
            calibrate: Ignored for REST client (calibration handled by server)
        """
        if self._connected:
            raise DeviceAlreadyConnectedError(f"{self} already connected")

        try:
            # Check server health
            health = self.client.health_check()
            logger.info(f"Server health: {health}")

            # Connect to robot hardware via API
            result = self.client.connect()
            logger.info(f"Robot connection result: {result}")

            self._connected = True
            logger.info(f"{self} connected via REST API at {self.base_url}")

        except Exception as e:
            logger.error(f"Failed to connect to {self.base_url}: {e}")
            raise DeviceNotConnectedError(f"Could not connect to {self.base_url}: {e}")

    @property
    def is_calibrated(self) -> bool:
        """Check calibration status via API.

        For REST client, we assume the server handles calibration.
        """
        if not self._connected:
            return False

        try:
            status = self.client.get_status()
            return status.get("calibrated", True)  # Assume calibrated if not specified
        except Exception:
            return False

    def calibrate(self) -> None:
        """Calibration not supported via REST API.

        Calibration must be performed on the server side before connecting.
        """
        logger.warning("Calibration not supported via REST client. Please calibrate on the robot server.")

    def configure(self) -> None:
        """Configuration handled by the server, no-op for REST client."""
        pass

    def get_observation(self) -> dict[str, Any]:
        """Get current observation from robot via API.

        Returns:
            dict with structure matching observation_features:
                - arm_*.pos: float (6 arm joint positions)
                - *.vel: float (3 base velocities)
                - camera_name: np.ndarray (H, W, 3) for each camera
        """
        import base64
        import time

        t_start = time.time()

        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected")

        # Get complete observation in one API call (3x faster!)
        t0 = time.time()
        full_obs = self.client.get_full_observation()
        t_api = time.time() - t0
        print(f"  get_full_observation API call: {t_api:.3f}s")

        obs_dict = {}

        # Extract arm positions
        arm_pos = full_obs.get("arm_motors", {})
        obs_dict.update({f"{k}.pos": v for k, v in arm_pos.items()})

        # Extract base velocities
        base_vel = full_obs.get("base_velocities", {})
        obs_dict.update({f"{k}.vel": v for k, v in base_vel.items()})

        # Decode camera frames from base64 JPEG
        cameras = full_obs.get("cameras", {})
        for cam_name in self._camera_names:
            try:
                # Decode base64 to JPEG bytes
                t0 = time.time()
                jpeg_base64 = cameras[cam_name]
                jpeg_bytes = base64.b64decode(jpeg_base64)
                t_b64 = time.time() - t0
                print(f"  base64 decode({cam_name}): {t_b64:.3f}s ({len(jpeg_bytes)} bytes)")

                # Convert JPEG to numpy array
                t0 = time.time()
                image = Image.open(BytesIO(jpeg_bytes))
                image_array = np.array(image)
                t_decode = time.time() - t0
                print(f"  JPEG decode({cam_name}): {t_decode:.3f}s")

                # Ensure RGB format (API returns BGR, convert if needed)
                if image_array.shape[2] == 3:  # Has 3 channels
                    cam_config = self.config.cameras[cam_name]
                    if hasattr(cam_config, "color_mode") and cam_config.color_mode == "bgr":
                        # Convert BGR to RGB
                        image_array = image_array[:, :, ::-1]

                obs_dict[cam_name] = image_array

            except Exception as e:
                logger.error(f"Failed to decode frame from {cam_name}: {e}")
                # Return blank frame as fallback
                h, w, c = self._cameras_ft[cam_name]
                obs_dict[cam_name] = np.zeros((h, w, c), dtype=np.uint8)
                logger.warning(f"Using blank frame for {cam_name}: shape=({h}, {w}, {c})")

        t_total = time.time() - t_start
        print(f"  get_observation TOTAL: {t_total:.3f}s")
        return obs_dict

    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Send action to robot via API.

        Args:
            action: dict with structure matching action_features:
                - arm_*.pos: float (6 arm joint positions)
                - *.vel: float (3 base velocities)

        Returns:
            The action actually sent (same as input, clamping handled by client)
        """
        import time
        t_start = time.time()

        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected")

        # Extract arm positions (remove .pos suffix for API call)
        arm_positions = {
            k.replace(".pos", ""): v
            for k, v in action.items()
            if k.endswith(".pos")
        }

        # Extract base velocities (remove .vel suffix for API call)
        base_velocities = {
            k.replace(".vel", ""): v
            for k, v in action.items()
            if k.endswith(".vel")
        }

        # Send arm positions if present
        if arm_positions:
            try:
                t0 = time.time()
                self.client.set_arm_position(
                    shoulder_pan=arm_positions.get("arm_shoulder_pan", 0.0),
                    shoulder_lift=arm_positions.get("arm_shoulder_lift", 0.0),
                    elbow_flex=arm_positions.get("arm_elbow_flex", 0.0),
                    wrist_flex=arm_positions.get("arm_wrist_flex", 0.0),
                    wrist_roll=arm_positions.get("arm_wrist_roll", 0.0),
                    gripper=arm_positions.get("arm_gripper", 50.0),
                )
                t_arm = time.time() - t0
                print(f"  set_arm_position API call: {t_arm:.3f}s")
            except Exception as e:
                logger.error(f"Failed to set arm position: {e}")

        # Send base velocities if present
        if base_velocities:
            try:
                t0 = time.time()
                self.client.set_base_velocity(
                    x=base_velocities.get("x", 0.0),
                    y=base_velocities.get("y", 0.0),
                    theta=base_velocities.get("theta", 0.0),
                )
                t_base = time.time() - t0
                print(f"  set_base_velocity API call: {t_base:.3f}s")
            except Exception as e:
                logger.error(f"Failed to set base velocity: {e}")

        t_total = time.time() - t_start
        print(f"  send_action TOTAL: {t_total:.3f}s")
        return action

    def disconnect(self) -> None:
        """Disconnect from the robot via API."""
        if not self._connected:
            return

        try:
            # Stop motors first
            self.client.stop()
            # Disconnect from hardware
            self.client.disconnect()
            # Close HTTP session to release resources
            self.client.close()
            logger.info(f"{self} disconnected")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
        finally:
            self._connected = False
