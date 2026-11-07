"""High-precision calibration-free coordinate mapper from camera space to screen pixels."""
import math
import time
from typing import Optional, Tuple

import config


class ScreenMapper:
    """Maps normalized webcam coordinates within an ergonomic interaction box to physical screen pixels."""

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        box_x_min: float = config.INTERACTION_BOX_X_MIN,
        box_x_max: float = config.INTERACTION_BOX_X_MAX,
        box_y_min: float = config.INTERACTION_BOX_Y_MIN,
        box_y_max: float = config.INTERACTION_BOX_Y_MAX,
        enable_acceleration: bool = config.ENABLE_ACCELERATION,
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.box_x_min = box_x_min
        self.box_x_max = box_x_max
        self.box_y_min = box_y_min
        self.box_y_max = box_y_max
        self.enable_acceleration = enable_acceleration

        self.last_screen_pos: Optional[Tuple[float, float]] = None
        self.last_time: Optional[float] = None

    def map_normalized_to_screen(
        self, norm_x: float, norm_y: float, timestamp: Optional[float] = None
    ) -> Tuple[int, int]:
        """Maps (norm_x, norm_y) [0.0 - 1.0] to (screen_x, screen_y) [0 - screen_size]."""
        if timestamp is None:
            timestamp = time.perf_counter()

        # 1. Normalize within interaction box
        box_w = self.box_x_max - self.box_x_min
        box_h = self.box_y_max - self.box_y_min

        rel_x = (norm_x - self.box_x_min) / box_w
        rel_y = (norm_y - self.box_y_min) / box_h

        # Clamp to [0, 1]
        clamped_x = max(0.0, min(1.0, rel_x))
        clamped_y = max(0.0, min(1.0, rel_y))

        # 2. Linear projection to screen dimensions
        target_x = clamped_x * float(self.screen_width - 1)
        target_y = clamped_y * float(self.screen_height - 1)

        # 3. Dynamic acceleration curve if enabled
        if self.enable_acceleration and self.last_screen_pos is not None and self.last_time is not None:
            dt = timestamp - self.last_time
            if 1e-4 < dt < 0.2:
                dx = target_x - self.last_screen_pos[0]
                dy = target_y - self.last_screen_pos[1]
                speed = math.hypot(dx, dy) / dt  # pixels per second

                # Acceleration threshold: kick in when speed > 800 px/s
                if speed > 800.0:
                    boost = 1.0 + min(0.6, (speed - 800.0) / 2500.0)
                    target_x = self.last_screen_pos[0] + dx * boost
                    target_y = self.last_screen_pos[1] + dy * boost
                    target_x = max(0.0, min(float(self.screen_width - 1), target_x))
                    target_y = max(0.0, min(float(self.screen_height - 1), target_y))

        self.last_screen_pos = (target_x, target_y)
        self.last_time = timestamp

        return int(round(target_x)), int(round(target_y))

    def reset(self):
        """Resets velocity state."""
        self.last_screen_pos = None
        self.last_time = None
