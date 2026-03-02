"""
distance.py
-----------
Monocular distance estimation using the pinhole camera model.

Formula:
    Distance (m) = (Real_Width × Focal_Length) / Apparent_Pixel_Width

The focal length is given in pixels and is calibrated for a typical
dashcam / webcam.  Adjust FOCAL_LENGTH and REAL_WIDTHS for your camera.
"""

import numpy as np
from typing import Dict


# ---------------------------------------------------------------------------
# Camera / scene constants
# ---------------------------------------------------------------------------

# Approximate focal length in pixels for a 1280×720 frame.
# Calibrate with: f = (pixel_width * known_distance) / known_real_width
FOCAL_LENGTH = 850.0   # pixels

# Known real-world widths (metres) for each COCO vehicle class
REAL_WIDTHS: Dict[int, float] = {
    2: 1.8,   # car
    3: 0.8,   # motorcycle
    5: 2.5,   # bus
    7: 2.4,   # truck
}

DEFAULT_REAL_WIDTH = 1.8  # fallback width (metres)

# Perspective correction: objects lower in the frame are closer
PERSPECTIVE_ALPHA = 0.5   # scaling factor for vertical offset correction


# ---------------------------------------------------------------------------
# DistanceEstimator class
# ---------------------------------------------------------------------------

class DistanceEstimator:
    """
    Estimates the distance to each tracked vehicle from a single camera.

    Parameters
    ----------
    focal_length : Camera focal length in pixels.
    frame_height : Height of the video frame in pixels.
    """

    def __init__(self,
                 focal_length: float = FOCAL_LENGTH,
                 frame_height: int   = 720):
        self._focal_length  = focal_length
        self._frame_height  = frame_height
        self._half_h        = frame_height / 2.0

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def estimate(self, track) -> float:
        """
        Estimate the distance (in metres) to a *track* object.

        The track must have attributes:
            .bbox      : [x1, y1, x2, y2]
            .class_id  : COCO class index
            .width     : pixel width of the bounding box
            .cy        : centre-Y of the bounding box

        Returns
        -------
        float
            Estimated distance in metres (clamped to [1.0, 200.0]).
        """
        pixel_width = max(track.width, 1)
        real_width  = REAL_WIDTHS.get(track.class_id, DEFAULT_REAL_WIDTH)

        # Basic pinhole formula
        dist = (real_width * self._focal_length) / pixel_width

        # Perspective correction: objects lower (cy > half_h) are closer
        vertical_offset = (track.cy - self._half_h) / self._half_h
        correction      = 1.0 - PERSPECTIVE_ALPHA * vertical_offset
        dist *= max(correction, 0.1)

        return float(np.clip(dist, 1.0, 200.0))

    def estimate_all(self, tracks) -> Dict[int, float]:
        """
        Estimate distances for a list of tracks.

        Returns
        -------
        dict : {track_id: distance_in_metres}
        """
        return {t.track_id: self.estimate(t) for t in tracks}
