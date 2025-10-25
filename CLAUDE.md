# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **LeKiwi Control Center** - a FastAPI-based REST API server for controlling the LeKiwi robot hardware. It runs on Raspberry Pi and provides endpoints for motor control and camera access.

**Key Characteristics:**

- Lightweight control center (no ML dependencies)
- REST API only
- LeKiwi support
- Direct hardware control
- Uses `uv` for package management

## Development Setup

### Installation with uv

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies (creates venv automatically)
uv sync

# Sync with dev dependencies
uv sync --extra dev

# Or manually activate venv if needed
source .venv/bin/activate
```

### Running the Server

```bash
# Recommended: Run with uv
uv run lekiwi-server

# Or activate venv first
source .venv/bin/activate
lekiwi-server

# With uvicorn options (for development)
uv run uvicorn lekiwi_control.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run tests
uv run pytest

# With coverage
uv run pytest --cov=lekiwi_control

# Test API endpoints
./examples/test_endpoints.sh

# Or use Python client
uv run python examples/client.py
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint
uv run ruff check . --fix

# Type check
uv run mypy src/lekiwi_control
```

## Architecture

### High-Level Structure

```
REST API (FastAPI)
    ↓
LeKiwi Robot Class
    ├─→ FeetechMotorsBus (9 motors)
    │    ├─→ 6 arm motors (position control)
    │    └─→ 3 base motors (velocity control)
    └─→ Cameras (OpenCV)
         ├─→ Front camera
         └─→ Wrist camera
```

### Key Components

1. **API Layer** (`src/lekiwi_control/api/`)

   - `main.py` - FastAPI app with lifespan management
   - `models.py` - Pydantic request/response models
   - `dependencies.py` - Robot singleton injection
   - `routes/` - Endpoint handlers (health, robot, motors, cameras)

2. **Robot Layer** (`src/lekiwi_control/robot/`)

   - `lekiwi.py` - Main robot class with motor/camera control
   - `config.py` - Configuration dataclasses

3. **Hardware Layer**
   - `motors/` - Feetech motor bus and drivers
   - `cameras/` - OpenCV camera interface

### Data Flow

**Motor Control:**

```
API Request (JSON)
  → Pydantic Validation
  → LeKiwi.send_action()
  → Motor Bus (sync_write)
  → Hardware
```

**State Reading:**

```
Hardware
  → Motor Bus (sync_read)
  → LeKiwi.get_observation()
  → Pydantic Response
  → API Response (JSON)
```

**Camera Access:**

```
API Request
  → LeKiwi.get_observation()
  → OpenCV Camera.async_read()
  → JPEG Encoding
  → HTTP Response (image/jpeg)
```

## API Endpoints Reference

### Health & Status

- `GET /health` - Returns `{status, version}`
- `GET /status` - Returns `{connected, calibrated}`

### Robot Management

- `POST /robot/connect` - Initialize hardware connection
- `POST /robot/disconnect` - Close connections, stop motors
- `POST /robot/calibrate` - Interactive calibration (requires terminal)

### Motor Control

- `GET /motors/state` - Returns arm positions + base velocities
- `POST /motors/arm/position` - Set arm target positions
  ```json
  {
    "arm_shoulder_pan": 0.0,
    "arm_shoulder_lift": 0.0,
    "arm_elbow_flex": 0.0,
    "arm_wrist_flex": 0.0,
    "arm_wrist_roll": 0.0,
    "arm_gripper": 50.0
  }
  ```
- `POST /motors/base/velocity` - Set base velocities
  ```json
  {
    "x": 0.1, // m/s forward
    "y": 0.0, // m/s lateral
    "theta": 0.0 // deg/s rotation
  }
  ```
- `POST /motors/stop` - Emergency stop (base only)

### Cameras

- `GET /cameras/list` - Returns `{cameras: ["front", "wrist"]}`
- `GET /cameras/{id}/frame` - Single JPEG frame
- `GET /cameras/{id}/stream` - MJPEG stream

## Motor System

### Motor Configuration

**Arm Motors** (IDs 1-6, Position Control):

1. `arm_shoulder_pan` - Shoulder rotation
2. `arm_shoulder_lift` - Shoulder elevation
3. `arm_elbow_flex` - Elbow joint
4. `arm_wrist_flex` - Wrist pitch
5. `arm_wrist_roll` - Wrist rotation
6. `arm_gripper` - Gripper (0-100)

**Base Motors** (IDs 7-9, Velocity Control): 7. `base_left_wheel` - Left omniwheel 8. `base_back_wheel` - Back omniwheel 9. `base_right_wheel` - Right omniwheel

### Normalization Modes

- **Arm motors**: `RANGE_M100_100` or `DEGREES` (configurable)
- **Gripper**: `RANGE_0_100` (0=open, 100=closed)
- **Base motors**: `RANGE_M100_100` (velocity)

### Kinematics

The base uses **omnidirectional kinematics**:

- Input: (x, y, theta) velocities in body frame
- Output: Raw wheel velocities
- Functions: `_body_to_wheel_raw()`, `_wheel_raw_to_body()`

## Configuration

### robot.yaml Structure

```yaml
robot:
  port: "/dev/ttyACM0"
  disable_torque_on_disconnect: true
  max_relative_target: null # or float for safety limit
  use_degrees: false

