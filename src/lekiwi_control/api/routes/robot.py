# ABOUTME: Robot connection and calibration management endpoints
# ABOUTME: Handles robot connect/disconnect and calibration operations

from fastapi import APIRouter, Depends, HTTPException

from lekiwi_control.api.dependencies import get_robot
from lekiwi_control.api.models import CalibrationResponse
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
