"""Unit tests for ScreenMapper zero-calibration coordinate mapping."""
from src.motion.mapper import ScreenMapper


def test_mapper_corners_and_clamping():
    screen_w, screen_h = 1920, 1080
    box_x = (0.20, 0.80)
    box_y = (0.20, 0.80)
    mapper = ScreenMapper(
        screen_width=screen_w,
        screen_height=screen_h,
        box_x_min=box_x[0],
        box_x_max=box_x[1],
        box_y_min=box_y[0],
        box_y_max=box_y[1],
        enable_acceleration=False,
    )

    # Top-Left corner of interaction box -> (0, 0)
    sx, sy = mapper.map_normalized_to_screen(0.20, 0.20)
    assert sx == 0
    assert sy == 0

    # Bottom-Right corner of interaction box -> (screen_w - 1, screen_h - 1)
    sx, sy = mapper.map_normalized_to_screen(0.80, 0.80)
    assert sx == screen_w - 1
    assert sy == screen_h - 1

    # Center of interaction box -> center of screen
    sx, sy = mapper.map_normalized_to_screen(0.50, 0.50)
    assert abs(sx - (screen_w // 2)) <= 1
    assert abs(sy - (screen_h // 2)) <= 1

    # Outside interaction box -> Clamped cleanly to bounds
    sx, sy = mapper.map_normalized_to_screen(0.05, 0.05)
    assert sx == 0
    assert sy == 0

    sx, sy = mapper.map_normalized_to_screen(0.95, 0.95)
    assert sx == screen_w - 1
    assert sy == screen_h - 1


def test_mapper_acceleration():
    screen_w, screen_h = 1920, 1080
    mapper = ScreenMapper(
        screen_width=screen_w,
        screen_height=screen_h,
        box_x_min=0.20,
        box_x_max=0.80,
        box_y_min=0.20,
        box_y_max=0.80,
        enable_acceleration=True,
    )

    t0 = 1.0
    mapper.map_normalized_to_screen(0.30, 0.30, timestamp=t0)
    
    # Very fast flick to 0.70 in 0.016s (60 FPS step)
    t1 = t0 + 0.016
    sx, sy = mapper.map_normalized_to_screen(0.70, 0.70, timestamp=t1)
    assert sx > 0
    assert sy > 0
