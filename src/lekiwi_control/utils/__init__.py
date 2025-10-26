# ABOUTME: Utility functions and error handling for LeKiwi control center
# ABOUTME: Provides error classes and helper utilities

from .errors import (
    DeviceAlreadyConnectedError,
    DeviceNotConnectedError,
)

__all__ = ["DeviceAlreadyConnectedError", "DeviceNotConnectedError"]
