"""Unit tests for WindowSnapper edge detection and tile geometries."""
from src.platform.snapper import SnapZone, WindowSnapper


def test_snapper_edge_detection():
    snapper = WindowSnapper(screen_width=1920, screen_height=1080, menubar_height=30)

    # 1. Left Edge -> LEFT_HALF
    zone = snapper.detect_snap_zone(cursor_x=20, cursor_y=500)
    assert zone == SnapZone.LEFT_HALF
    rect = snapper.get_tile_rect(zone)
    assert rect.x == 0.0
    assert rect.y == 30.0
    assert rect.width == 960.0
    assert rect.height == 1050.0

    # 2. Right Edge -> RIGHT_HALF
    zone = snapper.detect_snap_zone(cursor_x=1910, cursor_y=500)
    assert zone == SnapZone.RIGHT_HALF
    rect = snapper.get_tile_rect(zone)
    assert rect.x == 960.0
    assert rect.width == 960.0

    # 3. Top Center -> MAXIMIZE
    zone = snapper.detect_snap_zone(cursor_x=960, cursor_y=40)
    assert zone == SnapZone.MAXIMIZE
    rect = snapper.get_tile_rect(zone)
    assert rect.x == 0.0
    assert rect.y == 30.0
    assert rect.width == 1920.0
    assert rect.height == 1050.0

    # 4. Corners -> Quadrants
    assert snapper.detect_snap_zone(cursor_x=30, cursor_y=40) == SnapZone.TOP_LEFT
    assert snapper.detect_snap_zone(cursor_x=1900, cursor_y=40) == SnapZone.TOP_RIGHT
    assert snapper.detect_snap_zone(cursor_x=30, cursor_y=1070) == SnapZone.BOTTOM_LEFT
    assert snapper.detect_snap_zone(cursor_x=1900, cursor_y=1070) == SnapZone.BOTTOM_RIGHT

    # 5. Interior / Free Space -> NONE
    assert snapper.detect_snap_zone(cursor_x=500, cursor_y=500) == SnapZone.NONE
