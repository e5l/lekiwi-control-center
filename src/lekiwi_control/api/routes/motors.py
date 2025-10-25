# ABOUTME: Motor control endpoints for arm and base motors
# ABOUTME: Provides REST API for reading motor state and sending position/velocity commands

from fastapi import APIRouter, Depends, HTTPException

from lekiwi_control.api.dependencies import get_robot
from lekiwi_control.api.models import (
    ActionResponse,
    ArmPositionRequest,
    BaseVelocityRequest,
    MotorsStateResponse,
)
from lekiwi_control.robot.lekiwi import LeKiwi

router = APIRouter(prefix="/motors", tags=["motors"])


@router.get("/state", response_model=MotorsStateResponse)
async def get_motors_state(robot: LeKiwi = Depends(get_robot)):
    """Get current state of all motors (positions and velocities)."""
    if not robot.is_connected:
        raise HTTPException(status_code=503, detail="Robot not connected")

    try:
        observation = robot.get_observation()

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

        return MotorsStateResponse(arm_motors=arm_motors, base_velocities=base_velocities)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read motor state: {str(e)}")


@router.post("/arm/position", response_model=ActionResponse)
async def set_arm_position(request: ArmPositionRequest, robot: LeKiwi = Depends(get_robot)):
    """Set target positions for arm motors.

    Positions are in normalized units based on calibration.
    Base velocities are set to 0.
    """
    if not robot.is_connected:
        raise HTTPException(status_code=503, detail="Robot not connected")

    try:
        # Build action dict
        action = {
            "arm_shoulder_pan.pos": request.arm_shoulder_pan,
            "arm_shoulder_lift.pos": request.arm_shoulder_lift,
            "arm_elbow_flex.pos": request.arm_elbow_flex,
            "arm_wrist_flex.pos": request.arm_wrist_flex,
            "arm_wrist_roll.pos": request.arm_wrist_roll,
            "arm_gripper.pos": request.arm_gripper,
            "x.vel": 0.0,
            "y.vel": 0.0,
            "theta.vel": 0.0,
        }

        action_sent = robot.send_action(action)
        return ActionResponse(success=True, action_sent=action_sent)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set arm position: {str(e)}")


@router.post("/base/velocity", response_model=ActionResponse)
async def set_base_velocity(request: BaseVelocityRequest, robot: LeKiwi = Depends(get_robot)):
    """Set target velocities for base wheels.

    x, y: linear velocities in m/s
    theta: angular velocity in deg/s

    Arm positions are kept at current values.
    """
    if not robot.is_connected:
        raise HTTPException(status_code=503, detail="Robot not connected")

    try:
        # Get current arm positions
        observation = robot.get_observation()

        # Build action dict with current arm positions and new base velocities
        action = {
            "arm_shoulder_pan.pos": observation["arm_shoulder_pan.pos"],
            "arm_shoulder_lift.pos": observation["arm_shoulder_lift.pos"],
            "arm_elbow_flex.pos": observation["arm_elbow_flex.pos"],
            "arm_wrist_flex.pos": observation["arm_wrist_flex.pos"],
            "arm_wrist_roll.pos": observation["arm_wrist_roll.pos"],
            "arm_gripper.pos": observation["arm_gripper.pos"],
            "x.vel": request.x,
            "y.vel": request.y,
            "theta.vel": request.theta,
        }

        action_sent = robot.send_action(action)
        return ActionResponse(success=True, action_sent=action_sent)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set base velocity: {str(e)}")


@router.post("/stop", response_model=ActionResponse)
async def stop_motors(robot: LeKiwi = Depends(get_robot)):
    """Emergency stop - stops base motors immediately.

    Arm motors maintain their current position.
    """
    if not robot.is_connected:
        raise HTTPException(status_code=503, detail="Robot not connected")

    try:
        robot.stop_base()
        return ActionResponse(success=True, action_sent={"base": "stopped"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop motors: {str(e)}")
