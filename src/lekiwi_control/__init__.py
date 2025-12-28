# ABOUTME: LeKiwi Control Center package initialization
# ABOUTME: Provides REST API for controlling LeKiwi robot hardware

from lekiwi_control.client import LeKiwiClient

__version__ = "1.0.0"

__all__ = ["__version__", "LeKiwiClient"]
