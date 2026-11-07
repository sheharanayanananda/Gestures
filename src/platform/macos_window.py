"""macOS native window interaction with geometric hit-testing and edge tiling/snapping."""
import logging
from typing import Optional, Tuple

import AppKit
import ApplicationServices
import Quartz

from src.platform.snapper import SnapZone, WindowRect, WindowSnapper

logger = logging.getLogger(__name__)


class MacOSWindowManager:
    """Non-invasive window hit-testing, direct geometric manipulation, and native edge snapping."""

    def __init__(self):
        screen_w, screen_h = self.get_main_screen_resolution()
        self.screen_width = screen_w
        self.screen_height = screen_h
        self.snapper = WindowSnapper(screen_w, screen_h)

        self.active_window = None
        self.active_window_name: str = ""
        self.orig_size: Optional[Tuple[float, float]] = None
        self.grab_offset: Tuple[float, float] = (0.0, 0.0)
        self.is_dragging = False
        self.is_snapped = False

    @staticmethod
    def get_main_screen_resolution() -> Tuple[int, int]:
        """Returns (width, height) of primary screen in points/pixels."""
        screen = AppKit.NSScreen.mainScreen()
        if screen:
            frame = screen.frame()
            return int(frame.size.width), int(frame.size.height)
        return 1920, 1080

    def find_window_at_point(
        self, x: float, y: float
    ) -> Optional[Tuple[object, str, Tuple[float, float], Tuple[float, float]]]:
        """Geometrically hit-tests on-screen application windows from front to back.

        Returns (ax_window, owner_name, position, size) or None.
        Does NOT click or interfere with the window contents.
        """
        options = (
            Quartz.kCGWindowListOptionOnScreenOnly
            | Quartz.kCGWindowListExcludeDesktopElements
        )
        window_list = Quartz.CGWindowListCopyWindowInfo(options, Quartz.kCGNullWindowID)
        if not window_list:
            return None

        for w in window_list:
            # Layer 0 are standard application windows
            if w.get(Quartz.kCGWindowLayer) != 0:
                continue

            owner = w.get(Quartz.kCGWindowOwnerName, "")
            # Skip python preview and system background daemons
            if owner in ("Python", "Window Server", "Dock"):
                continue

            bounds = w.get(Quartz.kCGWindowBounds, {})
            bx = bounds.get("X", 0)
            by = bounds.get("Y", 0)
            bw = bounds.get("Width", 0)
            bh = bounds.get("Height", 0)

            # Hit-test
            if bx <= x <= bx + bw and by <= y <= by + bh:
                pid = w.get(Quartz.kCGWindowOwnerPID)
                app = ApplicationServices.AXUIElementCreateApplication(pid)
                err, ax_windows = ApplicationServices.AXUIElementCopyAttributeValue(
                    app, ApplicationServices.kAXWindowsAttribute, None
                )
                if err == 0 and ax_windows:
                    # Target top window of this application
                    win = ax_windows[0]
                    pos = self.get_window_position(win) or (float(bx), float(by))
                    size = self.get_window_size(win) or (float(bw), float(bh))
                    return (win, owner, pos, size)

        return None

    def get_window_position(self, window_element) -> Optional[Tuple[float, float]]:
        """Queries (x, y) origin of window."""
        if not window_element:
            return None
        err, pos_val = ApplicationServices.AXUIElementCopyAttributeValue(
            window_element, ApplicationServices.kAXPositionAttribute, None
        )
        if err == 0 and pos_val:
            success, point = ApplicationServices.AXValueGetValue(
                pos_val, ApplicationServices.kAXValueCGPointType, None
            )
            if success:
                return float(point.x), float(point.y)
        return None

    def get_window_size(self, window_element) -> Optional[Tuple[float, float]]:
        """Queries (width, height) of window."""
        if not window_element:
            return None
        err, size_val = ApplicationServices.AXUIElementCopyAttributeValue(
            window_element, ApplicationServices.kAXSizeAttribute, None
        )
        if err == 0 and size_val:
            success, size = ApplicationServices.AXValueGetValue(
                size_val, ApplicationServices.kAXValueCGSizeType, None
            )
            if success:
                return float(size.width), float(size.height)
        return None

    def set_window_position(self, window_element, x: float, y: float) -> bool:
        """Sets window position directly using macOS Accessibility API."""
        if not window_element:
            return False
        point = Quartz.CGPoint(float(x), float(y))
        pos_val = ApplicationServices.AXValueCreate(
            ApplicationServices.kAXValueCGPointType, point
        )
        err = ApplicationServices.AXUIElementSetAttributeValue(
            window_element, ApplicationServices.kAXPositionAttribute, pos_val
        )
        return err == 0

    def set_window_size(self, window_element, width: float, height: float) -> bool:
        """Sets window size directly using macOS Accessibility API."""
        if not window_element:
            return False
        size = Quartz.CGSize(float(width), float(height))
        size_val = ApplicationServices.AXValueCreate(
            ApplicationServices.kAXValueCGSizeType, size
        )
        err = ApplicationServices.AXUIElementSetAttributeValue(
            window_element, ApplicationServices.kAXSizeAttribute, size_val
        )
        return err == 0

    def start_drag(self, cursor_x: float, cursor_y: float) -> bool:
        """Auto-grabs the window underneath the air cursor without clicking mouse."""
        result = self.find_window_at_point(cursor_x, cursor_y)
        if not result:
            return False

        win, owner_name, pos, size = result
        self.active_window = win
        self.active_window_name = owner_name
        self.orig_size = size
        self.grab_offset = (pos[0] - cursor_x, pos[1] - cursor_y)
        self.is_dragging = True

        # Bring window to front
        ApplicationServices.AXUIElementPerformAction(win, "AXRaise")
        logger.info("Auto-grabbed [%s] at %s (offset: %s)", owner_name, pos, self.grab_offset)
        return True

    def update_drag(self, cursor_x: float, cursor_y: float) -> SnapZone:
        """Translates window smoothly and returns any active edge snap zone."""
        if not self.is_dragging or not self.active_window:
            return SnapZone.NONE

        snap_zone = self.snapper.detect_snap_zone(cursor_x, cursor_y)

        # Direct window translation (No simulated mouse events!)
        target_x = cursor_x + self.grab_offset[0]
        target_y = cursor_y + self.grab_offset[1]
        self.set_window_position(self.active_window, target_x, target_y)

        # If window was previously tiled and dragged into free space, restore original dimensions
        if self.is_snapped and snap_zone == SnapZone.NONE and self.orig_size:
            self.set_window_size(self.active_window, self.orig_size[0], self.orig_size[1])
            self.is_snapped = False

        return snap_zone

    def end_drag(self, cursor_x: float, cursor_y: float) -> SnapZone:
        """Releases the grabbed window, applying edge snapping if dropped in a snap zone."""
        if not self.is_dragging or not self.active_window:
            self.is_dragging = False
            return SnapZone.NONE

        snap_zone = self.snapper.detect_snap_zone(cursor_x, cursor_y)

        if snap_zone != SnapZone.NONE:
            tile_rect: Optional[WindowRect] = self.snapper.get_tile_rect(snap_zone)
            if tile_rect:
                # Snap to tile geometry!
                self.set_window_size(self.active_window, tile_rect.width, tile_rect.height)
                self.set_window_position(self.active_window, tile_rect.x, tile_rect.y)
                self.is_snapped = True
                logger.info("Snapped [%s] to %s", self.active_window_name, snap_zone.value)
        else:
            logger.info("Dropped [%s] in free space", self.active_window_name)

        self.active_window = None
        self.active_window_name = ""
        self.is_dragging = False
        return snap_zone
