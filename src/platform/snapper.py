"""macOS Window Snapping and Tiling Engine.

Computes snap tile targets (Left Half, Right Half, Maximize, Quadrants)
when dragging windows near screen edges.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class SnapZone(Enum):
    NONE = "none"
    LEFT_HALF = "left_half"
    RIGHT_HALF = "right_half"
    MAXIMIZE = "maximize"
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"


@dataclass
class WindowRect:
    x: float
    y: float
    width: float
    height: float


class WindowSnapper:
    """Detects when an air cursor is in an edge snap zone and calculates target tile geometries."""

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        menubar_height: int = 33,
        edge_threshold: int = 40,
        corner_threshold: int = 65,
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.menubar_height = menubar_height
        self.edge_threshold = edge_threshold
        self.corner_threshold = corner_threshold

    @property
    def usable_height(self) -> float:
        """Usable height below menubar."""
        return float(self.screen_height - self.menubar_height)

    def detect_snap_zone(self, cursor_x: float, cursor_y: float) -> SnapZone:
        """Determines if the cursor is within an edge/corner snapping zone."""
        sw = float(self.screen_width)
        sh = float(self.screen_height)
        m = float(self.menubar_height)

        is_left = cursor_x <= self.edge_threshold
        is_right = cursor_x >= (sw - self.edge_threshold)
        is_top = cursor_y <= (m + self.edge_threshold)
        is_bottom = cursor_y >= (sh - self.edge_threshold)

        is_corner_left = cursor_x <= self.corner_threshold
        is_corner_right = cursor_x >= (sw - self.corner_threshold)
        is_corner_top = cursor_y <= (m + self.corner_threshold)
        is_corner_bottom = cursor_y >= (sh - self.corner_threshold)

        # 1. Corner Quadrants
        if is_corner_left and is_corner_top:
            return SnapZone.TOP_LEFT
        if is_corner_right and is_corner_top:
            return SnapZone.TOP_RIGHT
        if is_corner_left and is_corner_bottom:
            return SnapZone.BOTTOM_LEFT
        if is_corner_right and is_corner_bottom:
            return SnapZone.BOTTOM_RIGHT

        # 2. Maximize (top edge, center section)
        if is_top and (sw * 0.25 <= cursor_x <= sw * 0.75):
            return SnapZone.MAXIMIZE

        # 3. Left / Right Halves
        if is_left:
            return SnapZone.LEFT_HALF
        if is_right:
            return SnapZone.RIGHT_HALF

        return SnapZone.NONE

    def get_tile_rect(self, zone: SnapZone) -> Optional[WindowRect]:
        """Returns the target (x, y, width, height) for a given SnapZone."""
        sw = float(self.screen_width)
        m = float(self.menubar_height)
        uh = self.usable_height
        half_w = sw / 2.0
        half_h = uh / 2.0

        if zone == SnapZone.LEFT_HALF:
            return WindowRect(x=0.0, y=m, width=half_w, height=uh)
        elif zone == SnapZone.RIGHT_HALF:
            return WindowRect(x=half_w, y=m, width=half_w, height=uh)
        elif zone == SnapZone.MAXIMIZE:
            return WindowRect(x=0.0, y=m, width=sw, height=uh)
        elif zone == SnapZone.TOP_LEFT:
            return WindowRect(x=0.0, y=m, width=half_w, height=half_h)
        elif zone == SnapZone.TOP_RIGHT:
            return WindowRect(x=half_w, y=m, width=half_w, height=half_h)
        elif zone == SnapZone.BOTTOM_LEFT:
            return WindowRect(x=0.0, y=m + half_h, width=half_w, height=half_h)
        elif zone == SnapZone.BOTTOM_RIGHT:
            return WindowRect(x=half_w, y=m + half_h, width=half_w, height=half_h)

        return None