cameras:
  front:
    index_or_path: "/dev/video0"
    width: 640
    height: 480
    fps: 30
    rotation: 2 # 0=none, 1=90CW, 2=180, 3=90CCW
  wrist:
    index_or_path: "/dev/video2"
    width: 480
    height: 640
    fps: 30
    rotation: 1
```

## Common Development Tasks

### Adding a New API Endpoint

1. Define Pydantic models in `api/models.py`
2. Create route handler in appropriate `routes/*.py`
3. Import and register router in `api/main.py`
4. Use `Depends(get_robot)` for robot access
5. Handle `DeviceNotConnectedError` exceptions
6. Return appropriate HTTP status codes

Example:

```python
@router.get("/motors/temperature")
async def get_motor_temperature(robot: LeKiwi = Depends(get_robot)):
    if not robot.is_connected:
        raise HTTPException(status_code=503, detail="Robot not connected")

    temp = robot.bus.sync_read("Present_Temperature", robot.arm_motors)
    return {"temperatures": temp}
```

### Modifying Robot Behavior

Edit `src/lekiwi_control/robot/lekiwi.py`:

- `get_observation()` - Change what data is read
- `send_action()` - Modify control logic
- `configure()` - Adjust motor parameters (PID, limits)
- Add helper methods as needed

### Adding Safety Features

Implement in `send_action()`:

- Position limits check
- Velocity limits
- Collision detection
- Emergency stop logic

Example safety check:

```python
if abs(action["x.vel"]) > MAX_VELOCITY:
    raise ValueError("Velocity exceeds safety limit")
```

## Deployment on Raspberry Pi

### Systemd Service

Located at `systemd/lekiwi-control.service`:

- Runs as user `pi`
- Auto-restart on failure
- Logs to journalctl

```bash
# Install
sudo cp systemd/lekiwi-control.service /etc/systemd/system/
sudo systemctl enable lekiwi-control
sudo systemctl start lekiwi-control

# Monitor
sudo journalctl -u lekiwi-control -f
```

### Performance Considerations

- Motor read frequency: ~30-50 Hz typical
- Camera capture: Runs async (`async_read()`)
- Base velocity control: Continuous (velocity mode)
- Arm position control: Interpolated by motors

## Troubleshooting

### Import Errors

All imports should use `lekiwi_control.*` (not `lerobot.*`):

```python
from lekiwi_control.robot import LeKiwi
from lekiwi_control.motors import Motor
from lekiwi_control.cameras import OpenCVCamera
```

### Motor Communication Errors

Check:

- Serial port permissions (`sudo usermod -a -G dialout $USER`)
- Correct port in config (`/dev/ttyACM0` or `/dev/ttyUSB0`)
- Baud rate matches motors (1000000)
- Motor IDs are sequential 1-9

### Camera Not Found

```bash
# List devices
ls -l /dev/video*

# Test with v4l2
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --all
```

### API 503 Errors

Robot not connected. Call `POST /robot/connect` first.

### Calibration Issues

Calibration requires terminal interaction (user input). Not suitable for API calls. Use pre-saved calibration files instead.

## Dependencies

### Core (7 packages)

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `numpy` - Array operations
- `opencv-python` - Camera capture
- `pyserial` - Serial communication
- `feetech-servo-sdk` - Motor drivers

### Dev

- `pytest` - Testing
- `httpx` - API testing
- `ruff` - Linting/formatting
- `mypy` - Type checking

## Code Style

- **Line length**: 110 characters
- **Formatting**: `ruff format` (black-compatible)
- **Imports**: Sorted with `isort`
- **Type hints**: Encouraged, checked with `mypy`
- **Docstrings**: Google style
- **Comments**: Use `# ABOUTME:` prefix in file headers

## Testing Strategy

1. **Unit tests**: Individual functions (motors, kinematics)
2. **Integration tests**: Robot class methods
3. **API tests**: Endpoint behavior (use `httpx.AsyncClient`)
4. **Hardware tests**: Run on actual robot (manual)

## Important Notes

- **No ML/Training**: This is hardware control only
- **No Dataset Management**: No recording/replay
- **No ZMQ**: REST API only
- **Single Robot**: Only LeKiwi supported
- **Direct Control**: No policy loading or inference
- **Synchronous Motors**: Uses `sync_read`/`sync_write`

## File Naming Conventions

- Routes: `routes/{resource}.py` (e.g., `motors.py`, `cameras.py`)
- Models: Grouped in `models.py` by resource
- Configs: Dataclasses in dedicated `config.py` files
- Tests: `test_{module}.py`

## Getting Help

- **API Docs**: http://localhost:8000/docs (when server running)
- **Logs**: `sudo journalctl -u lekiwi-control -f`
- **Examples**: See `examples/` directory
- **Issues**: Create GitHub issue with logs and error messages
