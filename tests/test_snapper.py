"""Unit tests for WindowSnapper covering all 9 placements and hysteresis."""
from src.platform.snapper import SnapZone, WindowSnapper


def test_snapper_all_9_placements():
    sw, sh, m = 1920, 1080, 30
    snapper = WindowSnapper(
        screen_width=sw,
        screen_height=sh,
        menubar_height=m,
        edge_threshold=75,
        corner_threshold=120,
    )
    uh = float(sh - m)
    half_w = sw / 2.0
    half_h = uh / 2.0

    # 1. UPPER_LEFT
    z = snapper.detect_snap_zone(cursor_x=50, cursor_y=50)
    assert z == SnapZone.UPPER_LEFT
    r = snapper.get_tile_rect(z)
    assert (r.x, r.y, r.width, r.height) == (0.0, 30.0, half_w, half_h)

    # 2. UPPER_RIGHT
    z = snapper.detect_snap_zone(cursor_x=1880, cursor_y=50)
    assert z == SnapZone.UPPER_RIGHT
    r = snapper.get_tile_rect(z)
    assert (r.x, r.y, r.width, r.height) == (half_w, 30.0, half_w, half_h)

    # 3. LOWER_LEFT
    z = snapper.detect_snap_zone(cursor_x=50, cursor_y=1050)
    assert z == SnapZone.LOWER_LEFT
    r = snapper.get_tile_rect(z)
    assert (r.x, r.y, r.width, r.height) == (0.0, 30.0 + half_h, half_w, half_h)

    # 4. LOWER_RIGHT
    z = snapper.detect_snap_zone(cursor_x=1880, cursor_y=1050)
    assert z == SnapZone.LOWER_RIGHT
    r = snapper.get_tile_rect(z)
    assert (r.x, r.y, r.width, r.height) == (half_w, 30.0 + half_h, half_w, half_h)

    # 5. LEFT_HALF
    z = snapper.detect_snap_zone(cursor_x=40, cursor_y=500)
    assert z == SnapZone.LEFT_HALF
    r = snapper.get_tile_rect(z)
    assert (r.x, r.y, r.width, r.height) == (0.0, 30.0, half_w, uh)

    # 6. RIGHT_HALF
    z = snapper.detect_snap_zone(cursor_x=1890, cursor_y=500)
    assert z == SnapZone.RIGHT_HALF
    r = snapper.get_tile_rect(z)
    assert (r.x, r.y, r.width, r.height) == (half_w, 30.0, half_w, uh)

    # 7. FULL_SCREEN (top center)
    z = snapper.detect_snap_zone(cursor_x=960, cursor_y=45)
    assert z == SnapZone.FULL_SCREEN
    r = snapper.get_tile_rect(z)
    assert (r.x, r.y, r.width, r.height) == (0.0, 30.0, float(sw), uh)

    # 8. UPPER_HALF (top edge, off-center)
    z = snapper.detect_snap_zone(cursor_x=400, cursor_y=45)
    assert z == SnapZone.UPPER_HALF
    r = snapper.get_tile_rect(z)
    assert (r.x, r.y, r.width, r.height) == (0.0, 30.0, float(sw), half_h)

    # 9. LOWER_HALF (bottom edge center)
    z = snapper.detect_snap_zone(cursor_x=960, cursor_y=1060)
    assert z == SnapZone.LOWER_HALF
    r = snapper.get_tile_rect(z)
    assert (r.x, r.y, r.width, r.height) == (0.0, 30.0 + half_h, float(sw), half_h)

    # 10. NONE (free interior)
    assert snapper.detect_snap_zone(cursor_x=960, cursor_y=500) == SnapZone.NONE


def test_snapper_hysteresis():
    snapper = WindowSnapper(screen_width=1920, screen_height=1080, edge_threshold=75, unsnap_threshold=110)

    # When starting from NONE, entering at 70px triggers LEFT_HALF
    assert snapper.detect_snap_zone(70, 500, current_zone=SnapZone.NONE) == SnapZone.LEFT_HALF

    # But at 90px from edge:
    # If starting from NONE: 90px > 75px -> NONE
    assert snapper.detect_snap_zone(90, 500, current_zone=SnapZone.NONE) == SnapZone.NONE
    # If already in LEFT_HALF: 90px < 110px -> STAYS in LEFT_HALF (hysteresis prevents flicker!)
    assert snapper.detect_snap_zone(90, 500, current_zone=SnapZone.LEFT_HALF) == SnapZone.LEFT_HALF

    # Pulling further inward to 150px -> properly un-snaps to NONE
    assert snapper.detect_snap_zone(150, 500, current_zone=SnapZone.LEFT_HALF) == SnapZone.NONE
