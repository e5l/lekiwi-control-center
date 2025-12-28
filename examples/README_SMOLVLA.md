# SmolVLA Policy Integration with LeKiwi Robot

This guide explains how to run pretrained SmolVLA vision-language policies on the LeKiwi robot using the REST API interface.

## Overview

The integration enables end-to-end autonomous robot control:

```
Language Task + Camera Observations → SmolVLA Policy → Motor Commands → Robot Actions
```

### Key Components

1. **LeKiwiRestClient** - Adapter that wraps the REST API client with the LeRobot Robot interface
2. **SmolVLA Policy** - Vision-language model trained for robot manipulation tasks
3. **REST API Server** - FastAPI server running on the robot (LeKiwi Control Center)
4. **Policy Execution Script** - Main script to run inference loop

## Architecture

```
┌─────────────────────────────────────┐
│   SmolVLA Policy (Laptop/Workstation) │
│   - Vision-language model             │
│   - Inference on GPU/CPU              │
└───────────────┬─────────────────────┘
                │ HTTP/REST
                ▼
┌─────────────────────────────────────┐
│   LeKiwi Control Center API         │
│   (Raspberry Pi on Robot)           │
│   - FastAPI server                  │
│   - Motor control                   │
│   - Camera streaming                │
└───────────────┬─────────────────────┘
                │ Serial + USB
                ▼
┌─────────────────────────────────────┐
│   LeKiwi Robot Hardware             │
│   - 9 Feetech motors (6 arm + 3 base)│
│   - 2 cameras (front + wrist)       │
└─────────────────────────────────────┘
```

## Prerequisites

### 1. Hardware Setup

- LeKiwi robot with all motors connected and calibrated
- Raspberry Pi with LeKiwi Control Center installed and running
- Network connection between workstation and robot
- Cameras connected and configured

### 2. Software Requirements

**On the robot (Raspberry Pi):**
```bash
# Install and start the LeKiwi Control Center
cd /path/to/lekiwi-control-center
uv sync
uv run lekiwi-server

# Or use systemd service
sudo systemctl start lekiwi-control
```

**On the workstation:**
```bash
# Install dependencies
cd /path/to/lekiwi-control-center
uv sync --extra dev

# Install additional dependencies if needed
pip install torch transformers pillow opencv-python
```

### 3. Pretrained Model

You need a pretrained SmolVLA policy compatible with the LeKiwi robot. This can be:

- A model from HuggingFace Hub: `lerobot/smolvla_lekiwi_base`
- A local checkpoint from training: `outputs/train/smolvla/checkpoints/010000/pretrained_model`

## Quick Start

### 1. Start the API Server

On the robot (Raspberry Pi):

```bash
# Start the server
uv run lekiwi-server

# Or with custom settings
uv run uvicorn lekiwi_control.api.main:app --host 0.0.0.0 --port 8000
```

Verify it's running:
```bash
curl http://pi.local:8000/health
# Should return: {"status": "ok", "version": "..."}
```

### 2. Connect to the Robot

```bash
curl -X POST http://pi.local:8000/robot/connect
# Should return: {"status": "connected"}
```

### 3. Run the Policy

On your workstation:

```bash
python examples/run_smolvla_policy.py \
    --policy-path lerobot/smolvla_lekiwi_base \
    --api-url http://pi.local:8000 \
    --task "pick up the red block" \
    --num-steps 100 \
    --hz 10.0 \
    --visualize
```

## Usage Guide

### Command Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--policy-path` | (required) | Path to pretrained SmolVLA policy |
| `--api-url` | `http://pi.local:8000` | Base URL of the API server |
| `--config-path` | `config/robot.yaml` | Path to robot configuration |
| `--task` | `"Move the robot arm..."` | Language task description |
| `--num-steps` | `50` | Number of inference steps |
| `--device` | `cuda` or `cpu` | Device for policy inference |
| `--visualize` | `False` | Display camera frames |
| `--hz` | `10.0` | Control frequency in Hz |

### Configuration File

The robot configuration (`config/robot.yaml`) defines:

