# ABOUTME: Main FastAPI application for LeKiwi control center
# ABOUTME: Configures routes, middleware, and application lifecycle events

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from lekiwi_control import __version__
from lekiwi_control.api.dependencies import initialize_robot
from lekiwi_control.api.routes import cameras_router, health_router, motors_router, robot_router
from lekiwi_control.robot.config import LeKiwiConfig
from lekiwi_control.robot.lekiwi import LeKiwi

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    logger.info("Starting LeKiwi Control Center API v%s", __version__)

    # Initialize robot with default config
    config = LeKiwiConfig()
    robot = LeKiwi(config)
    initialize_robot(robot)

    logger.info("Robot initialized. Use /robot/connect to connect to hardware.")

    yield

    # Shutdown
    logger.info("Shutting down LeKiwi Control Center")
    if robot.is_connected:
        try:
            robot.disconnect()
            logger.info("Robot disconnected")
        except Exception as e:
            logger.error("Error disconnecting robot: %s", e)


# Create FastAPI app
app = FastAPI(
    title="LeKiwi Control Center",
    description="REST API for controlling the LeKiwi robot",
    version=__version__,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(robot_router)
app.include_router(motors_router)
app.include_router(cameras_router)

# Mount static files directory
static_dir = Path(__file__).parent.parent.parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Serve control page
@app.get("/")
async def serve_control_page():
    """Serve the robot control web interface."""
    control_page = static_dir / "control.html"
    if control_page.exists():
        return FileResponse(control_page)
    return {"message": "Control page not found. Please create static/control.html"}


def main():
    """Main entry point for the LeKiwi control center server."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
