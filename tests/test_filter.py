"""Unit tests for OneEuroFilter and PointFilter2D."""
import time
from src.gestures.filter import OneEuroFilter, PointFilter2D


def test_one_euro_filter_initialization():
    f = OneEuroFilter()
    assert f.filter(100.0, timestamp=1.0) == 100.0


def test_one_euro_filter_attenuates_jitter():
    f = OneEuroFilter(min_cutoff=1.0, beta=0.01)
    t = 1.0
    val = f.filter(100.0, timestamp=t)
    
    # Introduce small noisy jitter around 100
    noisy_samples = [100.5, 99.4, 100.6, 99.5, 100.4]
    filtered_outputs = []
    for sample in noisy_samples:
        t += 0.033  # ~30 FPS
        filtered_outputs.append(f.filter(sample, timestamp=t))

    # All filtered values should be closely clamped around 100
    for out in filtered_outputs:
        assert abs(out - 100.0) < 0.4


def test_point_filter_2d():
    pfilter = PointFilter2D()
    fx, fy = pfilter.filter(500.0, 300.0, timestamp=1.0)
    assert fx == 500.0
    assert fy == 300.0

    fx2, fy2 = pfilter.filter(505.0, 305.0, timestamp=1.033)
    # Should move smoothly towards target
    assert 500.0 < fx2 < 505.0
    assert 300.0 < fy2 < 305.0