```yaml
robot:
  port: "/dev/ttyACM0"
  use_degrees: false

cameras:
  front:
    index_or_path: "/dev/video0"
    width: 640
    height: 480
    fps: 30
    rotation: 2  # 180 degrees
    color_mode: "bgr"

  wrist:
    index_or_path: "/dev/video2"
    width: 480
    height: 640
    fps: 30
    rotation: 1  # 90 degrees clockwise
    color_mode: "bgr"
```

### Python API Usage

For more control, you can use the Python API directly:

```python
from lerobot.robots.lekiwi.lekiwi_rest_client import LeKiwiRestClient
from lerobot.robots.lekiwi.config_lekiwi import LeKiwiConfig
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy

# Load configuration
config = LeKiwiConfig.from_yaml("config/robot.yaml")

# Create robot client
robot = LeKiwiRestClient(config, base_url="http://pi.local:8000")
robot.connect()

# Load policy
policy = SmolVLAPolicy.from_pretrained("lerobot/smolvla_lekiwi_base")
policy.eval()

# Inference loop
for step in range(100):
    # Get observation
    obs = robot.get_observation()
    obs["task"] = "pick up the red block"

    # Run policy
    action = policy.select_action(obs)

    # Execute action
    robot.send_action(action)

# Cleanup
robot.disconnect()
```

## Data Flow Details

### Observations

The robot provides observations in this structure:

```python
{
    # Motor state (9 DOF)
    "arm_shoulder_pan.pos": 0.0,      # -100 to 100
    "arm_shoulder_lift.pos": 0.0,     # -100 to 100
    "arm_elbow_flex.pos": 0.0,        # -95 to 99
    "arm_wrist_flex.pos": 0.0,        # -60 to 60
    "arm_wrist_roll.pos": 0.0,        # -100 to 100
    "arm_gripper.pos": 50.0,          # 0 to 100
    "x.vel": 0.0,                     # m/s
    "y.vel": 0.0,                     # m/s
    "theta.vel": 0.0,                 # deg/s

    # Camera images (numpy arrays)
    "front": np.array(480, 640, 3),   # RGB
    "wrist": np.array(640, 480, 3),   # RGB

    # Task description (added by you)
    "task": "pick up the red block"
}
```

### Actions

The policy outputs actions in the same structure as motor states:

```python
{
    "arm_shoulder_pan.pos": -20.5,
    "arm_shoulder_lift.pos": 15.3,
    "arm_elbow_flex.pos": 30.2,
    "arm_wrist_flex.pos": -10.1,
    "arm_wrist_roll.pos": 0.0,
    "arm_gripper.pos": 80.0,
    "x.vel": 0.1,
    "y.vel": 0.0,
    "theta.vel": 5.0,
}
```

Values are automatically clamped to safe ranges by the client before sending to the API.

### Processing Pipeline

1. **Observation Collection**
   - `robot.get_observation()` → HTTP GET `/motors/state` and `/cameras/{id}/frame`
   - JPEG images converted to numpy RGB arrays
   - State values extracted from JSON response

2. **Preprocessing**
   - Images resized to policy input size (e.g., 512×512)
   - Task description tokenized
   - State values normalized using dataset statistics
   - Batch dimension added

3. **Policy Inference**
   - Forward pass through SmolVLM vision encoder
   - Language instruction embedded
   - Action expert head predicts motor commands
   - Output denormalized to robot scale

4. **Action Execution**
   - Action dict converted to API format
   - Values clamped to motor limits
   - HTTP POST `/motors/arm/position` and `/motors/base/velocity`

## Troubleshooting

### Connection Issues

**Problem:** `Failed to connect to http://pi.local:8000`

**Solutions:**
- Check server is running: `curl http://pi.local:8000/health`
- Verify network connection: `ping pi.local`
- Try IP address instead: `--api-url http://192.168.1.100:8000`
- Check firewall settings on Raspberry Pi

### Policy Loading Errors

**Problem:** `Error loading policy from path`

**Solutions:**
- Verify model exists: `ls lerobot/smolvla_lekiwi_base/`
- Check for required files: `config.json`, `model.safetensors`
- Try downloading manually: `huggingface-cli download lerobot/smolvla_lekiwi_base`
- Check internet connection for Hub downloads

### Camera Frame Errors

