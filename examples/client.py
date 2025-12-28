#!/usr/bin/env python3
"""Example usage of the LeKiwi Control Center API client."""

import time

from lekiwi_control import LeKiwiClient

def main():
    """Example usage of the LeKiwi client."""
    client = LeKiwiClient()  # Update with your robot's IP

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
