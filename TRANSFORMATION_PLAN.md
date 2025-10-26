# LeKiwi Control Center Transformation Plan

## Overview
Transform the LeRobot repository into a lightweight REST API control center for the LeKiwi robot, running on Raspberry Pi.

## Current State Analysis

### LeKiwi Robot Components (TO KEEP)
- **Motors**:
  - 6 arm motors (shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper)
  - 3 base motors (left_wheel, back_wheel, right_wheel - omnidirectional)
  - All using Feetech STS3215 servos
- **Cameras**:
  - Front camera (`/dev/video0` - 640x480)
  - Wrist camera (`/dev/video2` - 480x640)
- **Features**:
  - Motor position reading (arm)
  - Motor velocity control (base wheels)
  - Omniwheel kinematics (x, y, theta velocities)
  - Camera image capture
  - Motor calibration

### Current Architecture (TO REMOVE)
- ZMQ-based client/server (lekiwi_host.py, lekiwi_client.py)
- All ML/policy code (ACT, Diffusion, TDMPC, etc.)
- Training/evaluation pipelines
- Dataset management
- All other robots (Aloha, SO100, Koch, etc.)
- Simulation environments (PushT, etc.)
- Processor pipelines for ML
- HuggingFace Hub integration

## Target Architecture

### Core Components (KEEP & SIMPLIFY)
1. **LeKiwi Robot Class** (`src/lerobot/robots/lekiwi/lekiwi.py`)
   - Motor control via Feetech bus
   - Camera interface
   - Calibration support

2. **Motor System** (`src/lerobot/motors/`)
   - Feetech motor drivers only
   - Motor calibration utilities

3. **Camera System** (`src/lerobot/cameras/`)
   - OpenCV camera support only

4. **Utilities** (`src/lerobot/utils/`)
   - Error handling
   - Basic utilities

### New Components (CREATE)
1. **FastAPI REST Server**
   - Replace ZMQ with REST endpoints
   - Run on Raspberry Pi
   - Auto-start capability

2. **API Endpoints**:
   ```
   GET  /health                    - Health check
   GET  /status                    - Robot connection status
   POST /connect                   - Connect to robot
   POST /disconnect                - Disconnect from robot

   GET  /motors/state              - Get all motor positions/velocities
   GET  /motors/{motor_id}/state   - Get single motor state
   POST /motors/arm/position       - Set arm motor positions
   POST /motors/base/velocity      - Set base velocities (x, y, theta)
   POST /motors/stop               - Emergency stop

   GET  /cameras/list              - List available cameras
   GET  /cameras/{camera_id}/frame - Get camera frame (JPEG)
   GET  /cameras/stream/{camera_id} - Stream camera (MJPEG)

   POST /calibrate                 - Run calibration
   ```

## Transformation Steps

### Phase 1: Clean Up (Remove Unnecessary Code)
- [ ] Remove all policy directories except base classes
- [ ] Remove datasets directory
- [ ] Remove environments directory
- [ ] Remove processor pipelines
- [ ] Remove training/evaluation scripts
- [ ] Remove other robot implementations
- [ ] Remove simulation-related code
- [ ] Remove HuggingFace Hub integration
- [ ] Remove ZMQ client code

### Phase 2: Simplify Dependencies
- [ ] Update pyproject.toml to minimal dependencies:
  ```toml
  dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "opencv-python>=4.9.0",
    "numpy>=1.24.0",
    "pyserial>=3.5",
    "feetech-servo-sdk>=1.0.0",
  ]
  ```
- [ ] Remove all ML dependencies (torch, transformers, etc.)
- [ ] Remove optional extras (aloha, pusht, etc.)
- [ ] Create uv-compatible configuration

### Phase 3: Create REST API Server
- [ ] Create `src/lekiwi_control/api/main.py` - FastAPI app
- [ ] Create `src/lekiwi_control/api/routes/` directory:
  - `health.py` - Health/status endpoints
  - `motors.py` - Motor control endpoints
  - `cameras.py` - Camera endpoints
  - `calibration.py` - Calibration endpoints
- [ ] Create `src/lekiwi_control/api/models.py` - Pydantic models
- [ ] Create `src/lekiwi_control/api/dependencies.py` - Robot singleton

