# Installation Guide

## Local Development

### 1. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup

```bash
git clone https://github.com/yourusername/lekiwi-control-center.git
cd lekiwi-control-center

# Sync dependencies (creates .venv automatically)
uv sync

# For development with extra tools
uv sync --extra dev
```

### 3. Run the Server

```bash
# Option 1: Using uv run (recommended)
uv run lekiwi-server

# Option 2: Activate venv first
source .venv/bin/activate
lekiwi-server
```

### 4. Test the Installation

```bash
# In another terminal
curl http://localhost:8000/health
```

## Raspberry Pi Deployment

### 1. Prerequisites on Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+ if needed
sudo apt install python3 python3-pip python3-venv -y

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env  # or restart terminal

# Add user to dialout group for serial port access
sudo usermod -a -G dialout $USER
# Log out and back in for this to take effect
```

### 2. Transfer Code to Pi

```bash
# From your development machine
scp -r lekiwi-control-center pi@<PI_IP_ADDRESS>:~/

# Or clone directly on Pi
ssh pi@<PI_IP_ADDRESS>
git clone https://github.com/yourusername/lekiwi-control-center.git
cd lekiwi-control-center
```

### 3. Install on Pi

```bash
# On the Pi
cd ~/lekiwi-control-center

# Sync dependencies
uv sync

# Test run
uv run lekiwi-server
# Press Ctrl+C to stop
```

### 4. Setup Auto-Start (systemd)

```bash
# Copy systemd service file
sudo cp systemd/lekiwi-control.service /etc/systemd/system/

# If you installed in a different location, edit the service file
sudo nano /etc/systemd/system/lekiwi-control.service
# Update WorkingDirectory and ExecStart paths if needed

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable lekiwi-control

# Start service now
sudo systemctl start lekiwi-control

# Check status
sudo systemctl status lekiwi-control
```

### 5. View Logs

```bash
# Follow logs in real-time
sudo journalctl -u lekiwi-control -f

# View recent logs
sudo journalctl -u lekiwi-control -n 100

# View logs since last boot
sudo journalctl -u lekiwi-control -b
```

### 6. Managing the Service

```bash
# Stop service
sudo systemctl stop lekiwi-control

# Restart service
sudo systemctl restart lekiwi-control

# Disable auto-start
sudo systemctl disable lekiwi-control

# Check if service is running
sudo systemctl is-active lekiwi-control
```

## Updating the Installation

### Local Development

```bash
cd lekiwi-control-center
git pull
uv sync  # Updates dependencies
```

### On Raspberry Pi

```bash
# Stop the service
sudo systemctl stop lekiwi-control

# Update code
cd ~/lekiwi-control-center
git pull

# Update dependencies
uv sync

# Restart service
sudo systemctl start lekiwi-control

# Check status
sudo systemctl status lekiwi-control
```

## Troubleshooting

### uv not found

```bash
# Make sure uv is in PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Or install it
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Permission denied on serial port

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Log out and back in, then verify
groups | grep dialout
```

### Service won't start

```bash
# Check logs for errors
sudo journalctl -u lekiwi-control -n 50

# Check if port 8000 is already in use
sudo netstat -tulpn | grep 8000

# Test manually
cd ~/lekiwi-control-center
uv run lekiwi-server
```

### Dependencies fail to install

```bash
# On Raspberry Pi, you may need additional packages
sudo apt install -y build-essential python3-dev pkg-config \
    libavformat-dev libavcodec-dev libavdevice-dev \
    libavutil-dev libswscale-dev libswresample-dev libavfilter-dev

# Then try again
uv sync
```

### Camera not found

```bash
# List video devices
ls -l /dev/video*

# Test camera
v4l2-ctl --list-devices

# Install v4l-utils if needed
sudo apt install v4l-utils
```

## Network Access

To access the API from other devices on your network:

1. Find Pi's IP address:
   ```bash
   hostname -I
   ```

2. Access API from another device:
   ```
   http://<PI_IP_ADDRESS>:8000
   ```

3. To allow external access, update firewall if needed:
   ```bash
   sudo ufw allow 8000/tcp
   ```

## Next Steps

- Review [README.md](README.md) for API documentation
- See [examples/](examples/) for client code examples
- Read [CLAUDE.md](CLAUDE.md) for development guidelines
