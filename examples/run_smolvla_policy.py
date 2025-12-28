#!/usr/bin/env python3
# ABOUTME: Execute a pretrained SmolVLA policy on the LeKiwi robot via REST API
# ABOUTME: Demonstrates end-to-end integration of vision-language model with robot control

"""
Run a pretrained SmolVLA policy on LeKiwi robot via REST API.

This script demonstrates how to:
1. Load a pretrained SmolVLA policy from HuggingFace Hub or local path
2. Connect to the LeKiwi robot via the REST API server
3. Run inference loop: observations → policy → actions
4. Handle camera frames and motor state properly

Usage:
    # With default settings (requires pretrained model and running API server)
    python examples/run_smolvla_policy.py

    # With custom model path and API URL
    python examples/run_smolvla_policy.py \
        --policy-path lerobot/smolvla_lekiwi_base \
        --api-url http://192.168.1.100:8000 \
        --task "pick up the red block" \
        --num-steps 100

Requirements:
    - LeKiwi Control Center API server running on the robot
    - Pretrained SmolVLA policy compatible with LeKiwi robot
    - Camera configuration matching the policy training
"""

import argparse
import logging
import time
from pathlib import Path

import torch
import numpy as np

from lerobot.robots.lekiwi.lekiwi_rest_client import LeKiwiRestClient
from lerobot.robots.lekiwi.config_lekiwi import LeKiwiConfig
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from lerobot.policies.smolvla.processor_smolvla import make_smolvla_pre_post_processors

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run SmolVLA policy on LeKiwi robot via REST API"
    )
    parser.add_argument(
        "--policy-path",
        type=str,
        required=True,
        help="Path to pretrained SmolVLA policy (HuggingFace Hub ID or local path)"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://pi.local:8000",
        help="Base URL of the LeKiwi Control Center API server"
    )
    parser.add_argument(
        "--config-path",
        type=str,
        default="config/robot.yaml",
        help="Path to robot configuration file"
    )
    parser.add_argument(
        "--task",
        type=str,
        default="Pick up the pen",
        help="Task description for the policy (language instruction)"
    )
    parser.add_argument(
        "--num-steps",
        type=int,
        default=50,
        help="Number of inference steps to run"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Device to run policy inference on (cuda/cpu)"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Display camera frames during execution (requires opencv-python)"
    )
    parser.add_argument(
        "--hz",
        type=float,
        default=10.0,
        help="Control frequency in Hz"
    )
    return parser.parse_args()


def load_policy(policy_path: str, device: str) -> SmolVLAPolicy:
    """Load pretrained SmolVLA policy from path.

    Args:
        policy_path: HuggingFace Hub ID or local path to pretrained model
        device: Device to load model on (cuda/cpu)

    Returns:
        Loaded SmolVLAPolicy ready for inference
    """
    logger.info(f"Loading policy from {policy_path}...")

    # Load policy using from_pretrained (handles both Hub and local paths)
    policy = SmolVLAPolicy.from_pretrained(policy_path)

    # Move to device and set to eval mode
    policy = policy.to(device)
    policy.eval()

    logger.info(f"Policy loaded successfully on {device}")
    logger.info(f"Policy config: chunk_size={policy.config.chunk_size}, "
                f"n_obs_steps={policy.config.n_obs_steps}")

    return policy


def load_robot(config_path: str, api_url: str) -> LeKiwiRestClient:
    """Initialize and connect to the LeKiwi robot via REST API.

    Args:
        config_path: Path to robot configuration YAML file
        api_url: Base URL of the REST API server

    Returns:
        Connected LeKiwiRestClient instance
    """
    logger.info(f"Connecting to robot at {api_url}...")

    # Load robot configuration
    config = LeKiwiConfig()

    # Create REST client adapter
    robot = LeKiwiRestClient(config, base_url=api_url)

    # Connect to robot (calibration handled by server)
    robot.connect(calibrate=False)

    if not robot.is_connected:
        raise RuntimeError("Failed to connect to robot")

    logger.info("Robot connected successfully")
    logger.info(f"Observation features: {list(robot.observation_features.keys())}")
    logger.info(f"Action features: {list(robot.action_features.keys())}")

    return robot


