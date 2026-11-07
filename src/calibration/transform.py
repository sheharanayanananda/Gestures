"""Perspective transformation and homography calibration.

Maps 2D air-pointing coordinates from webcam space to physical screen pixel coordinates.
"""
import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ScreenTransform:
    """Manages homography matrix between air coordinates and screen pixels."""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.homography_matrix: Optional[np.ndarray] = None
        self.calibration_points: Optional[List[Tuple[float, float]]] = None

    @property
    def is_calibrated(self) -> bool:
        return self.homography_matrix is not None

    def set_calibration_points(self, air_points: List[Tuple[float, float]]) -> bool:
        """Computes homography from 4 ordered air points:

        [Top-Left, Top-Right, Bottom-Right, Bottom-Left].
        Air points can be in normalized coordinates [0, 1] or camera pixel coords.
        """
        if len(air_points) != 4:
            raise ValueError(f"Expected 4 calibration points, got {len(air_points)}")

        src_pts = np.array(air_points, dtype=np.float32)
        dst_pts = np.array(
            [
                [0.0, 0.0],
                [float(self.screen_width), 0.0],
                [float(self.screen_width), float(self.screen_height)],
                [0.0, float(self.screen_height)],
            ],
            dtype=np.float32,
        )

        h_matrix, _ = cv2.findHomography(src_pts, dst_pts)
        if h_matrix is None:
            logger.error("Failed to compute homography matrix from given points.")
            return False

        self.homography_matrix = h_matrix
        self.calibration_points = [tuple(p) for p in air_points]
        return True

    def project(self, air_x: float, air_y: float, clamp: bool = True) -> Tuple[int, int]:
        """Maps an air coordinate (x, y) to screen coordinates (X_screen, Y_screen)."""
        if self.homography_matrix is None:
            raise RuntimeError("ScreenTransform is not calibrated yet.")

        pt = np.array([[[air_x, air_y]]], dtype=np.float32)
        projected = cv2.perspectiveTransform(pt, self.homography_matrix)
        screen_x = float(projected[0][0][0])
        screen_y = float(projected[0][0][1])

        if clamp:
            screen_x = max(0.0, min(screen_x, float(self.screen_width - 1)))
            screen_y = max(0.0, min(screen_y, float(self.screen_height - 1)))

        return int(round(screen_x)), int(round(screen_y))

    def save(self, filepath: Path) -> None:
        """Saves calibration to JSON."""
        if not self.is_calibrated:
            raise RuntimeError("Cannot save uncalibrated transform.")

        data = {
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "calibration_points": self.calibration_points,
            "homography_matrix": self.homography_matrix.tolist(),
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info("Saved calibration to %s", filepath)

    def load(self, filepath: Path) -> bool:
        """Loads calibration from JSON."""
        if not filepath.exists():
            return False
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.screen_width = data.get("screen_width", self.screen_width)
            self.screen_height = data.get("screen_height", self.screen_height)
            self.calibration_points = [tuple(p) for p in data["calibration_points"]]
            self.homography_matrix = np.array(data["homography_matrix"], dtype=np.float32)
            logger.info("Loaded calibration from %s", filepath)
            return True
        except Exception as e:
            logger.warning("Failed to load calibration from %s: %s", filepath, e)
            return False
