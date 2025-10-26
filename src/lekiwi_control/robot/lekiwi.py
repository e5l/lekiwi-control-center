# ABOUTME: LeKiwi robot class - main interface for controlling the LeKiwi robot
# ABOUTME: Manages motors (arm + omnidirectional base) and cameras (front + wrist)

import json
import logging
import time
from functools import cached_property
from itertools import chain
from pathlib import Path
from typing import Any

import numpy as np

from lekiwi_control.cameras import make_cameras_from_configs
from lekiwi_control.motors import Motor, MotorCalibration, MotorNormMode
from lekiwi_control.motors.feetech import FeetechMotorsBus, OperatingMode
from lekiwi_control.robot.config import LeKiwiConfig
from lekiwi_control.utils import DeviceAlreadyConnectedError, DeviceNotConnectedError

logger = logging.getLogger(__name__)


class LeKiwi:
    """LeKiwi robot with mobile omnidirectional base and manipulator arm.

    The robot includes:
    - 6 arm motors (shoulder, elbow, wrist, gripper)
    - 3 base motors (omnidirectional wheels)
    - 2 cameras (front and wrist)
    """

    def __init__(self, config: LeKiwiConfig):
        self.config = config
        norm_mode_body = MotorNormMode.DEGREES if config.use_degrees else MotorNormMode.RANGE_M100_100
        self.bus = FeetechMotorsBus(
            port=self.config.port,
            motors={
                # arm
                "arm_shoulder_pan": Motor(1, "sts3215", norm_mode_body),
                "arm_shoulder_lift": Motor(2, "sts3215", norm_mode_body),
                "arm_elbow_flex": Motor(3, "sts3215", norm_mode_body),
                "arm_wrist_flex": Motor(4, "sts3215", norm_mode_body),
                "arm_wrist_roll": Motor(5, "sts3215", norm_mode_body),
                "arm_gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
                # base
                "base_left_wheel": Motor(7, "sts3215", MotorNormMode.RANGE_M100_100),
                "base_back_wheel": Motor(8, "sts3215", MotorNormMode.RANGE_M100_100),
                "base_right_wheel": Motor(9, "sts3215", MotorNormMode.RANGE_M100_100),
            },
            calibration=self._load_calibration(),
        )
        self.arm_motors = [motor for motor in self.bus.motors if motor.startswith("arm")]
        self.base_motors = [motor for motor in self.bus.motors if motor.startswith("base")]
        self.cameras = make_cameras_from_configs(config.cameras)

    def _load_calibration(self) -> dict[str, MotorCalibration] | None:
        """Load calibration from file if it exists."""
        calibration_file = Path("config/calibration.json")
        if not calibration_file.exists():
            logger.debug(f"Calibration file not found: {calibration_file}")
            return None

        try:
            with open(calibration_file) as f:
                data = json.load(f)

            calibration = {}
            for name, cal_data in data.items():
                calibration[name] = MotorCalibration(**cal_data)

            logger.info(f"Loaded calibration from {calibration_file}")
            return calibration
        except Exception as e:
            logger.error(f"Failed to load calibration from {calibration_file}: {e}")
            return None

    def _save_calibration(self, calibration: dict[str, MotorCalibration]) -> None:
        """Save calibration to file."""
        calibration_file = Path("config/calibration.json")

        calibration_file.parent.mkdir(parents=True, exist_ok=True)

        data = {}
        for name, cal in calibration.items():
            data[name] = {
                "id": cal.id,
                "drive_mode": cal.drive_mode,
                "homing_offset": cal.homing_offset,
                "range_min": cal.range_min,
                "range_max": cal.range_max,
            }

        try:
            with open(calibration_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved calibration to {calibration_file}")
        except Exception as e:
            logger.error(f"Failed to save calibration to {calibration_file}: {e}")

    @property
    def is_connected(self) -> bool:
        """Check if robot is connected."""
        return self.bus.is_connected and all(cam.is_connected for cam in self.cameras.values())

    @property
    def is_calibrated(self) -> bool:
        """Check if robot is calibrated."""
        return self.bus.is_calibrated

    def connect(self, calibrate: bool = True) -> None:
        """Connect to robot hardware.

        Args:
            calibrate: If True, run interactive calibration if needed.
                      Skipped if calibration was loaded from file.
        """
        if self.is_connected:
            raise DeviceAlreadyConnectedError("Robot already connected")

        self.bus.connect()

        # If we have calibration loaded from file, write it to motors
        calibration_from_file = bool(self.bus.calibration)
        if calibration_from_file:
            logger.info("Writing calibration from file to motors...")
            self.bus.disable_torque()
            self.bus.write_calibration(self.bus.calibration)
            self.bus.enable_torque()
            logger.info("Calibration loaded from file and applied successfully")

        # Only run interactive calibration if:
        # 1. No calibration was loaded from file
        # 2. Robot is not calibrated
        # 3. calibrate flag is True
        if not calibration_from_file and not self.is_calibrated and calibrate:
            logger.info("Robot not calibrated. Running interactive calibration...")
            self.calibrate()

        for cam in self.cameras.values():
            cam.connect()

        self.configure()
        logger.info("LeKiwi robot connected")

    def configure(self):
        """Configure motor parameters."""
        self.bus.disable_torque()
        self.bus.configure_motors()

        # Configure arm motors (position mode)
        for name in self.arm_motors:
            self.bus.write("Operating_Mode", name, OperatingMode.POSITION.value)
            self.bus.write("P_Coefficient", name, 16)
            self.bus.write("I_Coefficient", name, 0)
            self.bus.write("D_Coefficient", name, 32)

        # Configure base motors (velocity mode)
        for name in self.base_motors:
            self.bus.write("Operating_Mode", name, OperatingMode.VELOCITY.value)

        self.bus.enable_torque()

    def calibrate(self) -> None:
        """Run motor calibration procedure.

        This is an interactive process that requires user input.
        """
        logger.info("Running calibration...")

        motors = self.arm_motors + self.base_motors

        self.bus.disable_torque(self.arm_motors)
        for name in self.arm_motors:
            self.bus.write("Operating_Mode", name, OperatingMode.POSITION.value)

        input("Move robot to the middle of its range of motion and press ENTER...")
        homing_offsets = self.bus.set_half_turn_homings(self.arm_motors)

        homing_offsets.update(dict.fromkeys(self.base_motors, 0))

        full_turn_motor = [
            motor for motor in motors if any(keyword in motor for keyword in ["wheel", "wrist_roll"])
        ]
        unknown_range_motors = [motor for motor in motors if motor not in full_turn_motor]

        print(
            f"Move all arm joints except '{full_turn_motor}' sequentially through their "
            "entire ranges of motion.\nRecording positions. Press ENTER to stop..."
        )
        range_mins, range_maxes = self.bus.record_ranges_of_motion(unknown_range_motors)
        for name in full_turn_motor:
            range_mins[name] = 0
            range_maxes[name] = 4095

        calibration = {}
        for name, motor in self.bus.motors.items():
            calibration[name] = MotorCalibration(
                id=motor.id,
                drive_mode=0,
                homing_offset=homing_offsets[name],
                range_min=range_mins[name],
                range_max=range_maxes[name],
            )

        self.bus.write_calibration(calibration)
        self._save_calibration(calibration)
        print("Calibration complete")

    @staticmethod
    def _degps_to_raw(degps: float) -> int:
        """Convert angular velocity from degrees/sec to raw motor units."""
        steps_per_deg = 4096.0 / 360.0
        speed_in_steps = degps * steps_per_deg
        speed_int = int(round(speed_in_steps))
        # Cap to signed 16-bit range
        if speed_int > 0x7FFF:
            speed_int = 0x7FFF
        elif speed_int < -0x8000:
            speed_int = -0x8000
        return speed_int

    @staticmethod
    def _raw_to_degps(raw_speed: int) -> float:
        """Convert raw motor speed to degrees/sec."""
        steps_per_deg = 4096.0 / 360.0
        degps = raw_speed / steps_per_deg
        return degps

    def _body_to_wheel_raw(
        self,
        x: float,
        y: float,
        theta: float,
        wheel_radius: float = 0.05,
        base_radius: float = 0.125,
        max_raw: int = 3000,
    ) -> dict:
        """Convert body-frame velocities to wheel raw commands.

        Args:
            x: Linear velocity in x (m/s)
            y: Linear velocity in y (m/s)
            theta: Rotational velocity (deg/s)
            wheel_radius: Wheel radius (m)
            base_radius: Distance from center to wheel (m)
            max_raw: Maximum raw command value

        Returns:
            Dict with wheel raw commands
        """
        # Convert theta to rad/s
        theta_rad = theta * (np.pi / 180.0)
        velocity_vector = np.array([x, y, theta_rad])

        # Wheel mounting angles with -90° offset
        angles = np.radians(np.array([240, 0, 120]) - 90)
        m = np.array([[np.cos(a), np.sin(a), base_radius] for a in angles])

        # Compute wheel speeds
        wheel_linear_speeds = m.dot(velocity_vector)
        wheel_angular_speeds = wheel_linear_speeds / wheel_radius
        wheel_degps = wheel_angular_speeds * (180.0 / np.pi)

        # Scale if exceeds max
        steps_per_deg = 4096.0 / 360.0
        raw_floats = [abs(degps) * steps_per_deg for degps in wheel_degps]
        max_raw_computed = max(raw_floats)
        if max_raw_computed > max_raw:
            scale = max_raw / max_raw_computed
            wheel_degps = wheel_degps * scale

        # Convert to raw
        wheel_raw = [self._degps_to_raw(deg) for deg in wheel_degps]

        return {
            "base_left_wheel": wheel_raw[0],
            "base_back_wheel": wheel_raw[1],
            "base_right_wheel": wheel_raw[2],
        }

    def _wheel_raw_to_body(
        self,
        left_wheel_speed,
        back_wheel_speed,
        right_wheel_speed,
        wheel_radius: float = 0.05,
        base_radius: float = 0.125,
    ) -> dict[str, Any]:
        """Convert wheel raw speeds back to body-frame velocities.

        Returns:
            Dict with x.vel, y.vel, theta.vel
        """
        # Convert raw to deg/s
        wheel_degps = np.array(
            [
                self._raw_to_degps(left_wheel_speed),
                self._raw_to_degps(back_wheel_speed),
                self._raw_to_degps(right_wheel_speed),
            ]
        )

        # Convert to rad/s and then to linear speeds
        wheel_radps = wheel_degps * (np.pi / 180.0)
        wheel_linear_speeds = wheel_radps * wheel_radius

        # Inverse kinematics
        angles = np.radians(np.array([240, 0, 120]) - 90)
        m = np.array([[np.cos(a), np.sin(a), base_radius] for a in angles])
        m_inv = np.linalg.inv(m)
        velocity_vector = m_inv.dot(wheel_linear_speeds)
        x, y, theta_rad = velocity_vector
        theta = theta_rad * (180.0 / np.pi)

        return {"x.vel": x, "y.vel": y, "theta.vel": theta}

    def get_observation(self) -> dict[str, Any]:
        """Get current robot state (motor positions/velocities and camera images).

        Returns:
            Dict with arm positions, base velocities, and camera images
        """
        if not self.is_connected:
            raise DeviceNotConnectedError("Robot not connected")

        # Read motor states
        start = time.perf_counter()
        arm_pos = self.bus.sync_read("Present_Position", self.arm_motors)
        base_wheel_vel = self.bus.sync_read("Present_Velocity", self.base_motors)

        base_vel = self._wheel_raw_to_body(
            base_wheel_vel["base_left_wheel"],
            base_wheel_vel["base_back_wheel"],
            base_wheel_vel["base_right_wheel"],
        )

        arm_state = {f"{k}.pos": v for k, v in arm_pos.items()}
        obs_dict = {**arm_state, **base_vel}

        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"Read motor state: {dt_ms:.1f}ms")

        # Capture camera images
        for cam_key, cam in self.cameras.items():
            start = time.perf_counter()
            obs_dict[cam_key] = cam.async_read()
            dt_ms = (time.perf_counter() - start) * 1e3
            logger.debug(f"Read {cam_key}: {dt_ms:.1f}ms")

        return obs_dict

    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Send action command to robot.

        Args:
            action: Dict with arm positions (.pos keys) and base velocities (.vel keys)

        Returns:
            The action actually sent (may be clipped for safety)
        """
        if not self.is_connected:
            raise DeviceNotConnectedError("Robot not connected")

        arm_goal_pos = {k: v for k, v in action.items() if k.endswith(".pos")}
        base_goal_vel = {k: v for k, v in action.items() if k.endswith(".vel")}

        base_wheel_goal_vel = self._body_to_wheel_raw(
            base_goal_vel["x.vel"], base_goal_vel["y.vel"], base_goal_vel["theta.vel"]
        )

        # Safety: cap goal position if too far from present
        if self.config.max_relative_target is not None:
            present_pos = self.bus.sync_read("Present_Position", self.arm_motors)
            for key, g_pos in arm_goal_pos.items():
                motor_name = key.replace(".pos", "")
                p_pos = present_pos[motor_name]
                max_rel = self.config.max_relative_target
                if isinstance(max_rel, dict):
                    max_rel = max_rel.get(motor_name, float("inf"))
                if abs(g_pos - p_pos) > max_rel:
                    arm_goal_pos[key] = p_pos + np.sign(g_pos - p_pos) * max_rel

        # Send commands
        arm_goal_pos_raw = {k.replace(".pos", ""): v for k, v in arm_goal_pos.items()}
        self.bus.sync_write("Goal_Position", arm_goal_pos_raw)
        self.bus.sync_write("Goal_Velocity", base_wheel_goal_vel)

        return {**arm_goal_pos, **base_goal_vel}

    def stop_base(self):
        """Emergency stop for base motors."""
        self.bus.sync_write("Goal_Velocity", dict.fromkeys(self.base_motors, 0), num_retry=5)
        logger.info("Base motors stopped")

    def disconnect(self):
        """Disconnect from robot hardware."""
        if not self.is_connected:
            raise DeviceNotConnectedError("Robot not connected")

        self.stop_base()
        self.bus.disconnect(self.config.disable_torque_on_disconnect)
        for cam in self.cameras.values():
            cam.disconnect()

        logger.info("LeKiwi robot disconnected")
