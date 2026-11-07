"""MediaPipe Hand Tracker using Tasks Vision API."""
import logging
from pathlib import Path
from typing import List, Optional, Tuple
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

import config

logger = logging.getLogger(__name__)


class HandData:
    """Encapsulates extracted landmark positions and key finger points."""

    def __init__(
        self,
        landmarks: List[Tuple[float, float, float]],
        image_width: int,
        image_height: int,
    ):
        self.raw_landmarks = landmarks  # Normalized [0, 1] (x, y, z)
        self.image_width = image_width
        self.image_height = image_height

        # Key landmark indices
        # 0: Wrist, 4: Thumb tip, 8: Index tip, 9: Middle MCP, 12: Middle tip
        self.wrist = landmarks[0][:2]
        self.thumb_tip = landmarks[4][:2]
        self.index_tip = landmarks[8][:2]
        self.middle_mcp = landmarks[9][:2]
        self.middle_tip = landmarks[12][:2]

    @property
    def index_pixel_pos(self) -> Tuple[int, int]:
        """Index fingertip in pixel coordinates."""
        return (
            int(self.index_tip[0] * self.image_width),
            int(self.index_tip[1] * self.image_height),
        )

    @property
    def thumb_pixel_pos(self) -> Tuple[int, int]:
        """Thumb tip in pixel coordinates."""
        return (
            int(self.thumb_tip[0] * self.image_width),
            int(self.thumb_tip[1] * self.image_height),
        )

    @property
    def middle_pixel_pos(self) -> Tuple[int, int]:
        """Middle fingertip in pixel coordinates."""
        return (
            int(self.middle_tip[0] * self.image_width),
            int(self.middle_tip[1] * self.image_height),
        )


class HandTracker:
    """Initializes and runs the MediaPipe Hand Landmarker model."""

    def __init__(
        self,
        model_path: Path = config.MODEL_PATH,
        model_url: str = config.MODEL_URL,
        num_hands: int = config.MAX_NUM_HANDS,
    ):
        self.model_path = model_path
        self._ensure_model(model_url)

        base_options = python.BaseOptions(model_asset_path=str(self.model_path))
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=num_hands,
            min_hand_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_hand_presence_confidence=config.MIN_TRACKING_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

    def _ensure_model(self, model_url: str) -> None:
        """Downloads the model task file if not already present."""
        if not self.model_path.exists():
            logger.info("Downloading hand landmarker model to %s...", self.model_path)
            urllib.request.urlretrieve(model_url, self.model_path)
            logger.info("Model downloaded successfully.")

    def process_frame(
        self, bgr_frame: np.ndarray, timestamp_ms: int
    ) -> Optional[HandData]:
        """Processes a single BGR OpenCV frame and returns HandData if detected."""
        h, w = bgr_frame.shape[:2]
        # MediaPipe expects RGB
        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        result = self.detector.detect_for_video(mp_image, timestamp_ms)

        if not result.hand_landmarks:
            return None

        # Primary hand
        primary_landmarks = result.hand_landmarks[0]
        points = [(lm.x, lm.y, lm.z) for lm in primary_landmarks]
        return HandData(points, image_width=w, image_height=h)

    def close(self):
        if hasattr(self, "detector") and self.detector:
            self.detector.close()