**Problem:** `Failed to get frame from front/wrist`

**Solutions:**
- Check camera configuration in `config/robot.yaml`
- Verify cameras are connected: `ls /dev/video*`
- Test camera access: `GET /cameras/list`
- Check camera rotation settings match training data

### Slow Inference

**Problem:** `Step took 0.5s, exceeding target 0.1s`

**Solutions:**
- Use GPU for inference: `--device cuda`
- Reduce image resolution in config
- Lower control frequency: `--hz 5.0`
- Profile to find bottleneck (network vs. inference)

### Robot Not Moving

**Problem:** Policy runs but robot doesn't move

**Solutions:**
- Check robot connection status: `GET /status`
- Verify motors are enabled (not in torque-off mode)
- Check action values are reasonable (not all zeros)
- Monitor server logs: `journalctl -u lekiwi-control -f`
- Verify safety limits aren't clamping all actions

## Safety Considerations

1. **Emergency Stop**: Press Ctrl+C to stop execution immediately
2. **Workspace Clear**: Ensure robot workspace is clear of obstacles
3. **Motor Limits**: Client automatically clamps values to safe ranges
4. **Supervision**: Always supervise autonomous operation
5. **Kill Switch**: Keep access to API `/motors/stop` endpoint

## Performance Optimization

### Network Latency

- Use wired Ethernet instead of WiFi
- Run policy on robot if GPU available (Jetson Nano/Xavier)
- Compress camera frames (JPEG quality settings)

### Inference Speed

- Use GPU for policy inference
- Enable mixed precision: `policy.to(dtype=torch.float16)`
- Batch multiple steps if policy supports it
- Consider model quantization

### Control Frequency

Target 10-30 Hz for manipulation tasks:

- 10 Hz: Safe for most tasks, lower computational requirements
- 20 Hz: Smoother motion, better for dynamic tasks
- 30 Hz: Real-time control, requires fast network and GPU

## Advanced Usage

### Custom Pre/Post Processing

```python
from lerobot.policies.smolvla.processor_smolvla import make_smolvla_pre_post_processors

# Load dataset statistics for proper normalization
dataset_stats = torch.load("path/to/stats.pt")

preprocessor, postprocessor = make_smolvla_pre_post_processors(
    policy.config,
    dataset_stats=dataset_stats
)

# Apply custom preprocessing
obs = robot.get_observation()
obs["task"] = "custom task"
processed_obs = preprocessor(obs)
```

### Multi-Step Rollouts

SmolVLA can predict action sequences (chunks):

```python
# Policy predicts chunk_size=50 steps ahead
action_chunk = policy.select_action(obs)

# Execute chunk over time
for t in range(policy.config.chunk_size):
    robot.send_action(action_chunk[t])
    time.sleep(1.0 / hz)
```

### Recording Demonstrations

```python
# Record observations and actions for later analysis
trajectory = []

for step in range(num_steps):
    obs = robot.get_observation()
    action = policy.select_action(obs)

    trajectory.append({
        "observation": obs,
        "action": action,
        "timestamp": time.time()
    })

    robot.send_action(action)

# Save trajectory
import pickle
with open("trajectory.pkl", "wb") as f:
    pickle.dump(trajectory, f)
```

## Next Steps

- Fine-tune SmolVLA on your own task demonstrations
- Collect LeKiwi dataset using the control center
- Train custom policies for specific manipulation tasks
- Implement closed-loop visual servoing
- Add force/torque sensing for contact-rich tasks

## References

- [LeKiwi Control Center Documentation](../README.md)
- [LeRobot Documentation](https://github.com/huggingface/lerobot)
- [SmolVLM Model](https://huggingface.co/HuggingFaceTB/SmolVLM2-500M-Video-Instruct)
- [REST API Documentation](http://pi.local:8000/docs)

## Support

For issues and questions:

- LeKiwi Control Center: [GitHub Issues](https://github.com/yourusername/lekiwi-control-center/issues)
- LeRobot Framework: [HuggingFace Forums](https://discuss.huggingface.co/c/lerobot)
- SmolVLA Policy: [Model Card](https://huggingface.co/lerobot/smolvla_base)
