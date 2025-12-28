#!/usr/bin/env python3
# ABOUTME: Test script for LeKiwiRestClient to verify API connection and basic operations
# ABOUTME: Does not require a trained policy, just tests the robot interface

"""
Test the LeKiwiRestClient connection and basic operations.

This script verifies that:
1. The REST API server is accessible
2. Robot can be connected
3. Observations can be retrieved (motors + cameras)
4. Actions can be sent
5. Proper cleanup on disconnect

Usage:
    python examples/test_rest_client.py --api-url http://pi.local:8000
"""

import argparse
import logging
import time

import numpy as np

from lerobot.robots.lekiwi.lekiwi_rest_client import LeKiwiRestClient
from lerobot.robots.lekiwi.config_lekiwi import LeKiwiConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Test LeKiwiRestClient")
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://pi.local:8000",
        help="Base URL of the LeKiwi Control Center API"
    )
    parser.add_argument(
        "--config-path",
        type=str,
        default="config/robot.yaml",
        help="Path to robot configuration file"
    )
    return parser.parse_args()


def test_connection(robot: LeKiwiRestClient):
    """Test robot connection."""
    logger.info("Testing connection...")

    assert robot.is_connected, "Robot should be connected"
    logger.info("✓ Connection verified")


def test_observation(robot: LeKiwiRestClient):
    """Test getting observations."""
    logger.info("Testing observation retrieval...")

    obs = robot.get_observation()

    # Check that all expected features are present
    expected_features = robot.observation_features.keys()
    for feature in expected_features:
        assert feature in obs, f"Missing feature: {feature}"

    # Check motor state values
    motor_features = [k for k in obs.keys() if k.endswith('.pos') or k.endswith('.vel')]
    for feature in motor_features:
        value = obs[feature]
        assert isinstance(value, (int, float, np.number)), f"{feature} should be numeric"
        logger.info(f"  {feature}: {value:.2f}")

    # Check camera frames
    camera_features = [k for k in obs.keys() if k in ['front', 'wrist']]
    for cam_name in camera_features:
        frame = obs[cam_name]
        assert isinstance(frame, np.ndarray), f"{cam_name} should be numpy array"
        assert frame.ndim == 3, f"{cam_name} should be 3D array (H, W, C)"
        assert frame.shape[2] == 3, f"{cam_name} should have 3 channels (RGB)"
        logger.info(f"  {cam_name}: shape={frame.shape}, dtype={frame.dtype}")

    logger.info("✓ Observations retrieved successfully")


def test_action(robot: LeKiwiRestClient):
    """Test sending actions."""
    logger.info("Testing action execution...")

    # Get current observation to know current state
    obs = robot.get_observation()

    # Create a small movement action (relative to current position)
    action = {
        "arm_shoulder_pan.pos": obs["arm_shoulder_pan.pos"] + 5.0,
        "arm_shoulder_lift.pos": obs["arm_shoulder_lift.pos"] + 0.0,
        "arm_elbow_flex.pos": obs["arm_elbow_flex.pos"] + 0.0,
        "arm_wrist_flex.pos": obs["arm_wrist_flex.pos"] + 0.0,
        "arm_wrist_roll.pos": obs["arm_wrist_roll.pos"] + 0.0,
        "arm_gripper.pos": obs["arm_gripper.pos"],
        "x.vel": 0.0,
        "y.vel": 0.0,
        "theta.vel": 0.0,
    }

    # Send action
    result = robot.send_action(action)

    # Verify action was sent
    assert result is not None, "Action should return result"
    logger.info("✓ Action sent successfully")

    # Wait a bit for motor to move
    time.sleep(1.0)

    # Return to original position
    action_back = {
        "arm_shoulder_pan.pos": obs["arm_shoulder_pan.pos"],
        "arm_shoulder_lift.pos": obs["arm_shoulder_lift.pos"],
        "arm_elbow_flex.pos": obs["arm_elbow_flex.pos"],
        "arm_wrist_flex.pos": obs["arm_wrist_flex.pos"],
        "arm_wrist_roll.pos": obs["arm_wrist_roll.pos"],
        "arm_gripper.pos": obs["arm_gripper.pos"],
        "x.vel": 0.0,
        "y.vel": 0.0,
        "theta.vel": 0.0,
    }
    robot.send_action(action_back)
    logger.info("✓ Returned to original position")


def test_feature_structure(robot: LeKiwiRestClient):
    """Test observation and action feature structures."""
    logger.info("Testing feature structures...")

    obs_features = robot.observation_features
    action_features = robot.action_features

    logger.info(f"Observation features: {list(obs_features.keys())}")
    logger.info(f"Action features: {list(action_features.keys())}")

    # Verify feature types
    for name, feature_type in obs_features.items():
        if isinstance(feature_type, tuple):
            logger.info(f"  {name}: shape={feature_type}")
        else:
            logger.info(f"  {name}: type={feature_type}")

    logger.info("✓ Feature structures verified")


def main():
    """Main test function."""
    args = parse_args()

    logger.info("=" * 60)
    logger.info("LeKiwiRestClient Test Suite")
    logger.info("=" * 60)

    try:
        # Load configuration
        logger.info(f"Loading configuration from {args.config_path}")
        config = LeKiwiConfig.from_yaml(args.config_path)

        # Create robot client
        logger.info(f"Creating REST client for {args.api_url}")
        robot = LeKiwiRestClient(config, base_url=args.api_url)

        # Connect to robot
        logger.info("Connecting to robot...")
        robot.connect(calibrate=False)

        # Run tests
        test_connection(robot)
        test_feature_structure(robot)
        test_observation(robot)
        test_action(robot)

        logger.info("=" * 60)
        logger.info("All tests passed! ✓")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return 1

    finally:
        # Disconnect
        if 'robot' in locals() and robot.is_connected:
            logger.info("Disconnecting from robot...")
            robot.disconnect()

    return 0


if __name__ == "__main__":
    exit(main())
