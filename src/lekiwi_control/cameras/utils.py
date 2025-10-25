#!/usr/bin/env python

# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import platform

from .camera import Camera
from .configs import CameraConfig, Cv2Rotation


def make_cameras_from_configs(camera_configs: dict[str, CameraConfig]) -> dict[str, Camera]:
    """Create camera instances from configuration dict.

    Currently only supports OpenCV cameras.

    Args:
        camera_configs: Dict mapping camera names to configuration objects

    Returns:
        Dict mapping camera names to Camera instances
    """
    from .opencv import OpenCVCamera

    cameras: dict[str, Camera] = {}

    for key, cfg in camera_configs.items():
        cameras[key] = OpenCVCamera(cfg)

    return cameras


def get_cv2_rotation(rotation: Cv2Rotation) -> int | None:
    import cv2  # type: ignore  # TODO: add type stubs for OpenCV

    if rotation == Cv2Rotation.ROTATE_90:
        return int(cv2.ROTATE_90_CLOCKWISE)
    elif rotation == Cv2Rotation.ROTATE_180:
        return int(cv2.ROTATE_180)
    elif rotation == Cv2Rotation.ROTATE_270:
        return int(cv2.ROTATE_90_COUNTERCLOCKWISE)
    else:
        return None


def get_cv2_backend() -> int:
    import cv2

    if platform.system() == "Windows":
        return int(cv2.CAP_MSMF)  # Use MSMF for Windows instead of AVFOUNDATION
    # elif platform.system() == "Darwin":  # macOS
    #     return cv2.CAP_AVFOUNDATION
    else:  # Linux and others
        return int(cv2.CAP_ANY)
