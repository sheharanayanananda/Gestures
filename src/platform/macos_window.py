"""macOS native window interaction with real-time fluid edge snapping and tiling."""
import logging
from typing import Optional, Tuple

import AppKit
import ApplicationServices
import Quartz

from src.platform.snapper import SnapZone, WindowRect, WindowSnapper

logger = logging.getLogger(__name__)


class MacOSWindowManager:
    """Non-invasive window hit-testing, direct geometric manipulation, and real-time fluid edge snapping."""

    def __init__(self):
        screen_w, screen_h = self.get_main_screen_resolution()
        self.screen_width = screen_w
        self.screen_height = screen_h
        self.snapper = WindowSnapper(screen_w, screen_h)

        self.active_window = None
        self.active_window_name: str = ""
        self.orig_size: Optional[Tuple[float, float]] = None
        self.orig_pos: Optional[Tuple[float, float]] = None
        self.grab_offset: Tuple[float, float] = (0.0, 0.0)
        self.is_dragging = False
        self.current_snap_zone: SnapZone = SnapZone.NONE

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
            if w.get(Quartz.kCGWindowLayer) != 0:
                continue

            owner = w.get(Quartz.kCGWindowOwnerName, "")
            if owner in ("Python", "Window Server", "Dock"):
                continue

            bounds = w.get(Quartz.kCGWindowBounds, {})
            bx = bounds.get("X", 0)
            by = bounds.get("Y", 0)
            bw = bounds.get("Width", 0)
            bh = bounds.get("Height", 0)

            if bx <= x <= bx + bw and by <= y <= by + bh:
                pid = w.get(Quartz.kCGWindowOwnerPID)
                app = ApplicationServices.AXUIElementCreateApplication(pid)
                err, ax_windows = ApplicationServices.AXUIElementCopyAttributeValue(
                    app, ApplicationServices.kAXWindowsAttribute, None
                )
                if err == 0 and ax_windows:
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
        self.orig_pos = pos
        self.grab_offset = (pos[0] - cursor_x, pos[1] - cursor_y)
        self.is_dragging = True
        self.current_snap_zone = SnapZone.NONE

        # Bring window to front
        ApplicationServices.AXUIElementPerformAction(win, "AXRaise")
        logger.info("Auto-grabbed [%s] at %s (orig_size: %s)", owner_name, pos, size)
        return True

    def update_drag(self, cursor_x: float, cursor_y: float) -> SnapZone:
        """Translates window smoothly and triggers REAL-TIME fluid snapping when entering any edge/corner."""
        if not self.is_dragging or not self.active_window:
            return SnapZone.NONE

        new_zone = self.snapper.detect_snap_zone(cursor_x, cursor_y, self.current_snap_zone)

        # Zone Transition Check
        if new_zone != self.current_snap_zone:
            if new_zone != SnapZone.NONE:
                # Entering a Snap Zone: Immediately morph and position the window to the tile!
                tile_rect: Optional[WindowRect] = self.snapper.get_tile_rect(new_zone)
                if tile_rect:
                    self.set_window_size(self.active_window, tile_rect.width, tile_rect.height)
                    self.set_window_position(self.active_window, tile_rect.x, tile_rect.y)
                    self.current_snap_zone = new_zone
                    logger.info("Fluid Snap: [%s] snapped to %s", self.active_window_name, new_zone.value)
            else:
                # Exiting Snap Zone back into Free Space: Restore original floating dimensions!
                if self.orig_size:
                    self.set_window_size(self.active_window, self.orig_size[0], self.orig_size[1])
                    # Re-anchor grab offset so window follows hand naturally
                    self.grab_offset = (-self.orig_size[0] / 2.0, -25.0)
                    target_x = cursor_x + self.grab_offset[0]
                    target_y = cursor_y + self.grab_offset[1]
                    self.set_window_position(self.active_window, target_x, target_y)
                self.current_snap_zone = SnapZone.NONE
                logger.info("Fluid Un-snap: [%s] restored to floating", self.active_window_name)
        else:
            # Continuing within the same zone
            if self.current_snap_zone == SnapZone.NONE:
                # Free space movement: smooth translation following hand offset
                target_x = cursor_x + self.grab_offset[0]
                target_y = cursor_y + self.grab_offset[1]
                self.set_window_position(self.active_window, target_x, target_y)

        return self.current_snap_zone

    def end_drag(self, cursor_x: float, cursor_y: float) -> SnapZone:
        """Commits the window in its current snapped or floating position upon release."""
        if not self.is_dragging or not self.active_window:
            self.is_dragging = False
            return SnapZone.NONE

        final_zone = self.current_snap_zone
        if final_zone != SnapZone.NONE:
            logger.info("Committed [%s] in snap tile: %s", self.active_window_name, final_zone.value)
        else:
            logger.info("Committed [%s] in free space", self.active_window_name)

        self.active_window = None
        self.active_window_name = ""
        self.is_dragging = False
        self.current_snap_zone = SnapZone.NONE
        return final_zone
