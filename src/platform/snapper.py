"""macOS Window Snapping and Tiling Engine.

Computes real-time snap tile targets for all 9 placements:
- Upper Left, Upper Right, Lower Left, Lower Right (Quadrants)
- Left Half, Right Half (Vertical splits)
- Upper Half, Lower Half (Horizontal splits)
- Full Screen (Maximize)
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SnapZone(Enum):
    NONE = "none"
    UPPER_LEFT = "upper_left"
    UPPER_RIGHT = "upper_right"
    LOWER_LEFT = "lower_left"
    LOWER_RIGHT = "lower_right"
    LEFT_HALF = "left_half"
    RIGHT_HALF = "right_half"
    UPPER_HALF = "upper_half"
    LOWER_HALF = "lower_half"
    FULL_SCREEN = "full_screen"


@dataclass
class WindowRect:
    x: float
    y: float
    width: float
    height: float


class WindowSnapper:
    """Detects when an air cursor enters any of the 9 edge snap zones and calculates target tile geometries."""

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        menubar_height: int = 33,
        edge_threshold: int = 75,
        corner_threshold: int = 120,
        unsnap_threshold: int = 110,
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.menubar_height = menubar_height
        self.edge_threshold = edge_threshold
        self.corner_threshold = corner_threshold
        self.unsnap_threshold = unsnap_threshold

    @property
    def usable_height(self) -> float:
        """Usable height below menubar."""
        return float(self.screen_height - self.menubar_height)

    def detect_snap_zone(
        self, cursor_x: float, cursor_y: float, current_zone: SnapZone = SnapZone.NONE
    ) -> SnapZone:
        """Determines active snap zone with hysteresis to prevent flickering when pulling away."""
        sw = float(self.screen_width)
        sh = float(self.screen_height)
        m = float(self.menubar_height)

        # Hysteresis: if already snapped, require pulling inward beyond unsnap_threshold
        effective_edge = (
            float(self.unsnap_threshold)
            if current_zone != SnapZone.NONE
            else float(self.edge_threshold)
        )
        effective_corner = (
            float(self.unsnap_threshold + 20)
            if current_zone != SnapZone.NONE
            else float(self.corner_threshold)
        )

        is_left_edge = cursor_x <= effective_edge
        is_right_edge = cursor_x >= (sw - effective_edge)
        is_top_edge = cursor_y <= (m + effective_edge)
        is_bottom_edge = cursor_y >= (sh - effective_edge)

        is_corner_left = cursor_x <= effective_corner
        is_corner_right = cursor_x >= (sw - effective_corner)
        is_corner_top = cursor_y <= (m + effective_corner)
        is_corner_bottom = cursor_y >= (sh - effective_corner)

        # 1. Four Corner Quadrants (Upper Left, Upper Right, Lower Left, Lower Right)
        if is_corner_left and is_corner_top:
            return SnapZone.UPPER_LEFT
        if is_corner_right and is_corner_top:
            return SnapZone.UPPER_RIGHT
        if is_corner_left and is_corner_bottom:
            return SnapZone.LOWER_LEFT
        if is_corner_right and is_corner_bottom:
            return SnapZone.LOWER_RIGHT

        # 2. Top Edge: Full Screen (Center) vs Upper Half (Outer)
        if is_top_edge:
            if sw * 0.35 <= cursor_x <= sw * 0.65:
                return SnapZone.FULL_SCREEN
            else:
                return SnapZone.UPPER_HALF

        # 3. Bottom Edge: Lower Half
        if is_bottom_edge:
            return SnapZone.LOWER_HALF

        # 4. Vertical Halves: Left Half & Right Half
        if is_left_edge:
            return SnapZone.LEFT_HALF
        if is_right_edge:
            return SnapZone.RIGHT_HALF

        return SnapZone.NONE

    def get_tile_rect(self, zone: SnapZone) -> Optional[WindowRect]:
        """Calculates exact (x, y, width, height) for any of the 9 snap placements."""
        sw = float(self.screen_width)
        m = float(self.menubar_height)
        uh = self.usable_height
        half_w = sw / 2.0
        half_h = uh / 2.0

        if zone == SnapZone.UPPER_LEFT:
            return WindowRect(x=0.0, y=m, width=half_w, height=half_h)
        elif zone == SnapZone.UPPER_RIGHT:
            return WindowRect(x=half_w, y=m, width=half_w, height=half_h)
        elif zone == SnapZone.LOWER_LEFT:
            return WindowRect(x=0.0, y=m + half_h, width=half_w, height=half_h)
        elif zone == SnapZone.LOWER_RIGHT:
            return WindowRect(x=half_w, y=m + half_h, width=half_w, height=half_h)
        elif zone == SnapZone.LEFT_HALF:
            return WindowRect(x=0.0, y=m, width=half_w, height=uh)
        elif zone == SnapZone.RIGHT_HALF:
            return WindowRect(x=half_w, y=m, width=half_w, height=uh)
        elif zone == SnapZone.UPPER_HALF:
            return WindowRect(x=0.0, y=m, width=sw, height=half_h)
        elif zone == SnapZone.LOWER_HALF:
            return WindowRect(x=0.0, y=m + half_h, width=sw, height=half_h)
        elif zone == SnapZone.FULL_SCREEN:
            return WindowRect(x=0.0, y=m, width=sw, height=uh)

        return None
