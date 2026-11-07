"""Webcam capture utility with optional mirroring."""
import logging
from typing import Optional, Tuple

import cv2
import numpy as np

import config

logger = logging.getLogger(__name__)


class Camera:
    """Manages OpenCV VideoCapture with mirroring and frame extraction."""

    def __init__(
        self,
        camera_index: int = config.CAMERA_INDEX,
        width: int = config.CAMERA_WIDTH,
        height: int = config.CAMERA_HEIGHT,
        fps: int = config.CAMERA_FPS,
        mirror: bool = True,
    ):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self.mirror = mirror
        self.cap: Optional[cv2.VideoCapture] = None

    def start(self) -> bool:
        """Opens camera and sets requested properties."""
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            logger.error("Could not open webcam index %d", self.camera_index)
            return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        logger.info("Camera started: index=%d (%dx%d)", self.camera_index, self.width, self.height)
        return True

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Reads a frame. If mirror is True, horizontally flips the frame."""
        if self.cap is None or not self.cap.isOpened():
            return False, None

        ret, frame = self.cap.read()
        if not ret or frame is None:
            return False, None

        if self.mirror:
            frame = cv2.flip(frame, 1)

        return True, frame

    def stop(self) -> None:
        """Releases the camera device."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            logger.info("Camera released.")
