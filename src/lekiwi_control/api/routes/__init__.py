# ABOUTME: API routes package initialization
# ABOUTME: Exports all route routers for registration with FastAPI app

from .cameras import router as cameras_router
from .health import router as health_router
from .motors import router as motors_router
from .robot import router as robot_router

__all__ = ["health_router", "motors_router", "cameras_router", "robot_router"]
