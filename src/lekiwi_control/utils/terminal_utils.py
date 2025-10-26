#!/usr/bin/env python

# ABOUTME: Terminal utility functions for motor bus calibration
# ABOUTME: Provides keyboard input checking and cursor manipulation

import platform
import select
import sys


def enter_pressed() -> bool:
    """Check if the enter key was pressed (non-blocking)."""
    if platform.system() == "Windows":
        import msvcrt

        if msvcrt.kbhit():
            key = msvcrt.getch()
            return key in (b"\r", b"\n")  # enter key
        return False
    else:
        return select.select([sys.stdin], [], [], 0)[0] and sys.stdin.readline().strip() == ""


def move_cursor_up(lines):
    """Move the cursor up by a specified number of lines."""
    print(f"\033[{lines}A", end="")
