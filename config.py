"""Global configuration parameters for Zero-Calibration Gesture Controller."""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "hand_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"

# Camera Settings
CAMERA_INDEX = 0
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30

# MediaPipe Settings
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.7
MAX_NUM_HANDS = 1

# Ergonomic Virtual Air-Pad (Normalized Camera Space [0.0 - 1.0])
# Maps comfortable centered hand movement to full screen dimensions
INTERACTION_BOX_X_MIN = 0.18
INTERACTION_BOX_X_MAX = 0.82
INTERACTION_BOX_Y_MIN = 0.20
INTERACTION_BOX_Y_MAX = 0.80

# 3-Finger Pinch (Thumb + Index + Middle) for Window Dragging
DRAG_3FINGER_START_RATIO = 0.35   # Engages grab below this threshold
DRAG_3FINGER_RELEASE_RATIO = 0.45 # Releases grab above this threshold

# High-Precision 1€ Filter parameters (Casiez et al.)
# Lower min_cutoff = rock-solid stationary cursor (zero micro-tremor)
# Higher beta = instantaneous zero-lag tracking during fast movement
FILTER_MIN_CUTOFF = 0.75
FILTER_BETA = 0.16
FILTER_DERIVATIVE_CUTOFF = 1.0

# Pointer Acceleration
ENABLE_ACCELERATION = True
ACCELERATION_FACTOR = 1.25  # Smooth gain for faster flicks
