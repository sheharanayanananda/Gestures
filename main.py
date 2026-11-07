"""Air Gestures: High-Precision Zero-Calibration Webcam Window Controller.

Features:
- Instant startup: zero calibration needed!
- Ergonomic virtual air-pad with pointer ballistics.
- Geometric window auto-grab (no simulated mouse clicks).
- Native macOS edge window snapping & tiling (Half, Maximize, Quadrants).
- 3-finger pinch (Thumb + Index + Middle) to grab and move windows.
"""
import argparse
import logging
import sys
import time

import cv2

import config
from src.gestures.filter import PointFilter2D
from src.gestures.pinch import PinchEvent, ThreeFingerDragDetector
from src.motion.mapper import ScreenMapper
from src.platform.macos_window import MacOSWindowManager
from src.platform.snapper import SnapZone
from src.ui.hud import HUDOverlay
from src.vision.camera import Camera
from src.vision.hand_tracker import HandTracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("GesturesMain")


def parse_args():
    parser = argparse.ArgumentParser(description="Zero-Calibration Air-Gesture Window Controller")
    parser.add_argument(
        "--camera",
        type=int,
        default=config.CAMERA_INDEX,
        help="Webcam device index (default: 0)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 1. Screen resolution & Window Manager
    window_manager = MacOSWindowManager()
    screen_w, screen_h = window_manager.get_main_screen_resolution()
    logger.info("Detected primary screen resolution: %dx%d", screen_w, screen_h)

    # 2. Motion Mapper (Zero Calibration)
    mapper = ScreenMapper(screen_w, screen_h)

    # 3. Vision & Gestures
    camera = Camera(camera_index=args.camera)
    if not camera.start():
        logger.error("Failed to initialize camera. Exiting.")
        sys.exit(1)

    hand_tracker = HandTracker()

    # 3-finger detector for window dragging
    drag_detector = ThreeFingerDragDetector(
        start_ratio=config.DRAG_3FINGER_START_RATIO,
        release_ratio=config.DRAG_3FINGER_RELEASE_RATIO,
    )

    point_filter = PointFilter2D(
        min_cutoff=config.FILTER_MIN_CUTOFF,
        beta=config.FILTER_BETA,
        d_cutoff=config.FILTER_DERIVATIVE_CUTOFF,
    )
    hud = HUDOverlay()

    window_name = "Air Gestures - Window Controller & Snapper"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    logger.info("Instant motion tracking active. Pinch 3 fingers over a window to grab and move it.")

    try:
        while True:
            ret, frame = camera.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            timestamp_ms = int(time.time() * 1000)
            hand_data = hand_tracker.process_frame(frame, timestamp_ms)

            drag_ratio = 1.0
            screen_cursor = None
            target_window_name = ""
            snap_zone = SnapZone.NONE

            if hand_data is not None:
                # 1. Evaluate 3-finger pinch (Thumb + Index + Middle)
                d_event, drag_ratio = drag_detector.update(
                    thumb_tip=hand_data.thumb_tip,
                    index_tip=hand_data.index_tip,
                    middle_tip=hand_data.middle_tip,
                    wrist=hand_data.wrist,
                    middle_mcp=hand_data.middle_mcp,
                )

                # 2. Select tracking point:
                # When dragging, anchor to 3-finger centroid to prevent fingertip flexing jumps
                if drag_detector.is_dragging:
                    target_x = (hand_data.thumb_tip[0] + hand_data.index_tip[0] + hand_data.middle_tip[0]) / 3.0
                    target_y = (hand_data.thumb_tip[1] + hand_data.index_tip[1] + hand_data.middle_tip[1]) / 3.0
                else:
                    target_x = hand_data.index_tip[0]
                    target_y = hand_data.index_tip[1]

                # 3. Map to screen pixel coordinates
                raw_sx, raw_sy = mapper.map_normalized_to_screen(target_x, target_y)

                # 4. High-precision 1€ filter jitter suppression
                smooth_sx, smooth_sy = point_filter.filter(raw_sx, raw_sy)
                screen_cursor = (int(round(smooth_sx)), int(round(smooth_sy)))

                # 5. Window Dragging & Snapping State Machine
                if d_event == PinchEvent.PINCH_DOWN:
                    window_manager.start_drag(screen_cursor[0], screen_cursor[1])
                    target_window_name = window_manager.active_window_name
                elif d_event == PinchEvent.PINCH_HOLD:
                    snap_zone = window_manager.update_drag(screen_cursor[0], screen_cursor[1])
                    target_window_name = window_manager.active_window_name
                elif d_event == PinchEvent.PINCH_UP:
                    snap_zone = window_manager.end_drag(screen_cursor[0], screen_cursor[1])
                    target_window_name = ""
                else:
                    # Hovering: non-invasively check what window is under the air cursor for HUD
                    win_info = window_manager.find_window_at_point(screen_cursor[0], screen_cursor[1])
                    if win_info:
                        target_window_name = win_info[1]
            else:
                # Hand lost: release active drag if in progress
                if drag_detector.is_dragging:
                    drag_detector.update(None, None, None, None, None)
                    if screen_cursor:
                        window_manager.end_drag(screen_cursor[0], screen_cursor[1])
                mapper.reset()
                point_filter.reset()

            # Render modern HUD overlay with live target and snap zones
            hud_frame = hud.render(
                frame=frame,
                hand_data=hand_data,
                drag_ratio=drag_ratio,
                is_dragging=drag_detector.is_dragging,
                target_window_name=target_window_name,
                snap_zone=snap_zone,
                screen_cursor=screen_cursor,
            )

            cv2.imshow(window_name, hud_frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):  # 'q' or Esc
                logger.info("Quit requested by user.")
                break

    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    finally:
        camera.stop()
        hand_tracker.close()
        cv2.destroyAllWindows()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    main()
