# ABOUTME: Pydantic models for API request/response validation
# ABOUTME: Defines data schemas for motor control, camera access, and robot status

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str


class RobotStatusResponse(BaseModel):
    """Robot connection status response."""

    connected: bool
    calibrated: bool


class MotorState(BaseModel):
    """Single motor state."""

    name: str
    position: float | None = None
    velocity: float | None = None


class MotorsStateResponse(BaseModel):
    """All motors state response."""

    arm_motors: dict[str, float]  # name -> position
    base_velocities: dict[str, float]  # x.vel, y.vel, theta.vel


class ArmPositionRequest(BaseModel):
    """Request to set arm motor positions."""

    arm_shoulder_pan: float = Field(..., description="Shoulder pan position")
    arm_shoulder_lift: float = Field(..., description="Shoulder lift position")
    arm_elbow_flex: float = Field(..., description="Elbow flex position")
    arm_wrist_flex: float = Field(..., description="Wrist flex position")
    arm_wrist_roll: float = Field(..., description="Wrist roll position")
    arm_gripper: float = Field(..., description="Gripper position (0-100)")


class BaseVelocityRequest(BaseModel):
    """Request to set base velocities."""

    x: float = Field(0.0, description="Linear velocity in x direction (m/s)")
    y: float = Field(0.0, description="Linear velocity in y direction (m/s)")
    theta: float = Field(0.0, description="Angular velocity (deg/s)")


class ActionResponse(BaseModel):
    """Response after sending action."""

    success: bool
    action_sent: dict[str, Any]


class CameraListResponse(BaseModel):
    """List of available cameras."""

    cameras: list[str]


class CalibrationResponse(BaseModel):
    """Calibration operation response."""

    success: bool
    message: str
