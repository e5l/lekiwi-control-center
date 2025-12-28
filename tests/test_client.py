# ABOUTME: Tests for the LeKiwi Python client
# ABOUTME: Verifies value clamping and client functionality

from lekiwi_control.client import LeKiwiClient


class TestLeKiwiClient:
    """Test suite for LeKiwiClient."""

    def test_clamp_value_within_range(self):
        """Test that values within range are not modified."""
        assert LeKiwiClient._clamp_value(50.0, "arm_shoulder_pan") == 50.0
        assert LeKiwiClient._clamp_value(0.0, "arm_gripper") == 0.0
        assert LeKiwiClient._clamp_value(-50.0, "arm_wrist_flex") == -50.0

    def test_clamp_value_above_max(self):
        """Test that values above max are clamped."""
        assert LeKiwiClient._clamp_value(150.0, "arm_shoulder_pan") == 100.0
        assert LeKiwiClient._clamp_value(120.0, "arm_gripper") == 100.0
        assert LeKiwiClient._clamp_value(100.0, "arm_elbow_flex") == 99.0
        assert LeKiwiClient._clamp_value(80.0, "arm_wrist_flex") == 60.0

    def test_clamp_value_below_min(self):
        """Test that values below min are clamped."""
        assert LeKiwiClient._clamp_value(-150.0, "arm_shoulder_pan") == -100.0
        assert LeKiwiClient._clamp_value(-10.0, "arm_gripper") == 0.0
        assert LeKiwiClient._clamp_value(-100.0, "arm_elbow_flex") == -95.0
        assert LeKiwiClient._clamp_value(-80.0, "arm_wrist_flex") == -60.0

    def test_clamp_value_boundary_values(self):
        """Test exact boundary values."""
        # Max boundaries
        assert LeKiwiClient._clamp_value(100.0, "arm_shoulder_pan") == 100.0
        assert LeKiwiClient._clamp_value(100.0, "arm_gripper") == 100.0
        assert LeKiwiClient._clamp_value(99.0, "arm_elbow_flex") == 99.0
        assert LeKiwiClient._clamp_value(60.0, "arm_wrist_flex") == 60.0

        # Min boundaries
        assert LeKiwiClient._clamp_value(-100.0, "arm_shoulder_lift") == -100.0
        assert LeKiwiClient._clamp_value(0.0, "arm_gripper") == 0.0
        assert LeKiwiClient._clamp_value(-95.0, "arm_elbow_flex") == -95.0
        assert LeKiwiClient._clamp_value(-60.0, "arm_wrist_flex") == -60.0

    def test_clamp_value_unknown_motor(self):
        """Test that unknown motor names return value unchanged."""
        assert LeKiwiClient._clamp_value(500.0, "unknown_motor") == 500.0

    def test_motor_limits_defined(self):
        """Test that all expected motor limits are defined."""
        expected_motors = [
            "arm_shoulder_pan",
            "arm_shoulder_lift",
            "arm_elbow_flex",
            "arm_wrist_flex",
            "arm_wrist_roll",
            "arm_gripper",
        ]

        for motor in expected_motors:
            assert motor in LeKiwiClient.MOTOR_LIMITS
            min_val, max_val = LeKiwiClient.MOTOR_LIMITS[motor]
            assert min_val < max_val, f"{motor} has invalid range"

    def test_client_initialization(self):
        """Test client initialization with different URLs."""
        # Default URL
        client = LeKiwiClient()
        assert client.base_url == "http://pi.local:8000"

        # Custom URL
        client = LeKiwiClient("http://192.168.1.100:8000")
        assert client.base_url == "http://192.168.1.100:8000"

        # URL with trailing slash
        client = LeKiwiClient("http://192.168.1.100:8000/")
        assert client.base_url == "http://192.168.1.100:8000"
