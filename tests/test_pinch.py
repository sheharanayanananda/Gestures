"""Unit tests for PinchDetector and ThreeFingerDragDetector hysteresis and scale invariance."""
from src.gestures.pinch import PinchDetector, PinchEvent, ThreeFingerDragDetector


def test_pinch_scale_invariance():
    detector = PinchDetector(start_ratio=0.28, release_ratio=0.38)

    # Hand close to camera: palm size = 100 px, finger dist = 20 px (ratio = 0.20 -> pinch)
    wrist_close = (200.0, 300.0)
    mcp_close = (200.0, 200.0)  # palm size = 100
    thumb_close = (200.0, 150.0)
    index_close = (200.0, 170.0)  # finger dist = 20 -> ratio 0.20

    event, ratio = detector.update(thumb_close, index_close, wrist_close, mcp_close)
    assert event == PinchEvent.PINCH_DOWN
    assert abs(ratio - 0.20) < 1e-4

    # Hand far from camera: palm size = 40 px, finger dist = 8 px (ratio = 0.20 -> still pinch!)
    wrist_far = (100.0, 150.0)
    mcp_far = (100.0, 110.0)  # palm size = 40
    thumb_far = (100.0, 90.0)
    index_far = (100.0, 98.0)  # finger dist = 8 -> ratio 0.20

    # Since already pinching, should remain PINCH_HOLD
    event, ratio = detector.update(thumb_far, index_far, wrist_far, mcp_far)
    assert event == PinchEvent.PINCH_HOLD
    assert abs(ratio - 0.20) < 1e-4


def test_pinch_hysteresis():
    detector = PinchDetector(start_ratio=0.28, release_ratio=0.38)
    wrist = (0.0, 0.0)
    mcp = (0.0, 100.0)  # palm size = 100

    # 1. Open hand: dist = 50 -> ratio = 0.50
    event, _ = detector.update((0.0, 150.0), (0.0, 200.0), wrist, mcp)
    assert event == PinchEvent.NONE
    assert detector.is_pinching is False

    # 2. Moving closer: dist = 30 -> ratio = 0.30 (still > 0.28, no pinch yet)
    event, _ = detector.update((0.0, 150.0), (0.0, 180.0), wrist, mcp)
    assert event == PinchEvent.NONE

    # 3. Touch: dist = 20 -> ratio = 0.20 (<= 0.28, PINCH_DOWN)
    event, _ = detector.update((0.0, 150.0), (0.0, 170.0), wrist, mcp)
    assert event == PinchEvent.PINCH_DOWN
    assert detector.is_pinching is True

    # 4. Slight open: dist = 35 -> ratio = 0.35 (between 0.28 and 0.38: hysteresis keeps HOLD)
    event, _ = detector.update((0.0, 150.0), (0.0, 185.0), wrist, mcp)
    assert event == PinchEvent.PINCH_HOLD
    assert detector.is_pinching is True

    # 5. Full open: dist = 45 -> ratio = 0.45 (> 0.38, PINCH_UP)
    event, _ = detector.update((0.0, 150.0), (0.0, 195.0), wrist, mcp)
    assert event == PinchEvent.PINCH_UP
    assert detector.is_pinching is False


def test_three_finger_drag_detector():
    detector = ThreeFingerDragDetector(start_ratio=0.35, release_ratio=0.45)
    wrist = (0.0, 0.0)
    mcp = (0.0, 100.0)  # palm size = 100

    # Case A: Only 2 fingers pinched (thumb and index at dist 15), but middle is far away (dist 60)
    thumb = (0.0, 150.0)
    index = (0.0, 165.0)  # thumb-index = 15
    middle_far = (0.0, 210.0)  # thumb-middle = 60 -> max spread = 60 / 100 = 0.60
    event, ratio = detector.update(thumb, index, middle_far, wrist, mcp)
    assert event == PinchEvent.NONE
    assert detector.is_dragging is False
    assert abs(ratio - 0.60) < 1e-4

    # Case B: All 3 fingers brought together (max spread = 20 -> ratio 0.20 <= 0.35)
    middle_close = (0.0, 170.0)  # thumb-middle = 20, index-middle = 5 -> max spread = 20
    event, ratio = detector.update(thumb, index, middle_close, wrist, mcp)
    assert event == PinchEvent.PINCH_DOWN
    assert detector.is_dragging is True
    assert abs(ratio - 0.20) < 1e-4

    # Case C: Slight spread during drag (max spread = 38 -> ratio 0.38, between 0.35 and 0.45)
    middle_slight = (0.0, 188.0)
    event, ratio = detector.update(thumb, index, middle_slight, wrist, mcp)
    assert event == PinchEvent.PINCH_HOLD
    assert detector.is_dragging is True

    # Case D: Open all fingers (max spread = 50 -> ratio 0.50 > 0.45)
    middle_open = (0.0, 200.0)
    event, ratio = detector.update(thumb, index, middle_open, wrist, mcp)
    assert event == PinchEvent.PINCH_UP
    assert detector.is_dragging is False
