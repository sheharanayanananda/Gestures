"""Interactive 4-corner calibration wizard using pinch-to-confirm."""
import logging
import time
from typing import List, Optional, Tuple

import config
from src.calibration.transform import ScreenTransform
from src.gestures.pinch import PinchEvent

logger = logging.getLogger(__name__)


class CalibrationWizard:
    """Guides the user through pointing at 4 physical screen corners and confirming each with a pinch."""

    def __init__(self, transform: ScreenTransform):
        self.transform = transform
        self.current_step = 0  # 0 to 3
        self.captured_points: List[Tuple[float, float]] = []
        self.is_completed = False
        self.last_pinch_time = 0.0
        self.flash_until = 0.0  # Timestamp until which to show confirmation flash

    @property
    def current_corner_name(self) -> str:
        if self.current_step < len(config.CALIBRATION_CORNER_NAMES):
            return config.CALIBRATION_CORNER_NAMES[self.current_step]
        return "Complete"

    def reset(self):
        """Restarts calibration from corner 0."""
        self.current_step = 0
        self.captured_points = []
        self.is_completed = False
        self.last_pinch_time = 0.0
        logger.info("Calibration wizard reset.")

    def process_pinch(
        self,
        pinch_event: PinchEvent,
        pointing_pos: Tuple[float, float],
    ) -> bool:
        """Processes hand input during calibration.

        pointing_pos is (x, y) in camera space (normalized or pixel).
        Returns True if a corner was captured on this frame.
        """
        if self.is_completed:
            return False

        now = time.time()
        # Cooldown between successive corner registrations
        if now - self.last_pinch_time < config.CALIBRATION_COOLDOWN_SEC:
            return False

        if pinch_event == PinchEvent.PINCH_DOWN:
            self.last_pinch_time = now
            self.flash_until = now + 0.35  # 350ms green flash
            self.captured_points.append(pointing_pos)
            logger.info(
                "Captured corner %d (%s) at %s",
                self.current_step + 1,
                self.current_corner_name,
                pointing_pos,
            )
            self.current_step += 1

            if self.current_step >= 4:
                # All 4 corners registered!
                success = self.transform.set_calibration_points(self.captured_points)
                if success:
                    self.transform.save(config.CALIBRATION_FILE)
                    self.is_completed = True
                    logger.info("4-corner calibration successfully completed and saved.")
                else:
                    logger.error("Failed to solve homography matrix. Please retry calibration.")
                    self.reset()
            return True

        return False
