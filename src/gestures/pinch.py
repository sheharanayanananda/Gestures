"""Pinch and Multi-Finger Gesture detection with scale-invariant metric and hysteresis."""
from enum import Enum
import math
from typing import Optional, Tuple


class PinchEvent(Enum):
    NONE = "none"
    PINCH_DOWN = "pinch_down"  # Triggered once on the exact frame pinch engages
    PINCH_HOLD = "pinch_hold"  # Maintained while pinch continues
    PINCH_UP = "pinch_up"      # Triggered once on the exact frame pinch releases


def euclidean_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Euclidean distance in 2D."""
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


class PinchDetector:
    """2-Finger Pinch Detector (Thumb tip + Index tip).

    Used for calibration point confirmation.
    """

    def __init__(
        self,
        start_ratio: float = 0.28,
        release_ratio: float = 0.38,
    ):
        self.start_ratio = start_ratio
        self.release_ratio = release_ratio
        self.is_pinching = False

    def compute_pinch_ratio(
        self,
        thumb_tip: Tuple[float, float],
        index_tip: Tuple[float, float],
        wrist: Tuple[float, float],
        middle_mcp: Tuple[float, float],
    ) -> float:
        """Computes the normalized ratio of index-thumb distance to palm size."""
        finger_dist = euclidean_distance(thumb_tip, index_tip)
        palm_size = euclidean_distance(wrist, middle_mcp)

        if palm_size < 1e-5:
            return 1.0

        return finger_dist / palm_size

    def update(
        self,
        thumb_tip: Optional[Tuple[float, float]],
        index_tip: Optional[Tuple[float, float]],
        wrist: Optional[Tuple[float, float]],
        middle_mcp: Optional[Tuple[float, float]],
    ) -> Tuple[PinchEvent, float]:
        """Updates 2-finger pinch state. Returns (PinchEvent, ratio)."""
        if None in (thumb_tip, index_tip, wrist, middle_mcp):
            if self.is_pinching:
                self.is_pinching = False
                return PinchEvent.PINCH_UP, 1.0
            return PinchEvent.NONE, 1.0

        ratio = self.compute_pinch_ratio(thumb_tip, index_tip, wrist, middle_mcp)

        if not self.is_pinching:
            if ratio <= self.start_ratio:
                self.is_pinching = True
                return PinchEvent.PINCH_DOWN, ratio
            return PinchEvent.NONE, ratio
        else:
            if ratio > self.release_ratio:
                self.is_pinching = False
                return PinchEvent.PINCH_UP, ratio
            return PinchEvent.PINCH_HOLD, ratio

    def reset(self):
        self.is_pinching = False


class ThreeFingerDragDetector:
    """3-Finger Drag Detector (Thumb + Index + Middle fingertips pinched together).

    Used exclusively for window grabbing and dragging.
    Ensures all 3 fingertips are close together, separating it from 2-finger pointing/calibration.
    """

    def __init__(
        self,
        start_ratio: float = 0.35,
        release_ratio: float = 0.45,
    ):
        self.start_ratio = start_ratio
        self.release_ratio = release_ratio
        self.is_dragging = False

    def compute_three_finger_ratio(
        self,
        thumb_tip: Tuple[float, float],
        index_tip: Tuple[float, float],
        middle_tip: Tuple[float, float],
        wrist: Tuple[float, float],
        middle_mcp: Tuple[float, float],
    ) -> float:
        """Computes the maximum pairwise distance between the 3 fingertips normalized by palm size."""
        d_ti = euclidean_distance(thumb_tip, index_tip)
        d_tm = euclidean_distance(thumb_tip, middle_tip)
        d_im = euclidean_distance(index_tip, middle_tip)
        palm_size = euclidean_distance(wrist, middle_mcp)

        if palm_size < 1e-5:
            return 1.0

        max_spread = max(d_ti, d_tm, d_im)
        return max_spread / palm_size

    def update(
        self,
        thumb_tip: Optional[Tuple[float, float]],
        index_tip: Optional[Tuple[float, float]],
        middle_tip: Optional[Tuple[float, float]],
        wrist: Optional[Tuple[float, float]],
        middle_mcp: Optional[Tuple[float, float]],
    ) -> Tuple[PinchEvent, float]:
        """Updates 3-finger drag state. Returns (PinchEvent, ratio)."""
        if None in (thumb_tip, index_tip, middle_tip, wrist, middle_mcp):
            if self.is_dragging:
                self.is_dragging = False
                return PinchEvent.PINCH_UP, 1.0
            return PinchEvent.NONE, 1.0

        ratio = self.compute_three_finger_ratio(
            thumb_tip, index_tip, middle_tip, wrist, middle_mcp
        )

        if not self.is_dragging:
            if ratio <= self.start_ratio:
                self.is_dragging = True
                return PinchEvent.PINCH_DOWN, ratio
            return PinchEvent.NONE, ratio
        else:
            if ratio > self.release_ratio:
                self.is_dragging = False
                return PinchEvent.PINCH_UP, ratio
            return PinchEvent.PINCH_HOLD, ratio

    def reset(self):
        self.is_dragging = False
