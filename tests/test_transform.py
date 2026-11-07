"""Unit tests for ScreenTransform homography and projection."""
import json
from pathlib import Path
import pytest
from src.calibration.transform import ScreenTransform


def test_screen_transform_homography(tmp_path: Path):
    screen_w, screen_h = 1920, 1080
    transform = ScreenTransform(screen_w, screen_h)
    assert not transform.is_calibrated

    # Synthetic quadrilateral in normalized air coordinates [0.1, 0.9]
    air_points = [
        (0.1, 0.1),  # Top-Left
        (0.9, 0.1),  # Top-Right
        (0.9, 0.9),  # Bottom-Right
        (0.1, 0.9),  # Bottom-Left
    ]

    success = transform.set_calibration_points(air_points)
    assert success is True
    assert transform.is_calibrated is True

    # Test projection of exact corners
    tl_x, tl_y = transform.project(0.1, 0.1)
    assert abs(tl_x - 0) <= 1
    assert abs(tl_y - 0) <= 1

    br_x, br_y = transform.project(0.9, 0.9)
    assert abs(br_x - (screen_w - 1)) <= 1
    assert abs(br_y - (screen_h - 1)) <= 1

    # Test center point interpolation (0.5, 0.5)
    cx, cy = transform.project(0.5, 0.5)
    assert abs(cx - (screen_w // 2)) <= 2
    assert abs(cy - (screen_h // 2)) <= 2

    # Test save and load
    save_file = tmp_path / "test_calib.json"
    transform.save(save_file)
    assert save_file.exists()

    loaded_transform = ScreenTransform(screen_w, screen_h)
    assert loaded_transform.load(save_file) is True
    assert loaded_transform.is_calibrated is True

    cx_loaded, cy_loaded = loaded_transform.project(0.5, 0.5)
    assert cx == cx_loaded
    assert cy == cy_loaded


def test_invalid_point_count():
    transform = ScreenTransform(1920, 1080)
    with pytest.raises(ValueError):
        transform.set_calibration_points([(0.1, 0.1), (0.9, 0.1)])
