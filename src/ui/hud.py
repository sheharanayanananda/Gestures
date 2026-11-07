"""Heads-Up Display (HUD) overlay: real-time visual feedback for zero-calibration gestures & snapping."""
from typing import Optional, Tuple

import cv2
import numpy as np

import config
from src.platform.snapper import SnapZone
from src.vision.hand_tracker import HandData


class HUDOverlay:
    """Draws real-time interaction zones, finger skeletons, tracking reticles, window target badges, and snap zones."""

    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def render(
        self,
        frame: np.ndarray,
        hand_data: Optional[HandData],
        drag_ratio: float,
        is_dragging: bool,
        target_window_name: str = "",
        snap_zone: SnapZone = SnapZone.NONE,
        screen_cursor: Optional[Tuple[int, int]] = None,
    ) -> np.ndarray:
        """Renders HUD elements onto the camera feed."""
        h, w = frame.shape[:2]
        display = frame.copy()

        # 1. Draw Ergonomic Interaction Zone (Air-Pad)
        self._draw_interaction_box(display, w, h)

        # 2. Draw Hand & 3-Finger Gestures
        if hand_data is not None:
            self._draw_hand(display, hand_data, drag_ratio, is_dragging)

        # 3. Draw Snap Target Preview if active
        if is_dragging and snap_zone != SnapZone.NONE:
            self._draw_snap_indicator(display, snap_zone, w, h)

        # 4. Draw Top Status Banner with Target Window Name
        self._draw_status_bar(
            display, screen_cursor, is_dragging, target_window_name, snap_zone, w, h
        )

        return display

    def _draw_interaction_box(self, img: np.ndarray, w: int, h: int):
        """Draws a stylish, semi-transparent guide for the active air-pad."""
        bx1 = int(config.INTERACTION_BOX_X_MIN * w)
        by1 = int(config.INTERACTION_BOX_Y_MIN * h)
        bx2 = int(config.INTERACTION_BOX_X_MAX * w)
        by2 = int(config.INTERACTION_BOX_Y_MAX * h)

        cv2.rectangle(img, (bx1, by1), (bx2, by2), (60, 60, 60), 1)

        corner_len = 20
        c_color = (0, 200, 255)
        thick = 2
        # Top-Left
        cv2.line(img, (bx1, by1), (bx1 + corner_len, by1), c_color, thick)
        cv2.line(img, (bx1, by1), (bx1, by1 + corner_len), c_color, thick)
        # Top-Right
        cv2.line(img, (bx2, by1), (bx2 - corner_len, by1), c_color, thick)
        cv2.line(img, (bx2, by1), (bx2, by1 + corner_len), c_color, thick)
        # Bottom-Left
        cv2.line(img, (bx1, by2), (bx1 + corner_len, by2), c_color, thick)
        cv2.line(img, (bx1, by2), (bx1, by2 - corner_len), c_color, thick)
        # Bottom-Right
        cv2.line(img, (bx2, by2), (bx2 - corner_len, by2), c_color, thick)
        cv2.line(img, (bx2, by2), (bx2, by2 - corner_len), c_color, thick)

        cv2.putText(
            img,
            "Air Screen Zone",
            (bx1 + 8, by1 - 8),
            self.font,
            0.45,
            (140, 140, 140),
            1,
            cv2.LINE_AA,
        )

    def _draw_hand(
        self,
        img: np.ndarray,
        hand_data: HandData,
        drag_ratio: float,
        is_dragging: bool,
    ):
        """Draws the 3 active fingertips (Thumb, Index, Middle) and pinch metric."""
        idx_pt = hand_data.index_pixel_pos
        thb_pt = hand_data.thumb_pixel_pos
        mid_pt = hand_data.middle_pixel_pos

        line_color = (0, 70, 255) if is_dragging else (255, 200, 0)
        cv2.line(img, thb_pt, idx_pt, line_color, 2)
        cv2.line(img, thb_pt, mid_pt, line_color, 2)
        cv2.line(img, idx_pt, mid_pt, line_color, 2)

        # Fingertip circles
        cv2.circle(img, idx_pt, 7, (0, 255, 255), -1)   # Cyan Index
        cv2.circle(img, thb_pt, 7, (255, 120, 0), -1)   # Orange Thumb
        cv2.circle(img, mid_pt, 7, (255, 255, 0), -1)   # Yellow Middle

        # Centroid reticle
        cx = (idx_pt[0] + thb_pt[0] + mid_pt[0]) // 3
        cy = (idx_pt[1] + thb_pt[1] + mid_pt[1]) // 3

        reticle_color = (0, 70, 255) if is_dragging else (0, 255, 0)
        cv2.circle(img, (cx, cy), 14, reticle_color, 2)
        cv2.circle(img, (cx, cy), 4, reticle_color, -1)

        # 3-finger pinch progress bar
        bar_w = 64
        bar_h = 6
        bx, by = cx - 32, cy - 25
        fill_ratio = min(1.0, max(0.0, drag_ratio / 0.6))
        cv2.rectangle(img, (bx, by), (bx + bar_w, by + bar_h), (80, 80, 80), -1)
        bar_color = (0, 70, 255) if is_dragging else (0, 255, 0)
        cv2.rectangle(img, (bx, by), (bx + int(bar_w * fill_ratio), by + bar_h), bar_color, -1)

    def _draw_snap_indicator(self, img: np.ndarray, zone: SnapZone, w: int, h: int):
        """Highlights the active snap edge on the camera preview."""
        overlay = img.copy()
        edge_thickness = 16
        color = (0, 220, 255)

        if zone == SnapZone.LEFT_HALF:
            cv2.rectangle(overlay, (0, 0), (edge_thickness, h), color, -1)
        elif zone == SnapZone.RIGHT_HALF:
            cv2.rectangle(overlay, (w - edge_thickness, 0), (w, h), color, -1)
        elif zone == SnapZone.MAXIMIZE:
            cv2.rectangle(overlay, (0, 0), (w, edge_thickness), color, -1)
        elif zone == SnapZone.TOP_LEFT:
            cv2.rectangle(overlay, (0, 0), (edge_thickness * 3, edge_thickness * 3), color, -1)
        elif zone == SnapZone.TOP_RIGHT:
            cv2.rectangle(overlay, (w - edge_thickness * 3, 0), (w, edge_thickness * 3), color, -1)
        elif zone == SnapZone.BOTTOM_LEFT:
            cv2.rectangle(overlay, (0, h - edge_thickness * 3), (edge_thickness * 3, h), color, -1)
        elif zone == SnapZone.BOTTOM_RIGHT:
            cv2.rectangle(overlay, (w - edge_thickness * 3, h - edge_thickness * 3), (w, h), color, -1)

        cv2.addWeighted(overlay, 0.45, img, 0.55, 0, img)

    def _draw_status_bar(
        self,
        img: np.ndarray,
        screen_cursor: Optional[Tuple[int, int]],
        is_dragging: bool,
        target_name: str,
        snap_zone: SnapZone,
        w: int,
        h: int,
    ):
        """Top status bar with mode, target window, snap zone, and cursor coordinates."""
        cv2.rectangle(img, (0, 0), (w, 58), (20, 20, 20), -1)

        if is_dragging:
            if snap_zone != SnapZone.NONE:
                status_text = f"SNAP TARGET: [{snap_zone.value.upper()}] - Release to Tile"
                status_color = (0, 220, 255)
            else:
                target_str = f"[{target_name}]" if target_name else ""
                status_text = f"GRABBED {target_str} - Move to drag | Release to drop"
                status_color = (0, 100, 255)
        else:
            if target_name:
                status_text = f"HOVERING: Window under finger -> [{target_name}] (Pinch 3 to Grab)"
                status_color = (0, 255, 120)
            else:
                status_text = "HOVERING: Free Space (Pinch 3 over a window to grab)"
                status_color = (0, 200, 0)

        cv2.putText(img, status_text, (20, 36), self.font, 0.54, status_color, 2, cv2.LINE_AA)

        if screen_cursor:
            cursor_str = f"({screen_cursor[0]}, {screen_cursor[1]})"
            cv2.putText(img, cursor_str, (w - 180, 36), self.font, 0.55, (220, 220, 220), 1, cv2.LINE_AA)

        # Bottom help
        cv2.putText(
            img,
            "[q] Quit",
            (20, h - 20),
            self.font,
            0.5,
            (160, 160, 160),
            1,
            cv2.LINE_AA,
        )
