# ABOUTME: Health check and status endpoints for the LeKiwi control center
# ABOUTME: Provides system health monitoring and robot connection status

from fastapi import APIRouter, Depends

from lekiwi_control import __version__
from lekiwi_control.api.dependencies import get_robot_or_none
from lekiwi_control.api.models import HealthResponse, RobotStatusResponse
from lekiwi_control.robot.lekiwi import LeKiwi

router = APIRouter(prefix="", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version=__version__)


@router.get("/status", response_model=RobotStatusResponse)
async def get_status(robot: LeKiwi | None = Depends(get_robot_or_none)):
    """Get robot connection and calibration status."""
    if robot is None:
        return RobotStatusResponse(connected=False, calibrated=False)

    return RobotStatusResponse(connected=robot.is_connected, calibrated=robot.is_calibrated)
