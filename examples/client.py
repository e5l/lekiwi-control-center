#!/usr/bin/env python3
"""Example Python client for LeKiwi Control Center API."""

import requests
import time
from typing import Dict, Any

class LeKiwiClient:
    """Simple client for interacting with LeKiwi Control Center API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")

    def health_check(self) -> Dict[str, Any]:
        """Check if the server is healthy."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def get_status(self) -> Dict[str, Any]:
        """Get robot connection status."""
        response = requests.get(f"{self.base_url}/status")
        response.raise_for_status()
        return response.json()

    def connect(self) -> Dict[str, Any]:
        """Connect to the robot."""
        response = requests.post(f"{self.base_url}/robot/connect")
        response.raise_for_status()
        return response.json()

    def disconnect(self) -> Dict[str, Any]:
        """Disconnect from the robot."""
        response = requests.post(f"{self.base_url}/robot/disconnect")
        response.raise_for_status()
        return response.json()

    def get_motors_state(self) -> Dict[str, Any]:
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
    ) -> Dict[str, Any]:
        """Set arm motor positions."""
        payload = {
            "arm_shoulder_pan": shoulder_pan,
            "arm_shoulder_lift": shoulder_lift,
            "arm_elbow_flex": elbow_flex,
            "arm_wrist_flex": wrist_flex,
            "arm_wrist_roll": wrist_roll,
            "arm_gripper": gripper,
        }
        response = requests.post(f"{self.base_url}/motors/arm/position", json=payload)
        response.raise_for_status()
        return response.json()

    def set_base_velocity(self, x: float = 0.0, y: float = 0.0, theta: float = 0.0) -> Dict[str, Any]:
        """Set base velocities."""
        payload = {"x": x, "y": y, "theta": theta}
        response = requests.post(f"{self.base_url}/motors/base/velocity", json=payload)
        response.raise_for_status()
        return response.json()

    def stop(self) -> Dict[str, Any]:
        """Emergency stop."""
        response = requests.post(f"{self.base_url}/motors/stop")
        response.raise_for_status()
        return response.json()

    def list_cameras(self) -> Dict[str, Any]:
        """List available cameras."""
        response = requests.get(f"{self.base_url}/cameras/list")
        response.raise_for_status()
        return response.json()

    def get_camera_frame(self, camera_id: str, save_path: str = None) -> bytes:
        """Get a single frame from camera."""
        response = requests.get(f"{self.base_url}/cameras/{camera_id}/frame")
        response.raise_for_status()

        if save_path:
            with open(save_path, "wb") as f:
                f.write(response.content)

        return response.content


def main():
    """Example usage of the LeKiwi client."""
    client = LeKiwiClient("http://192.168.1.100:8000")  # Update with your robot's IP

    # Check health
    print("Health:", client.health_check())

    # Connect to robot
    print("Connecting...", client.connect())
    time.sleep(1)

    # Get status
    print("Status:", client.get_status())

    # Get current state
    print("Motor state:", client.get_motors_state())

    # Move forward for 2 seconds
    print("Moving forward...")
    client.set_base_velocity(x=0.1, y=0.0, theta=0.0)
    time.sleep(2)

    # Stop
    print("Stopping...")
    client.stop()

    # Get camera frame
    print("Capturing image...")
    cameras = client.list_cameras()
    print("Available cameras:", cameras)

    if cameras["cameras"]:
        client.get_camera_frame(cameras["cameras"][0], "test_image.jpg")
        print("Image saved to test_image.jpg")

    # Disconnect
    print("Disconnecting...", client.disconnect())


if __name__ == "__main__":
    main()
