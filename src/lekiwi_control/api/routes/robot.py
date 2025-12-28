# ABOUTME: Robot connection and calibration management endpoints
# ABOUTME: Handles robot connect/disconnect and calibration operations

import base64
import time

import cv2
from fastapi import APIRouter, Depends, HTTPException

from lekiwi_control.api.dependencies import get_robot
from lekiwi_control.api.models import CalibrationResponse, FullObservationResponse
from lekiwi_control.robot.lekiwi import LeKiwi

router = APIRouter(prefix="/robot", tags=["robot"])


@router.post("/connect")
async def connect_robot(robot: LeKiwi = Depends(get_robot)):
    """Connect to the robot hardware.

    This initializes the motor bus and cameras.

    Calibration behavior:
    - If config/calibration.json exists: loaded and applied automatically
    - If no calibration file: interactive calibration is NOT triggered via API
      (use the /robot/calibrate endpoint or run calibration manually)
    """
    if robot.is_connected:
        raise HTTPException(status_code=400, detail="Robot already connected")

    try:
        robot.connect(calibrate=False)
        return {"success": True, "message": "Robot connected successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect: {str(e)}")


@router.post("/disconnect")
async def disconnect_robot(robot: LeKiwi = Depends(get_robot)):
    """Disconnect from the robot hardware.

    This stops all motors and closes connections.
    """
    if not robot.is_connected:
        raise HTTPException(status_code=400, detail="Robot not connected")

    try:
        robot.disconnect()
        return {"success": True, "message": "Robot disconnected successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")


@router.post("/calibrate", response_model=CalibrationResponse)
async def calibrate_robot(robot: LeKiwi = Depends(get_robot)):
    """Run robot calibration.

    WARNING: This is an interactive process that requires user input.
    Not recommended for automated use via API.

    For automated calibration, use the calibration file instead.
    """
    if not robot.is_connected:
        raise HTTPException(status_code=400, detail="Robot not connected. Connect first.")

    try:
        # Note: This will fail in API context as it requires user input
        # This endpoint is provided for completeness but should be used carefully
        robot.calibrate()
        return CalibrationResponse(success=True, message="Calibration completed")
    except Exception as e:
        return CalibrationResponse(success=False, message=f"Calibration failed: {str(e)}")


@router.get("/observation", response_model=FullObservationResponse)
async def get_full_observation(robot: LeKiwi = Depends(get_robot)):
    """Get complete robot state in one call (motors + all cameras).

    This endpoint is optimized for performance by returning everything in a single
    HTTP request, avoiding multiple round-trips (3x faster than separate calls).

    Returns:
        - arm_motors: Dict of arm motor positions
        - base_velocities: Dict of base velocities (x, y, theta)
        - cameras: Dict of camera name -> base64-encoded JPEG
    """
    if not robot.is_connected:
        raise HTTPException(status_code=503, detail="Robot not connected")

    try:
        t0 = time.time()
        # Get complete observation (motors + cameras)
        observation = robot.get_observation()
        t_obs = time.time() - t0
        print(f"[API /robot/observation] get_observation took {t_obs:.3f}s")

        # Extract arm positions
        arm_motors = {
            "arm_shoulder_pan": observation["arm_shoulder_pan.pos"],
            "arm_shoulder_lift": observation["arm_shoulder_lift.pos"],
            "arm_elbow_flex": observation["arm_elbow_flex.pos"],
            "arm_wrist_flex": observation["arm_wrist_flex.pos"],
            "arm_wrist_roll": observation["arm_wrist_roll.pos"],
            "arm_gripper": observation["arm_gripper.pos"],
        }

        # Extract base velocities
        base_velocities = {
            "x": observation["x.vel"],
            "y": observation["y.vel"],
            "theta": observation["theta.vel"],
        }

        # Encode camera frames as base64 JPEG
        cameras = {}
        for cam_name in robot.cameras.keys():
            frame = observation[cam_name]

            # Encode as JPEG
            t_encode_start = time.time()
            ret, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            t_encode = time.time() - t_encode_start
            print(f"[API /robot/observation] JPEG encode {cam_name} took {t_encode:.3f}s")

            if not ret:
                raise HTTPException(status_code=500, detail=f"Failed to encode {cam_name}")

            # Convert to base64
            cameras[cam_name] = base64.b64encode(buffer.tobytes()).decode("utf-8")

        t_total = time.time() - t0
        print(f"[API /robot/observation] TOTAL took {t_total:.3f}s")

        return FullObservationResponse(
            arm_motors=arm_motors, base_velocities=base_velocities, cameras=cameras
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get observation: {str(e)}")
