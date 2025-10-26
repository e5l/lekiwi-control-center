# LeKiwi Control Center

REST API control center for the LeKiwi robot, designed to run on Raspberry Pi.

## Overview

The LeKiwi Control Center provides a FastAPI-based REST API for controlling the LeKiwi robot hardware:
- **6 arm motors** (shoulder, elbow, wrist, gripper) - Feetech STS3215 servos
- **3 base motors** (omnidirectional wheels) - Feetech STS3215 servos
- **2 cameras** (front and wrist) - USB cameras via OpenCV

## Features

- ✅ RESTful API for motor control (positions and velocities)
- ✅ Camera image capture and streaming (JPEG/MJPEG)
- ✅ Motor calibration support
- ✅ Auto-start capability via systemd
- ✅ Lightweight (~7 core dependencies)
- ✅ Raspberry Pi optimized

## Installation

### Prerequisites

- Raspberry Pi (tested on Pi 4)
- Python 3.10+
- `uv` package manager ([installation guide](https://github.com/astral-sh/uv))

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Clone and Install

```bash
git clone https://github.com/yourusername/lekiwi-control-center.git
cd lekiwi-control-center

# Sync dependencies (creates venv automatically)
uv sync
```

### Development Installation

```bash
# Sync with dev dependencies
uv sync --extra dev
```

## Quick Start

### 1. Start the Server

```bash
# Run with uv
uv run lekiwi-server

# Or activate venv and run directly
source .venv/bin/activate
lekiwi-server
```

The API will be available at `http://localhost:8000`

### 2. Access API Documentation

Open your browser to:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

### 3. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Connect to robot
curl -X POST http://localhost:8000/robot/connect

# Get motor state
curl http://localhost:8000/motors/state

# Set base velocity (move forward)
curl -X POST http://localhost:8000/motors/base/velocity \
  -H "Content-Type: application/json" \
  -d '{"x": 0.1, "y": 0.0, "theta": 0.0}'

# Stop
curl -X POST http://localhost:8000/motors/stop
```

## API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /status` - Robot connection status

### Robot Connection
- `POST /robot/connect` - Connect to robot hardware
- `POST /robot/disconnect` - Disconnect from robot
- `POST /robot/calibrate` - Run calibration (interactive)

### Motor Control
- `GET /motors/state` - Get all motor positions/velocities
- `POST /motors/arm/position` - Set arm motor positions
- `POST /motors/base/velocity` - Set base velocities (x, y, theta)
- `POST /motors/stop` - Emergency stop

### Cameras
- `GET /cameras/list` - List available cameras
- `GET /cameras/{camera_id}/frame` - Get single frame (JPEG)
- `GET /cameras/{camera_id}/stream` - Stream frames (MJPEG)

## Configuration

Edit `config/robot.yaml` to configure:
- Motor serial port
- Camera devices and settings
- Safety limits
- Server settings

## Auto-Start on Boot

### Install systemd Service

```bash
# Copy service file
sudo cp systemd/lekiwi-control.service /etc/systemd/system/

# Edit paths in service file if needed
sudo nano /etc/systemd/system/lekiwi-control.service

# Enable and start service
sudo systemctl enable lekiwi-control
sudo systemctl start lekiwi-control

# Check status
sudo systemctl status lekiwi-control
```

### View Logs

```bash
# Follow logs
sudo journalctl -u lekiwi-control -f

# View recent logs
sudo journalctl -u lekiwi-control -n 100
```

## Examples

### Python Client

```python
from examples.client import LeKiwiClient

client = LeKiwiClient("http://192.168.1.100:8000")

# Connect
client.connect()

# Get state
state = client.get_motors_state()
print(state)

# Move forward
client.set_base_velocity(x=0.1, y=0.0, theta=0.0)

# Capture image
client.get_camera_frame("front", "image.jpg")

# Disconnect
client.disconnect()
```

See `examples/` directory for more examples.

## Development

### Run Tests

```bash
uv run pytest
```

### Format Code

```bash
uv run ruff format .
```

### Lint

```bash
uv run ruff check .
```

### Type Check

```bash
uv run mypy src/lekiwi_control
```

## Architecture

```
lekiwi-control-center/
├── src/lekiwi_control/
│   ├── api/              # FastAPI application
│   │   ├── main.py       # App entry point
│   │   ├── models.py     # Pydantic models
│   │   ├── dependencies.py  # DI container
│   │   └── routes/       # API endpoints
│   ├── robot/            # Robot implementation
│   │   ├── lekiwi.py     # LeKiwi class
│   │   └── config.py     # Configuration
│   ├── motors/           # Motor control
│   │   └── feetech/      # Feetech drivers
│   ├── cameras/          # Camera interface
│   └── utils/            # Utilities
├── config/               # Configuration files
├── scripts/              # Startup scripts
├── systemd/              # Systemd service
└── examples/             # Example clients
```

## Troubleshooting

### Permission Denied on Serial Port

```bash
sudo usermod -a -G dialout $USER
# Log out and log back in
```

### Camera Not Found

```bash
# List video devices
ls -l /dev/video*

# Test camera
v4l2-ctl --list-devices
```

### Server Won't Start

```bash
# Check if port 8000 is in use
sudo netstat -tulpn | grep 8000

# Check logs
sudo journalctl -u lekiwi-control -n 50
```

## License

Apache 2.0

## Contributing

Contributions welcome! Please open an issue or pull request.
