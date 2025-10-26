# ABOUTME: FastAPI dependency injection for robot instance management
# ABOUTME: Provides singleton access to the LeKiwi robot instance

from typing import Optional

from lekiwi_control.robot.lekiwi import LeKiwi

# Global robot instance
_robot_instance: Optional[LeKiwi] = None


def get_robot() -> LeKiwi:
    """Get the robot instance.

    Raises:
        RuntimeError: If robot is not initialized.

    Returns:
        LeKiwi: The robot instance.
    """
    if _robot_instance is None:
        raise RuntimeError("Robot not initialized. Call initialize_robot() first.")
    return _robot_instance


def initialize_robot(robot: LeKiwi) -> None:
    """Initialize the global robot instance.

    Args:
        robot: The LeKiwi robot instance to use.
    """
    global _robot_instance
    _robot_instance = robot


def get_robot_or_none() -> Optional[LeKiwi]:
    """Get the robot instance or None if not initialized.

    Returns:
        Optional[LeKiwi]: The robot instance or None.
    """
    return _robot_instance
