#!/usr/bin/env python3
"""Demonstration of automatic value clamping in LeKiwiClient."""

from lekiwi_control import LeKiwiClient


def main():
    """Demonstrate automatic value clamping."""
    print("LeKiwi Client - Value Clamping Demonstration")
    print("=" * 60)

    # Show motor limits
    print("\nMotor Limits:")
    for motor, (min_val, max_val) in LeKiwiClient.MOTOR_LIMITS.items():
        print(f"  {motor:25s}: {min_val:6.1f} to {max_val:6.1f}")

    # Test clamping examples
    print("\nClamping Examples:")
    print("-" * 60)

    test_cases = [
        ("arm_shoulder_pan", 150.0, "value above max"),
        ("arm_shoulder_pan", -150.0, "value below min"),
        ("arm_shoulder_pan", 50.0, "value within range"),
        ("arm_elbow_flex", 100.0, "elbow above max (99.0)"),
        ("arm_elbow_flex", -100.0, "elbow below min (-95.0)"),
        ("arm_wrist_flex", 80.0, "wrist_flex above max (60.0)"),
        ("arm_wrist_flex", -80.0, "wrist_flex below min (-60.0)"),
        ("arm_gripper", 150.0, "gripper above max (100.0)"),
        ("arm_gripper", -10.0, "gripper below min (0.0)"),
    ]

    for motor, value, description in test_cases:
        clamped = LeKiwiClient._clamp_value(value, motor)
        limits = LeKiwiClient.MOTOR_LIMITS[motor]
        print(f"{motor:25s}: {value:7.1f} → {clamped:7.1f}  ({description})")
        print(f"{'':25s}  Range: [{limits[0]:.1f}, {limits[1]:.1f}]")
        print()

    print("=" * 60)
    print("All values are automatically clamped when using set_arm_position()")


if __name__ == "__main__":
    main()