def run_policy_loop(
    policy: SmolVLAPolicy,
    robot: LeKiwiRestClient,
    task: str,
    num_steps: int,
    hz: float,
    visualize: bool = True,
    dataset_stats: dict | None = None,
):
    """Run the policy inference loop.

    Args:
        policy: Loaded SmolVLA policy
        robot: Connected robot client
        task: Language task description
        num_steps: Number of inference steps
        hz: Control frequency in Hz
        visualize: Whether to display camera frames
        dataset_stats: Dataset statistics for normalization (if available)
    """
    logger.info(f"Starting policy execution for {num_steps} steps at {hz} Hz")
    logger.info(f"Task: {task}")

    # Create pre/post processors
    preprocessor, postprocessor = make_smolvla_pre_post_processors(
        policy.config,
        dataset_stats=dataset_stats
    )

    # Reset policy state
    policy.reset()

    # Get policy device for tensor allocation
    policy_device = next(policy.parameters()).device
    logger.info(f"Policy device: {policy_device}")

    # Control loop timing
    dt = 1.0 / hz

    # Visualization setup
    if visualize:
        try:
            import cv2
            cv2.namedWindow("Front Camera", cv2.WINDOW_NORMAL)
            cv2.namedWindow("Wrist Camera", cv2.WINDOW_NORMAL)
        except ImportError:
            logger.warning("opencv-python not installed, disabling visualization")
            visualize = False

    try:
        for step in range(num_steps):
            step_start = time.time()

            # Get observation from robot
            t0 = time.time()
            obs = robot.get_observation()
            t_obs = time.time() - t0
            print(f"Step {step}: get_observation took {t_obs:.3f}s")

            if obs is None:
                logger.error(f"Step {step}: Observation is None!")
                raise ValueError("get_observation() returned None")

            if not isinstance(obs, dict):
                logger.error(f"Step {step}: Observation is not a dict, got {type(obs)}")
                raise ValueError(f"get_observation() returned {type(obs)}, expected dict")

            # Preprocess observation
            # The preprocessor expects a "batch" dict with keys like "observation.key_name"
            # Task goes at the top level as complementary data, not in observation

            # Map camera names to policy's expected format
            # Policy expects: observation.images.camera1, observation.images.camera2, etc.
            t0 = time.time()
            camera_mapping = {
                "front": "images.camera1",
                "wrist": "images.camera2",
            }

            # Flatten observation dict by adding "observation." prefix to all keys
            batch = {}
            for key, value in obs.items():
                # Rename cameras to match policy expectations
                if key in camera_mapping:
                    batch_key = f"observation.{camera_mapping[key]}"
                else:
                    batch_key = f"observation.{key}"
                batch[batch_key] = value

            # Add task as top-level key (complementary data)
            batch["task"] = task
            t_batch = time.time() - t0
            print(f"Step {step}: create_batch took {t_batch:.3f}s")

            # Preprocess the batch
            t0 = time.time()
            processed_obs = preprocessor(batch)
            t_preprocess = time.time() - t0
            print(f"Step {step}: preprocessor took {t_preprocess:.3f}s")

            # Move language tokens to policy device
            t0 = time.time()
            for key, value in processed_obs.items():
                if 'language' in key.lower() and isinstance(value, torch.Tensor):
                    processed_obs[key] = value.to(policy_device)

            # Convert images from (H, W, C) to (B, C, H, W) format for policy
            image_keys = [k for k in processed_obs.keys() if 'image' in k.lower() or 'camera' in k.lower()]
            for key in image_keys:
                value = processed_obs[key]
                if isinstance(value, torch.Tensor):
                    # Permute from (H, W, C) to (C, H, W)
                    if len(value.shape) == 3 and value.shape[2] in [3, 4]:  # HWC format
                        value = value.permute(2, 0, 1)  # -> (C, H, W)
                        # Add batch dimension
                        value = value.unsqueeze(0)  # -> (B, C, H, W)
                        # Convert to float and normalize to [0, 1]
                        value = value.float() / 255.0
                        # Move to policy device
                        value = value.to(policy_device)
                        processed_obs[key] = value

            # Combine all state values into observation.state tensor
            # Collect all state values (positions and velocities)
            state_keys = [k for k in processed_obs.keys() if k.startswith('observation.')
                         and not any(x in k for x in ['image', 'camera', 'language'])]
            state_values = []
            for key in sorted(state_keys):  # Sort for consistent ordering
                value = processed_obs[key]
                if isinstance(value, (int, float)):
                    state_values.append(float(value))
                elif isinstance(value, torch.Tensor):
                    state_values.append(value.item() if value.numel() == 1 else value.flatten())

            if state_values:
                # Combine into single tensor and move to policy device
                state_tensor = torch.tensor(state_values, dtype=torch.float32).unsqueeze(0)  # (1, num_states)
                state_tensor = state_tensor.to(policy_device)
                processed_obs['observation.state'] = state_tensor
            t_tensors = time.time() - t0
            print(f"Step {step}: tensor_processing took {t_tensors:.3f}s")

            # Run policy inference
            t0 = time.time()
            with torch.no_grad():
                action = policy.select_action(processed_obs)
            t_inference = time.time() - t0
            print(f"Step {step}: policy_inference took {t_inference:.3f}s")

            # Postprocess action
            t0 = time.time()
            action_tensor = postprocessor(action)

            # Convert action tensor to dict format expected by robot
            # Action tensor is (1, num_actions) - squeeze to get (num_actions,)
            action_values = action_tensor.squeeze().cpu().numpy()

            # Map to robot action features (policy likely outputs only arm positions)
            action_dict = {}
            action_features = list(robot.action_features.keys())

            # Assuming policy outputs arm positions only (6 values)
            # Fill in the action dict with arm positions, set base velocities to 0
            for i, feature in enumerate(action_features):
                if i < len(action_values):
                    action_dict[feature] = float(action_values[i])
                else:
                    # Default to 0 for any missing values (e.g., base velocities)
                    action_dict[feature] = 0.0
            t_postprocess = time.time() - t0
            print(f"Step {step}: postprocess_action took {t_postprocess:.3f}s")

            # Send action to robot
            t0 = time.time()
            robot.send_action(action_dict)
            t_send = time.time() - t0
            print(f"Step {step}: send_action took {t_send:.3f}s")

            # Print timing breakdown
            step_total = time.time() - step_start
            print(f"Step {step} TOTAL: {step_total:.3f}s")
            print(f"  Breakdown: obs={t_obs:.3f}s, batch={t_batch:.3f}s, preprocess={t_preprocess:.3f}s, "
                  f"tensors={t_tensors:.3f}s, inference={t_inference:.3f}s, postprocess={t_postprocess:.3f}s, send={t_send:.3f}s")
            print()

            # Visualize if requested
            if visualize and "front" in obs and "wrist" in obs:
                front_img = obs["front"]
                wrist_img = obs["wrist"]

                # Convert RGB to BGR for OpenCV display
                cv2.imshow("Front Camera", cv2.cvtColor(front_img, cv2.COLOR_RGB2BGR))
                cv2.imshow("Wrist Camera", cv2.cvtColor(wrist_img, cv2.COLOR_RGB2BGR))

                # Exit on 'q' key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("Visualization window closed, stopping execution")
                    break

            # Log progress every 10 steps
            if (step + 1) % 10 == 0:
                logger.info(f"Completed {step + 1}/{num_steps} steps")

            # Maintain control frequency
            elapsed = time.time() - step_start
            if elapsed < dt:
                time.sleep(dt - elapsed)
            else:
                logger.warning(f"Step took {elapsed:.3f}s, exceeding target {dt:.3f}s")

        logger.info("Policy execution completed successfully")

    except KeyboardInterrupt:
        logger.info("Execution interrupted by user")

    except Exception as e:
        logger.error(f"Error during policy execution: {e}", exc_info=True)
        raise

    finally:
        # Cleanup visualization
        if visualize:
            cv2.destroyAllWindows()


def main():
    """Main execution function."""
    args = parse_args()

    logger.info("=" * 80)
    logger.info("SmolVLA Policy Execution on LeKiwi Robot")
    logger.info("=" * 80)

    try:
        # Load policy
        policy = load_policy(args.policy_path, args.device)

        # Connect to robot
        robot = load_robot(args.config_path, args.api_url)

        # Run policy loop
        run_policy_loop(
            policy=policy,
            robot=robot,
            task=args.task,
            num_steps=args.num_steps,
            hz=args.hz,
            dataset_stats=None,  # TODO: Load from policy if available
        )

    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        return 1

    finally:
        # Disconnect from robot
        if 'robot' in locals():
            logger.info("Disconnecting from robot...")
            robot.disconnect()

    logger.info("Execution finished")
    return 0


if __name__ == "__main__":
    exit(main())
