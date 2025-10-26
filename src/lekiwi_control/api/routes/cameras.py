# ABOUTME: Camera access endpoints for capturing images from robot cameras
# ABOUTME: Provides JPEG image capture and MJPEG streaming from front and wrist cameras

import io

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse

from lekiwi_control.api.dependencies import get_robot
from lekiwi_control.api.models import CameraListResponse
from lekiwi_control.robot.lekiwi import LeKiwi

router = APIRouter(prefix="/cameras", tags=["cameras"])


@router.get("/list", response_model=CameraListResponse)
async def list_cameras(robot: LeKiwi = Depends(get_robot)):
    """Get list of available cameras."""
    if not robot.is_connected:
        raise HTTPException(status_code=503, detail="Robot not connected")

    return CameraListResponse(cameras=list(robot.cameras.keys()))


@router.get("/{camera_id}/frame")
async def get_camera_frame(camera_id: str, robot: LeKiwi = Depends(get_robot)):
    """Get a single frame from the specified camera as JPEG.

    Args:
        camera_id: Camera identifier ('front' or 'wrist')

    Returns:
        JPEG image
    """
    if not robot.is_connected:
        raise HTTPException(status_code=503, detail="Robot not connected")

    if camera_id not in robot.cameras:
        raise HTTPException(
            status_code=404, detail=f"Camera '{camera_id}' not found. Available: {list(robot.cameras.keys())}"
        )

    try:
        # Get observation which includes camera frames
        observation = robot.get_observation()
        frame = observation[camera_id]

        # Encode as JPEG
        ret, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if not ret:
            raise HTTPException(status_code=500, detail="Failed to encode image")

        return Response(content=buffer.tobytes(), media_type="image/jpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to capture frame: {str(e)}")


@router.get("/{camera_id}/stream")
async def stream_camera(camera_id: str, robot: LeKiwi = Depends(get_robot)):
    """Stream camera frames as MJPEG.

    Args:
        camera_id: Camera identifier ('front' or 'wrist')

    Returns:
        MJPEG stream
    """
    if not robot.is_connected:
        raise HTTPException(status_code=503, detail="Robot not connected")

    if camera_id not in robot.cameras:
        raise HTTPException(
            status_code=404, detail=f"Camera '{camera_id}' not found. Available: {list(robot.cameras.keys())}"
        )

    def generate_frames():
        """Generator function for streaming frames."""
        try:
            while True:
                # Get current frame
                observation = robot.get_observation()
                frame = observation[camera_id]

                # Encode as JPEG
                ret, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                if not ret:
                    continue

                # Yield frame in MJPEG format
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
                )

        except GeneratorExit:
            pass
        except Exception:
            pass

    return StreamingResponse(
        generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame"
    )