### Phase 4: Simplify Robot Code
- [ ] Keep LeKiwi class but remove ML-specific methods
- [ ] Keep Feetech motor bus implementation
- [ ] Keep OpenCV camera implementation
- [ ] Remove Robot base class abstractions (or simplify)
- [ ] Remove calibration file dependencies on HF Hub
- [ ] Simplify error handling

### Phase 5: Configuration & Deployment
- [ ] Create simple YAML/JSON config file for:
  - Motor port (/dev/ttyACM0)
  - Camera devices
  - API server settings
- [ ] Create systemd service file for auto-start
- [ ] Create startup script
- [ ] Add logging configuration

### Phase 6: Documentation
- [ ] Update README.md with:
  - Installation instructions using uv
  - API endpoint documentation
  - Quick start guide
  - Raspberry Pi setup instructions
- [ ] Update CLAUDE.md with new architecture
- [ ] Create API documentation (OpenAPI/Swagger)
- [ ] Add example client scripts (Python, curl)

### Phase 7: Testing
- [ ] Create basic tests for API endpoints
- [ ] Test motor control functionality
- [ ] Test camera capture
- [ ] Test on Raspberry Pi hardware

## New Directory Structure
```
lekiwi-control-center/
├── src/
│   └── lekiwi_control/
│       ├── __init__.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── main.py              # FastAPI app
│       │   ├── models.py            # Pydantic models
│       │   ├── dependencies.py      # DI (robot singleton)
│       │   └── routes/
│       │       ├── __init__.py
│       │       ├── health.py
│       │       ├── motors.py
│       │       ├── cameras.py
│       │       └── calibration.py
│       ├── robot/
│       │   ├── __init__.py
│       │   ├── lekiwi.py           # Simplified LeKiwi class
│       │   └── config.py           # Robot configuration
│       ├── motors/
│       │   ├── __init__.py
│       │   ├── motor.py            # Motor classes
│       │   ├── feetech/            # Feetech driver
│       │   └── calibration.py
│       ├── cameras/
│       │   ├── __init__.py
│       │   └── opencv_camera.py
│       └── utils/
│           ├── __init__.py
│           └── errors.py
├── config/
│   ├── robot.yaml                  # Robot configuration
│   └── logging.yaml                # Logging config
├── scripts/
│   ├── start_server.sh
│   └── calibrate.py
├── systemd/
│   └── lekiwi-control.service
├── tests/
│   ├── test_api.py
│   ├── test_motors.py
│   └── test_cameras.py
├── examples/
│   ├── client.py                   # Python client example
│   └── test_endpoints.sh           # curl examples
├── pyproject.toml
├── uv.lock
├── README.md
└── CLAUDE.md
```

## Key Simplifications

1. **No ML Dependencies**: Remove PyTorch, transformers, datasets, etc.
2. **No Multi-Robot Support**: Only LeKiwi
3. **No Dataset Management**: No recording/replay functionality
4. **No Policy Loading**: Direct motor control only
5. **No Hub Integration**: Local configuration files only
6. **Simple Config**: YAML/JSON instead of dataclass registry
7. **REST Instead of ZMQ**: Standard HTTP/REST API
8. **uv Package Manager**: Fast, modern Python packaging

## Dependencies

### Core (Minimal)
- fastapi - REST API framework
- uvicorn - ASGI server
- opencv-python - Camera capture
- numpy - Array operations
- pyserial - Serial communication
- feetech-servo-sdk - Motor control
- pydantic - Data validation

### Development
- pytest - Testing
- httpx - API testing
- ruff - Linting/formatting

### System (Raspberry Pi)
- Python 3.10+
- uv package manager
- ffmpeg (for camera support)

## Migration Strategy

1. **Create new structure** alongside old code
2. **Copy and simplify** needed components
3. **Remove old code** once new code works
4. **Test thoroughly** before final cleanup
5. **Update documentation** last

## Risk Mitigation

- Keep git history for rollback capability
- Test each phase independently
- Maintain calibration file compatibility
- Document all API breaking changes
- Create migration guide for existing users

## Success Criteria

- [ ] REST API responds to all defined endpoints
- [ ] Motors can be controlled via API
- [ ] Camera images accessible via API
- [ ] Runs on Raspberry Pi without issues
- [ ] Auto-starts on boot (systemd)
- [ ] Installation via uv works
- [ ] Documentation complete and accurate
- [ ] Zero ML dependencies
- [ ] < 100MB total package size
