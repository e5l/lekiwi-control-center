#!/bin/bash
# Example curl commands for testing LeKiwi Control Center API

# Set the base URL (update with your robot's IP)
BASE_URL="http://localhost:8000"

echo "=== Health Check ==="
curl -X GET "$BASE_URL/health"
echo -e "\n"

echo "=== Get Status ==="
curl -X GET "$BASE_URL/status"
echo -e "\n"

echo "=== Connect to Robot ==="
curl -X POST "$BASE_URL/robot/connect"
echo -e "\n"

echo "=== Get Motor State ==="
curl -X GET "$BASE_URL/motors/state"
echo -e "\n"

echo "=== Set Arm Position (example values) ==="
curl -X POST "$BASE_URL/motors/arm/position" \
  -H "Content-Type: application/json" \
  -d '{
    "arm_shoulder_pan": 0.0,
    "arm_shoulder_lift": 0.0,
    "arm_elbow_flex": 0.0,
    "arm_wrist_flex": 0.0,
    "arm_wrist_roll": 0.0,
    "arm_gripper": 50.0
  }'
echo -e "\n"

echo "=== Set Base Velocity (move forward slowly) ==="
curl -X POST "$BASE_URL/motors/base/velocity" \
  -H "Content-Type: application/json" \
  -d '{"x": 0.1, "y": 0.0, "theta": 0.0}'
echo -e "\n"

sleep 2

echo "=== Stop Motors ==="
curl -X POST "$BASE_URL/motors/stop"
echo -e "\n"

echo "=== List Cameras ==="
curl -X GET "$BASE_URL/cameras/list"
echo -e "\n"

echo "=== Get Camera Frame (front) ==="
curl -X GET "$BASE_URL/cameras/front/frame" --output front_camera.jpg
echo "Saved to front_camera.jpg"
echo -e "\n"

echo "=== Disconnect from Robot ==="
curl -X POST "$BASE_URL/robot/disconnect"
echo -e "\n"

echo "Done!"
